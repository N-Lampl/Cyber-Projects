# p5 · Market-manipulation detection on OHLCV time series

<!-- realdata-banner -->
> **Real data.** Committed results run on **real AAPL daily OHLCV (2015–2017)**: `scripts/run_detect.py --ticker AAPL`. Real markets have no manipulation labels, so flags are surfaced, not scored — the labeled synthetic path (`make run`) keeps the PR/recall metrics.

Inject **known** manipulations into a seeded synthetic price/volume series, then catch them with
unsupervised anomaly detection — and score it the way a surveillance desk would: PR-AUC,
event-level recall at a fixed alert budget, and **median lead-time-to-flag**.

**Authorized use only.** Everything here is synthetic data I generated and models I fit myself —
no real venue, broker or account is touched. See [../../ETHICS.md](../../ETHICS.md).

## The idea

Real labelled market-manipulation events are rare and confidential, so I do the opposite of guessing:
I generate a deterministic OHLCV series ([src/market_manip/data.py](src/market_manip/data.py)) and
**inject manipulations with exact bar spans** so detection can be measured against ground truth.

- **Geometric Brownian motion** drives the price; a log-normal process drives volume.
- **Pump-and-dump** — a coordinated multi-day ramp in price *and* volume (4–9× normal), then a sharp
  crash back through the pre-pump level.
- **Spoofing-like bursts** — a 1–2 bar volume spike (8–16×) with only a fleeting, reverted price tick
  (orders flashed then cancelled). Deliberately subtle: this is the hard case.

Then a small, fully **causal** feature set ([features.py](src/market_manip/features.py)): log returns,
rolling volatility, **volume ratio vs a *trailing* moving average** (shifted by one bar so a single
spike isn't diluted by itself), price z-score, return z-score, and intraday range. Two unsupervised
detectors ([detect.py](src/market_manip/detect.py)) score every bar (higher = more anomalous):

1. **Rolling z-score** — a transparent composite of the volume / price / return z-scores (the classic
   statistical baseline, no model).
2. **IsolationForest** — scikit-learn's tree-based outlier detector over the feature matrix (primary).

Imbalance is handled honestly: the positive class is ~4% of bars, so I report **PR-AUC** as the headline
(not accuracy) and pick the operating threshold from a fixed **per-bar alert budget** rather than 0.5.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make detect                        # generate + detect + write figures & metrics.json
make test                          # fast smoke tests (-m "not slow")
make detect ARGS=                  # (defaults: --seed 42 --n 1500 --window 20 --budget 0.05)
python scripts/run_detect.py --budget 0.07   # widen the alert budget -> higher recall
```

Outputs land in [results/](results/):
- `figures/price_volume_flagged.png` — price + volume with injected windows shaded and **flagged bars
  in red** (the at-a-glance plot).
- `figures/anomaly_score_timeline.png` — the IsolationForest score over time vs the operating threshold.
- `figures/pr_curve.png` — the **money plot**: precision-recall for both detectors vs prevalence.
- `metrics.json` — PR/ROC-AUC, precision@k, confusion at the operating point, event recall by kind, and
  lead-time (committed as evidence).

## What the result shows

On 1500 bars (60 manipulated, 4.0% prevalence), the IsolationForest hits **PR-AUC 0.86 / ROC-AUC 0.99**
(chance PR-AUC ≈ 0.04). At a **5% per-bar alert budget** it catches **11/14 injected events
(79% event recall)** — **every pump-and-dump (6/6)** and 5/8 spoofs — at **69% bar precision / 1.6% false-
positive rate**, with a **median lead-time of +4 bars before the worst (peak) bar** of an event, i.e. it
tends to fire on the *ramp*, not the crash. The miss pattern is the honest, expected one: multi-bar
pumps light up several features at once and are easy; single-bar spoofs spike only volume and are the
ones a generic detector lets slip — which is exactly why surveillance teams use order-flow features, not
just OHLCV.

## Interview story (3 sentences)

> Because real manipulation labels are scarce, I injected known pump-and-dump and spoofing events into a
> seeded synthetic OHLCV series, engineered causal price/volume features, and detected them with a
> rolling z-score baseline and an IsolationForest — scoring it like a surveillance desk with PR-AUC,
> event recall at a fixed alert budget, and lead-time-to-flag instead of accuracy. The forest reaches
> 0.86 PR-AUC and catches every multi-bar pump with a +4-bar median lead-time, while single-bar spoofs
> stay hard — a clean, honest illustration of why OHLCV-only surveillance needs order-flow features. The
> whole thing is deterministic and runs offline on a CPU in seconds.

## Layout

```
src/market_manip/  utils.py (seeds) · data.py (synthetic OHLCV + events) ·
                   features.py · detect.py (z-score + IsolationForest) · evaluate.py (metrics)
scripts/           run_detect.py  (generate -> detect -> figures + metrics.json)
tests/             test_smoke.py  (fast invariants + one @slow end-to-end)
results/           figures/*.png + metrics.json  (committed)
data/ models/      git-ignored (no data needed; detectors fit at runtime)
```

## References

- Liu, Ting, Zhou. *Isolation Forest.* ICDM 2008.
- Cao et al. *Detecting price manipulation in the financial market.* (pump-and-dump / spoofing surveys.)
- scikit-learn `IsolationForest`, `average_precision_score`, `precision_recall_curve`.
