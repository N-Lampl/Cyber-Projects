# shared · ids_pipeline (reusable tabular-IDS library)

A small, **reusable** intrusion-detection library that both `p1-nids-baseline` and the
`CAPSTONE-adversarial-ids` import. It gives them one clean, **leak-free** path from raw
network-flow rows to SOC-grade metrics -- so the capstone can focus on attacking/defending a
detector instead of re-plumbing data prep.

**Authorized use only.** Targets are a model I train myself on synthetic data (or the
public NSL-KDD research dataset). No live traffic, no third-party systems. See
[../../ETHICS.md](../../ETHICS.md).

## The problem

A flow-based NIDS classifies each connection as **benign** or **attack** from tabular features
(durations, byte counts, connection rates, flag ratios, protocol/service). Two failure modes
sink most student projects:

1. **Data leakage** -- fitting the scaler/encoder on the *whole* dataset leaks test statistics
   into preprocessing and inflates every score. Here the `StandardScaler` and `OneHotEncoder`
   live *inside* an `sklearn.Pipeline` and are fit on **TRAIN only**.
2. **Accuracy theatre** -- with class imbalance, accuracy is meaningless. We report the metrics
   a SOC actually uses: precision / recall / F1, **precision@k** (the top-k alerts an analyst
   reviews), the confusion matrix, and **ROC-AUC**.

## The idea / design

```
raw flows ─► ColumnTransformer (fit on TRAIN only) ─► RandomForest ─► SOC metrics
              ├─ StandardScaler   (numeric features)
              └─ OneHotEncoder    (protocol_type, service, flag)
```

Clean four-call API (`src/ids_pipeline/`):

```python
from ids_pipeline import load_data, build_pipeline, train, evaluate

ds   = load_data(synthetic=True)   # offline synthetic flows (or synthetic=False for NSL-KDD)
pipe = build_pipeline(ds)          # leak-free preprocess + RandomForest (default)
train(pipe, ds)                    # fits on TRAIN only
metrics = evaluate(pipe, ds)       # precision/recall/F1, precision@k, ROC-AUC, confusion matrix
```

- **Default classifier:** scikit-learn `RandomForestClassifier` (`class_weight="balanced"`).
- **Optional upgrade:** `build_pipeline(ds, classifier="xgb")` uses XGBoost, imported lazily so
  the module still imports without it.
- **Default data:** a deterministic synthetic network-flow generator -- benign and attack flows
  drawn from different overlapping distributions, with controllable class imbalance.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make run            # synthetic flows -> train -> evaluate -> figures + metrics.json
make test           # fast smoke tests (leak-check, determinism, metric ranges)

python3 scripts/run_demo.py --classifier xgb     # optional: XGBoost (needs xgboost installed)
python3 scripts/run_demo.py --real               # optional: real NSL-KDD (see data/README.md)
```

Outputs land in [results/](results/):
- `figures/confusion_matrix.png` -- benign vs attack, true/false positives/negatives.
- `figures/roc_curve.png` -- threshold-free ranking quality with the AUC.
- `metrics.json` -- precision/recall/F1, precision@k, ROC-AUC, confusion matrix (committed).

## What the result shows

On the (deliberately overlapping) synthetic test set the RandomForest reaches **ROC-AUC ≈ 0.97**
with precision ≈ 0.90 / recall ≈ 0.80 / **F1 ≈ 0.84**, and **precision@k ≈ 1.0** for the top
alerts -- a clean, honest, non-trivial baseline produced with **zero leakage**. That trustworthy
baseline is the whole point: the capstone then shows how an attacker can perturb flow features to
evade exactly this detector, and how to harden it.

## Interview story (3 sentences)

> I built a reusable tabular-IDS library whose entire preprocessing stack is fit on training
> data only -- inside a single sklearn Pipeline -- so the benchmark can't leak, and it reports
> SOC metrics (precision@k, ROC-AUC, confusion matrix) instead of misleading accuracy. It runs
> fully offline on a synthetic network-flow generator, with real NSL-KDD as a one-flag upgrade,
> so a reviewer can reproduce it in seconds. Two downstream projects -- a NIDS baseline and an
> adversarial-IDS capstone -- import the same `load_data / build_pipeline / train / evaluate`
> API, which is what makes the attack/defense comparison apples-to-apples.

## Layout

```
src/ids_pipeline/  utils.py (seeds) · data.py (synthetic gen + NSL-KDD) ·
                   pipeline.py (leak-free preprocess + RF/xgb) · metrics.py (SOC metrics)
scripts/           run_demo.py   (load -> train -> evaluate -> figures + metrics.json)
tests/             test_smoke.py (leak-check + invariants + one @slow end-to-end)
results/           figures/*.png + metrics.json  (committed)
data/ models/      git-ignored (synthetic by default; NSL-KDD downloaded on demand)
```

## References

- Tavallaee, Bagheri, Lu, Ghorbani. *A Detailed Analysis of the KDD CUP 99 Data Set.* IEEE
  CISDA 2009 (the NSL-KDD dataset).
- Pedregosa et al. *Scikit-learn: Machine Learning in Python.* JMLR 2011 -- `Pipeline`,
  `ColumnTransformer`, leakage-safe preprocessing.
