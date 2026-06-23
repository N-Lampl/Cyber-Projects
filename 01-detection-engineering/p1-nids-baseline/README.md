# p1 · NIDS baseline (SOC metrics on a shared IDS pipeline)

A clean, leak-free **network intrusion detection** baseline: a RandomForest over
flow features, scored the way a **SOC** actually reads a detector — by *alert
budget*, detection rate, and the daily false-alert load, not a single accuracy
number. The model + preprocessing live in the reusable
[`../shared/ids_pipeline`](../shared/ids_pipeline) library (imported **by path**),
which this project shares with the adversarial-IDS capstone; here we add the SOC
reporting layer and the figures.

**Authorized use only.** The target is a model I trained myself on synthetic
flows (or the public NSL-KDD research dataset). See [../../ETHICS.md](../../ETHICS.md).

## The problem

Test accuracy is a terrible NIDS metric: with ~25% attacks, a "flag nothing"
model is already 75% accurate. A SOC cares about a different question — *given an
analyst team that can triage only the top few percent of traffic, how many real
attacks do we catch, and how many false alerts do we drown them in?* That is an
**operating-point** question, and it's set by where you put the score threshold.

## The idea

1. **Leak-free pipeline** (in the shared library): scale numerics + one-hot
   encode categoricals, fit on **TRAIN only**, wrapped in one `sklearn.Pipeline`
   so no test statistics leak into preprocessing. Classifier: `RandomForest`
   (`class_weight="balanced"` for the imbalance).
2. **Threshold by alert budget** (this project). Instead of the arbitrary 0.5,
   pick the score cutoff at the quantile that flags a target fraction of flows:

   ```
   threshold = quantile(scores, 1 - alert_budget)
   ```

   A 1% budget means "we'll review the top 1% of traffic" — the rest is the SOC
   reality of finite analyst hours.
3. **Report what ships a detector:** detection rate (recall), alert precision
   (PPV), miss rate, and an extrapolated **false-alerts-per-day** load, swept
   across budgets — see [src/nids_baseline/soc.py](src/nids_baseline/soc.py).

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make detect                          # synthetic flows: train + SOC report + figures + metrics.json
make detect ARGS='--alert-budget 0.05'   # tighter budget (fewer, higher-precision alerts)
make detect ARGS='--classifier xgb'  # optional xgboost path (requires `pip install xgboost`)
make detect ARGS=--real              # benchmark on real NSL-KDD (see data/README.md)
make test                            # fast smoke tests
```

Outputs land in [results/](results/):
- `figures/roc_curve.png` — threshold-free ranking quality (ROC-AUC).
- `figures/confusion_matrix.png` — the operating point as a 2×2 table.
- `figures/alert_budget_tradeoff.png` — detection vs precision as the budget widens.
- `metrics.json` — the full SOC report + the budget sweep (committed as evidence).

## What the result shows

On the synthetic flows (seed 42, 3k held-out test, ROC-AUC ≈ **0.97**), the
operating point is everything:

| alert budget | detection rate | alert precision |
|---|---|---|
| 1%  | 4%  | 100% |
| 5%  | 20% | 99%  |
| 10% | 39% | 97%  |
| 25% | 85% | 85%  |

Same model, wildly different SOC story depending on how much triage capacity you
spend. A strong ranker (precision@50 = 1.0) lets a SOC run a *tight* budget with
near-zero false positives; chasing high recall means accepting more noise. That
trade-off — not raw accuracy — is the deliverable.

## Interview story (3 sentences)

> I built a network-intrusion-detection baseline on a shared, leak-free
> scikit-learn pipeline and evaluated it the way a SOC does: by alert budget,
> detection rate, alert precision, and projected daily false-alert load rather
> than accuracy. On held-out data the RandomForest hits ROC-AUC ≈ 0.97, and the
> budget sweep makes the real decision explicit — a 1% budget catches few attacks
> at 100% precision, a 25% budget catches 85% but halves precision. The pipeline
> is the same one my adversarial-IDS capstone attacks, so this baseline doubles
> as the victim model for the evasion work.

## Layout

```
src/nids_baseline/   utils.py (seeds + locate shared lib by path) · soc.py (alert-budget metrics) · __init__.py
scripts/             run_nids.py  (load->train->evaluate->figures+metrics.json)
tests/               test_smoke.py  (fast invariants + one @slow end-to-end)
results/             figures/*.png + metrics.json  (committed)
data/ models/        git-ignored (NSL-KDD downloaded / models produced at runtime)
../shared/ids_pipeline/   the reusable pipeline this project imports by path
```

## References

- Tavallaee, Bagheri, Lu, Ghorbani. *A Detailed Analysis of the KDD CUP 99 Data
  Set.* IEEE CISDA 2009 (the NSL-KDD dataset).
- Sommer & Paxson. *Outside the Closed World: On Using Machine Learning for
  Network Intrusion Detection.* IEEE S&P 2010 (why operating points / base rates
  matter for NIDS).
- scikit-learn `Pipeline`, `ColumnTransformer`, `RandomForestClassifier` docs.
