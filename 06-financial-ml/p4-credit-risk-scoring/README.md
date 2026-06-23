# p4 · Credit default-risk scoring (calibration + fairness)

<!-- realdata-banner -->
> **Real data.** Committed results are from **real UCI German Credit** (1,000 borrowers), with applicant age<25 as a genuine protected attribute: `scripts/run_scoring.py --real-csv data/german.data`. Synthetic borrowers remain the offline fallback.

A small, honest credit scorecard: train and **calibrate** two probability-of-default
(PD) models on a seeded synthetic borrower table, then judge them the way a lender
actually would — by **discrimination** (ROC-AUC, KS, Gini) *and* **calibration**
(Brier score, reliability curve), with a **fairness check** across a protected group.

**Authorized use only.** Synthetic data and my own models — no real applicants,
no scraped PII. See [../../ETHICS.md](../../ETHICS.md).

## The idea

Credit models don't just rank applicants; they **price** risk, so the *number*
0.08 has to mean "8% chance of default", not merely "riskier than the next person".
That makes calibration a first-class metric. Accuracy is also the wrong target on
an imbalanced default label, so this project reports the metrics underwriters use:

- **Discrimination** — ROC-AUC, **KS** (max gap between defaulter / non-defaulter
  score CDFs) and **Gini** (`2·AUC − 1`).
- **Calibration** — **Brier score** and a **reliability curve** (predicted PD vs.
  observed default rate per bin), plus ECE.
- **Fairness** — at a fixed approval threshold, the **approval-rate gap** and
  **TPR gap** between two synthetic protected groups.

The synthetic data ([src/credit_risk/data.py](src/credit_risk/data.py)) draws each
borrower's default from a **logistic process** over real-feeling features (income,
debt-to-income, utilization, delinquencies, employment length, loan amount) plus
noise and a deliberately **baked-in group disparity** — so the fairness check has
something real to find. Imbalance is handled honestly: logistic regression uses
`class_weight="balanced"`, both models are **calibrated** (`CalibratedClassifierCV`,
isotonic) and we operate at an explicit **decline-the-riskiest-X%** threshold
rather than a naive 0.5 cut.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make run                              # train+calibrate LogReg & GBM, write figures + metrics.json
make test                             # fast smoke tests (-m "not slow")
make run ARGS="--decline-rate 0.10"   # tighter approval policy
make run ARGS="--real-csv data/credit.csv"   # optional: real public dataset (see data/README.md)
```

Outputs land in [results/](results/):
- `figures/roc_curve.png` — discrimination for both models.
- `figures/reliability_curve.png` — the **money plot**: predicted PD vs. observed default rate.
- `figures/score_distribution.png` — score separation by outcome with the operating threshold.
- `metrics.json` — ROC-AUC / KS / Gini, Brier / ECE, confusion + fairness gaps (committed).

## What the result shows

On the default synthetic run (12k borrowers, ~26% default rate): the calibrated
**LogisticRegression** reaches **ROC-AUC ≈ 0.88, KS ≈ 0.61, Gini ≈ 0.77** with a
low **Brier ≈ 0.11 / ECE ≈ 0.015** — strong, *trustworthy* PDs that track the
reliability diagonal. GradientBoosting discriminates almost identically; the point
is that both stay well calibrated after wrapping, which is what lets a lender use
the raw probability. Declining the riskiest 20% of applicants leaves an
**approval-rate gap of only ~0.01** between the protected groups even though the
data-generating process injected a disparity — a concrete demonstration that you
have to *measure* fairness at the operating point, not assume it.

## Interview story (3 sentences)

> I built a credit default scorer and evaluated it like a lender would — not on
> accuracy, but on discrimination (ROC-AUC, KS, Gini) and especially calibration
> (Brier, reliability curve), since a credit PD has to be a usable probability,
> not just a ranking. I calibrated both a logistic and a gradient-boosting model
> and operated at an explicit decline-the-riskiest-X% threshold instead of 0.5,
> because the default label is imbalanced. I then added a fairness check that
> reports the approval-rate and TPR gaps between protected groups at that
> threshold, surfacing exactly the disparity the data-generating process baked in.

## Layout

```
src/credit_risk/   utils.py (seeds) · data.py (synthetic DGP) · model.py (calibrated LogReg/GBM) · metrics.py (KS/Gini/Brier/fairness)
scripts/           run_scoring.py
tests/             test_smoke.py  (fast invariants + one @slow end-to-end)
results/           figures/*.png + metrics.json  (committed)
data/ models/      git-ignored (synthetic at runtime; optional real CSV)
```

## References

- B. W. Brier. *Verification of forecasts expressed in terms of probability.* 1950. (Brier score)
- Kolmogorov–Smirnov statistic — standard scorecard separation measure.
- Niculescu-Mizil & Caruana. *Predicting Good Probabilities With Supervised Learning.* ICML 2005. (calibration)
- Give Me Some Credit (Kaggle, 2011) · Statlog German Credit (UCI) — real-data options in [data/README.md](data/README.md).
