# p1 · Credit-card fraud detection on a highly imbalanced table

<!-- realdata-banner -->
> **Real data.** Committed results are from the **real ULB credit-card fraud** dataset (284,807 transactions): `scripts/run_detection.py --real data/creditcard.csv`. The offline synthetic generator (`make detect`) is the no-network fallback for tests/CI.

Supervised fraud detection where fraud is **~1% of transactions**. The point of
this project is *how you measure*: on a 1% base rate, "99% accuracy" is what you
get by predicting **never fraud**, so accuracy is banned here. We report
**PR-AUC** (primary), ROC-AUC, precision@k, and recall at a fixed false-positive
budget, and we tune the decision threshold to an operating point a fraud team
would actually run.

**Authorized use only.** Synthetic data and models I trained myself; the
optional real path is a public dataset used under its stated license. See
[../../ETHICS.md](../../ETHICS.md).

## The idea

Fraud detection is a **needle-in-a-haystack ranking problem**, not a balanced
classification one. Two consequences drive every choice here:

1. **Metrics.** PR-AUC summarizes precision/recall across all thresholds and,
   unlike ROC-AUC, does not flatter a model on extreme imbalance. We also report
   precision@k (the quality of the top-k analyst review queue) and recall at a
   1% false-positive budget (how much fraud you catch if you can only afford to
   bother 1% of legitimate customers).
2. **Imbalance, handled honestly.** `class_weight="balanced"` reweights the rare
   class instead of resampling; the threshold is then tuned explicitly to a
   stated FPR budget rather than left at the meaningless default of 0.5.

The default data is a **seeded synthetic transaction generator** with an injected
fraud signal (extreme amounts, small-hours timing, high-risk merchant
categories, young accounts, velocity bursts) — so the project produces real
metrics with **zero downloads**.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make detect            # generate txns + train logreg/RF (+ xgboost if installed) + write figures & metrics.json
make test              # fast smoke tests (-m 'not slow')
make detect ARGS=...   # e.g. python3 scripts/run_detection.py --target-fpr 0.005 --n 50000
make clean             # remove generated figures + metrics.json
```

Outputs land in [results/](results/):
- `figures/precision_recall_curve.png` — the **money plot**: PR curve vs. the chance line (base rate).
- `figures/confusion_matrix.png` — counts at the tuned operating threshold.
- `figures/precision_at_k.png` — precision among the top 50/100/200 flagged txns.
- `metrics.json` — PR-AUC, ROC-AUC, precision@k, recall@FPR, confusion (committed as evidence).

## What the result shows

On 30,000 synthetic transactions (realized fraud rate **0.99%**), the best model
by PR-AUC is **logistic regression**: **PR-AUC ≈ 0.44**, ROC-AUC ≈ 0.96. At a
**1% false-positive budget** it catches **~56% of fraud at ~40% alert
precision** (confusion: tp=50, fp=74, fn=39, tn=8837), and **precision@50 = 0.58**.

The instructive part is the **gap between ROC-AUC (0.96) and PR-AUC (0.44)**:
ROC-AUC looks excellent because true negatives dominate, while PR-AUC tells the
honest story that finding the rare positives is hard. Note too that logistic
regression *edged out* RandomForest and XGBoost here — on a cleanly-separable
linear signal, the simple calibrated model wins, which is exactly the kind of
result a metrics-first evaluation surfaces instead of hiding.

## Interview story (3 sentences)

> I built a credit-card fraud detector on a 1% base rate and deliberately refused
> to report accuracy, ranking models by PR-AUC instead and tuning the threshold
> to a fixed 1% false-positive budget — the constraint a real fraud team works
> under. The headline is the gap between a flattering 0.96 ROC-AUC and an honest
> 0.44 PR-AUC, plus a concrete operating point that catches ~56% of fraud at ~40%
> alert precision. It shows I evaluate imbalanced security problems the way they
> behave in production — by alert budget and review-queue quality, not a single
> accuracy number.

## Layout

```
src/fraud_detection/  utils.py (seeds) · data.py (synthetic generator) · models.py · metrics.py
scripts/              run_detection.py  (generate -> train -> tune -> figures + metrics.json)
tests/                test_smoke.py  (fast invariants + one @slow end-to-end)
results/              figures/*.png + metrics.json  (committed)
data/ models/         git-ignored (synthetic at runtime; optional Kaggle csv)
```

## References

- Saito & Rehmsmeier. *The Precision-Recall Plot Is More Informative than the ROC
  Plot When Evaluating Binary Classifiers on Imbalanced Datasets.* PLoS ONE, 2015.
- Dal Pozzolo et al. *Calibrating Probability with Undersampling for Unbalanced
  Classification.* IEEE SSCI, 2015. (The ULB / Worldline fraud dataset.)
- Kaggle ULB **Credit Card Fraud Detection** dataset (optional real path) —
  see [data/README.md](data/README.md).
