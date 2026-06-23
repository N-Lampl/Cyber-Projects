# p7 · Concept-drift monitoring as a security control

A deployed detector is only trustworthy while its **inputs look like its training
data**. This project treats *concept/data drift* as a first-class security
signal: it simulates a tabular detector's input stream, injects a distribution
shift partway through (the kind an attacker causes while probing/evading, or that
a silently-broken pipeline causes), and raises **thresholded alerts** using two
classic drift statistics — **PSI** and **KS**.

**Authorized use only.** Targets are synthetic data and self-trained models;
no real systems or third-party data are touched. See [../../ETHICS.md](../../ETHICS.md).

## The idea

For each monitoring window (say, one hour of traffic) and each feature, compare
the live distribution against the training-time **reference** distribution.

**PSI — Population Stability Index** (bin the reference into deciles, measure how
much probability mass moved):

```
PSI = Σ_i ( cur_i − ref_i ) · ln( cur_i / ref_i )
```

Convention: `< 0.10` stable · `0.10–0.25` moderate shift · `≥ 0.25` major shift.

**KS — Kolmogorov–Smirnov** (binning-free max gap between the two empirical CDFs):

```
KS = sup_x | F_ref(x) − F_cur(x) |        (two-sample, with a p-value)
```

A feature **alerts** only when PSI crosses its threshold **and** the KS evidence
agrees (statistic large *and* p-value significant) — requiring both cuts noise.
A window alerts if any feature alerts. One feature (`session_len`) is never
drifted, so the monitor must *avoid* false-alarming on it.

```
reference (train)        live windows (0..N) ── inject drift at window D ──►
   │                          │
   └──► per feature: PSI + KS ◄┘   ─► thresholds ─► alert? ─► drift-over-time plot
```

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make detect      # simulate the stream, run the PSI/KS monitor, write figures + metrics.json
make test        # fast smoke tests
make detect ARGS=  # (pass flags via the script, e.g. --psi-threshold 0.2 --drift-start 8)
python3 scripts/run_monitor.py --n-windows 36 --drift-start 18   # custom run
```

Default path needs only **numpy / scikit-learn / pandas / matplotlib** (scipy
optional, for the exact KS p-value) and runs fully offline.

Outputs land in [results/](results/):
- `figures/drift_over_time.png` — the **money plot**: PSI per feature over time vs. the alert line.
- `figures/psi_heatmap.png` — feature × window PSI heatmap.
- `metrics.json` — first-alert window, detection latency, false alarms, per-window PSI (committed).

## What the result shows

Before the injected drift, every feature sits well below threshold and **zero
alerts** fire. Once drift begins, PSI on the affected features climbs past the
alert line within a couple of windows — giving a small **detection latency** with
**no pre-drift false alarms**, while the deliberately-stable control feature
never alarms. That's exactly the behavior you want from a monitoring control:
quiet until something actually changes, then loud.

## Interview story (3 sentences)

> I built a model-monitoring control that watches a detector's input stream and
> alerts on distribution drift using PSI and KS with tuned thresholds, treating
> drift as a security signal rather than just an MLOps metric. On a synthetic
> stream with injected drift it fires within a couple of windows of onset, with no
> false alarms beforehand and no alarm on a deliberately-stable control feature.
> The same monitor drops straight in front of the tabular IDS elsewhere in this
> repo, so input drift (including evasion-driven shifts) is caught before it
> silently degrades detection.

## Layout

```
src/drift_monitoring/  utils.py (seeds) · metrics.py (PSI/KS) · stream.py (synthetic drift) · monitor.py (alerts)
scripts/               run_monitor.py
tests/                 test_smoke.py  (fast invariants + one @slow end-to-end)
results/               figures/*.png + metrics.json  (committed)
data/ models/          git-ignored; no external data needed (synthetic stream)
```

## References

- B. Siddiqi. *Credit Risk Scorecards* — the PSI bins-and-deciles convention and
  the 0.1 / 0.25 thresholds.
- Kolmogorov–Smirnov two-sample test — `scipy.stats.ks_2samp`.
- NannyML / Evidently AI docs — PSI & KS as standard tabular drift detectors for
  production model monitoring.
