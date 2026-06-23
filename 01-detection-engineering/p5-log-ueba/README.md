# p5 · Auth-log anomaly detection / UEBA

Catch **lateral movement** in authentication logs without labels. A synthetic enterprise
auth feed (users authenticating across hosts over two weeks) has red-team activity
injected into a handful of accounts; an unsupervised **IsolationForest** over per-user
behavioural features ranks the events, and we score it the way a SOC actually cares:
**precision@k** and **time-to-detect** — not just ROC-AUC.

**Authorized use only.** Targets are a self-generated synthetic log and self-trained
models — no real systems, no real users. See [../../ETHICS.md](../../ETHICS.md).

## The problem

ROC-AUC on this data is **1.000** — and that number is almost useless to an analyst. An
analyst works a *ranked queue* and only ever looks at the top of it. The real questions:

- **precision@k** — of the top k alerts I open, how many are real lateral movement?
- **time-to-detect** — once an account is compromised, how long until one of its events
  surfaces in my queue?
- **recall@k** — what fraction of the attack did I ever see?

## The idea: behaviour *relative to each entity*

UEBA = **U**ser & **E**ntity **B**ehaviour **A**nalytics. You don't flag "a service logon
at 2am" in the abstract; you flag it because *this user* never does that. So we learn a
per-user baseline from the **past only** (streaming / causal — no peeking) and turn every
event into a small vector of "how surprising is this for this user":

```
novel_dst      first time this user touches this dst_host?
novel_src      first time from this src_host?
user_dst_card  how many distinct hosts has this user touched so far (fan-out)?
hour_zscore    |event hour - user's running mean hour| / std   (off-hours signal)
off_hours      outside 07:00–19:00?
is_failure     auth failed?
logon_rarity   service / remote / batch logon (rare for a human)?
recent_dst_rate distinct new hosts in a trailing 1-hour window (burst of pivots)
```

Lateral movement lights up several at once: a stolen credential **fans out** across many
never-seen hosts (`novel_dst`, `recent_dst_rate`, `user_dst_card`), **off-hours**
(`off_hours`, `hour_zscore`), with **service/remote logons** and lots of **failures**.

**IsolationForest** (Liu et al., 2008) isolates such rare feature combinations in very few
random splits → high anomaly score. It's unsupervised — it never sees `is_anomaly` at fit
time, mirroring a real deployment where you have no labelled lateral movement up front.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make detect                      # generate log + IsolationForest + figures + metrics.json
make detect ARGS=--autoencoder   # ALSO run the optional torch autoencoder (lazy import)
make test                        # fast smoke tests
```

Default path needs only **numpy, pandas, scikit-learn, matplotlib** — fully offline,
synthetic data. `torch` is optional and imported lazily (the module imports fine without
it).

Outputs land in [results/](results/):
- `figures/precision_at_k.png` — precision@k curve (the money plot for a SOC).
- `figures/score_distribution.png` — benign vs lateral-movement score separation.
- `figures/triage_queue.png` — the top-100 ranked queue, true hits in red.
- `metrics.json` — precision@k, recall@k, time-to-detect, AP and ROC-AUC (committed).

## What the result shows

On 15.4k events with 100 injected anomalies (**0.65%** base rate):

| metric | IsolationForest |
|---|---|
| precision@10 / @25 | **1.00 / 1.00** |
| recall@50 | 0.50 |
| average precision | 0.948 |
| ROC-AUC | 1.000 |
| first true hit | **rank 1** (0 false alerts first) |
| time-to-detect (avg / compromised account) | **~882 s** (~15 min) |

The top of the queue is *pure* lateral movement: an analyst's first 25 clicks are all real.
And `time-to-detect` shows that for each popped account, the very first event we flag lands
within minutes of the attack's start — the metric that actually bounds blast radius.

**Honest contrast (run `--autoencoder`):** the optional torch autoencoder gets
ROC-AUC ≈ 0.98 yet **precision@25 ≈ 0** — its reconstruction error under-weights the sparse
binary "novel host / off-hours" signals that define this attack. Same headline AUC, useless
queue. That's the whole argument for reporting precision@k and time-to-detect.

## Interview story (3 sentences)

> I built an offline UEBA pipeline that detects lateral movement in auth logs by scoring
> each event against the user's *own* streaming behavioural baseline, then ranks with an
> unsupervised IsolationForest. I deliberately reported precision@k and time-to-detect
> instead of ROC-AUC — and showed a competing autoencoder with 0.98 AUC but ~0 precision@25,
> proving why AUC misleads SOC teams. The feature builder is causal and streaming, so the
> exact same code drops onto a real LANL/LogHub auth feed as a SIEM filter.

## Layout

```
src/log_ueba/   utils.py (seeds) · generate.py (synthetic auth events) ·
                features.py (causal per-user UEBA features) ·
                detect.py (IsolationForest + optional torch AE) · metrics.py (precision@k, TTD)
scripts/        run_ueba.py  (generate → features → detect → figures + metrics.json)
tests/          test_smoke.py  (fast invariants + one @slow end-to-end)
results/        figures/*.png + metrics.json  (committed)
data/ models/   git-ignored (synthetic data is generated; nothing downloaded)
```

## Real-data path (documented; offline path is the default)

The feature/detector code is dataset-agnostic. See [data/README.md](data/README.md) for the
**LANL Comprehensive Cyber Security Events** path (real labelled red-team auth data,
streamed/filtered so you never materialize the multi-GB file) and the **LogHub** path
(template the lines with Drain, then derive the same features). Because `build_features`
only uses the past, it is a real-time SIEM filter, not just a batch job.

## References

- Liu, Ting, Zhou. *Isolation Forest.* ICDM 2008.
- Kent. *Comprehensive, Multi-Source Cyber-Security Events.* LANL, 2015.
  <https://csr.lanl.gov/data/cyber1/>
- He, Zhu, He, Lyu. *Loghub: A Large Collection of System Log Datasets.* (LogPAI)
  <https://github.com/logpai/loghub>
- scikit-learn `IsolationForest` docs.
