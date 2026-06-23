# p2 · Unsupervised transaction anomaly detection

<!-- realdata-banner -->
> **Real data.** Committed results run IsolationForest on the **real ULB credit-card** data, scored against the real fraud labels (used for evaluation only): `scripts/run_detect.py --real <creditcard.csv>`. Synthetic stream remains the offline fallback.

Label-free anomaly detection over a transaction stream. An **IsolationForest** (and an
optional small **autoencoder**) scores every transaction by how unusual it is — no fraud
labels at fit time. We inject three realistic anomaly patterns into a seeded synthetic
stream and grade the detectors against those injected labels (used **only** for evaluation).

**Authorized use only.** Everything here is synthetic data and my own models — no real
accounts, no scraping, no third-party systems. See [../../ETHICS.md](../../ETHICS.md).

## The idea

Fraud teams rarely have clean labels for *new* attack shapes, so the practical first line
is **unsupervised**: learn what "normal" looks like and surface the outliers. The catch is
that anomalies are rare, so **accuracy is meaningless** — a model that flags nothing is
98.5% "accurate" here. We report the metrics an analyst queue actually lives by:
**PR-AUC** (primary), ROC-AUC, **precision@k / recall@k**, and **recall at a fixed 1%
false-positive budget** with the confusion matrix at that operating point.

Three injected anomaly types (deterministic, seeded — see
[src/txn_anomaly/data.py](src/txn_anomaly/data.py)):
- **amount_spike** — amount 15-40x the account's normal scale
- **off_hours** — activity at 1-4am for daytime accounts
- **velocity** — a burst of many transactions from one account within minutes

The detector never sees `is_anomaly`; it only sees six engineered features
(`amount_log`, `hour`, `is_off_hours`, `txn_count_1h`, `secs_since_prev`,
`amount_vs_acct_mean`).

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make detect            # synthesize stream, fit IsolationForest, write figures + metrics.json
make detect ARGS=--ae  # also run the optional torch autoencoder (sklearn fallback if no torch)
make test              # fast smoke tests
```

Outputs land in [results/](results/):
- `figures/score_distribution.png` — anomaly score, **normal vs injected** (the separation).
- `figures/precision_at_k.png` — precision@k / recall@k as the alert queue deepens.
- `figures/anomaly_timeline.png` — every txn's score over time, colored by injected type, with the operating threshold.
- `metrics.json` — PR-AUC, ROC-AUC, P@k, recall@1%FPR, confusion, per-type recall (committed as evidence).

## What the result shows

On a 12,070-transaction stream with **179 injected anomalies (1.48% base rate)**, the
label-free IsolationForest reaches **PR-AUC ≈ 0.59** and **ROC-AUC ≈ 0.97**; at a strict
**1% false-positive budget it recalls ≈ 64%** of anomalies. The optional autoencoder does
better on PR-AUC (**≈ 0.74**). Breaking recall down by type is the honest part: the
detectors nail **off-hours (≈ 96%)** and **amount spikes (≈ 75%)** but miss most
**velocity bursts (≈ 18%)** — the per-transaction features don't capture cross-transaction
timing well, which is exactly the kind of gap a real fraud team would iterate on next.

## Interview story (3 sentences)

> I built an unsupervised transaction-anomaly detector (IsolationForest, plus an optional
> autoencoder) that scores every transaction without ever seeing fraud labels, then graded
> it with the metrics that matter under extreme class imbalance — PR-AUC, precision@k, and
> recall at a fixed false-positive budget — instead of accuracy. On a seeded synthetic
> stream with injected amount-spike, off-hours, and velocity anomalies it hits ROC-AUC ≈
> 0.97 and recalls ~64% of anomalies at a 1% FP budget. The per-type breakdown showed it
> catches amount/time anomalies but misses velocity bursts, which is the kind of concrete,
> feature-driven finding that drives the next iteration of a detection system.

## Layout

```
src/txn_anomaly/  utils.py (seeds) · data.py (synthetic stream + features) · detectors.py (IForest + optional AE) · evaluate.py (PR-AUC/P@k/recall@budget)
scripts/          run_detect.py  (synthesize → score → figures + metrics.json)
tests/            test_smoke.py  (fast invariants + one @slow end-to-end)
results/          figures/*.png + metrics.json  (committed)
data/ models/     git-ignored (synthetic data generated at runtime; models fit at runtime)
```

## References

- Liu, Ting, Zhou. *Isolation Forest.* ICDM 2008.
- scikit-learn *Novelty and Outlier Detection* user guide; `IsolationForest`.
- Optional real benchmark: ULB Machine Learning Group, *Credit Card Fraud Detection* (Kaggle) — see [data/README.md](data/README.md).
