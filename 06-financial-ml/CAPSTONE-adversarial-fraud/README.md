# CAPSTONE · Adversarial Fraud — attack AND defend a fraud model

<!-- realdata-banner -->
> **Why synthetic here (on purpose).** The feature-mutability attack needs interpretable features (a fraudster changing *amount/timing* but not account age). Real fraud data (ULB) is anonymized PCA components that can't express that, so this capstone uses a realistic synthetic generator. Real-data fraud results live in p1/p2.

The finance mirror of the detection track's adversarial-IDS capstone. I train a
fraud classifier, then **evade** it by crafting adversarial fraudulent
transactions under a realistic threat model (a fraudster can change
amount/timing/merchant, but **not** account history), measure the
attack-success-rate, then **harden** the model with adversarial training and
re-measure. The deliverable is a one-page *Fraud Model Robustness Report Card*.

**Authorized use only.** Everything here is synthetic data and models I trained
myself — no real cardholders, no production systems. See [../../ETHICS.md](../../ETHICS.md).

## The idea

A fraud model with a great PR-AUC can still be trivial to evade if an attacker
nudges the few fields they actually control. The attack must respect a **feature
mutability** contract, which is what makes it a *finance* problem and not a toy
image attack:

| Mutable (attacker-controlled) | Immutable (server-side / account history) |
|---|---|
| `amount`, `hour`, `merchant_risk`, `distance_from_home`, `n_items` | `account_age_days`, `avg_amount_30d`, `txn_count_30d`, `home_country_risk`, `card_present` |

On top of mutability the attack enforces **plausibility bounds** (e.g. amount in
`[$1, $5000]`), **integer fields** (`hour`, `n_items` are rounded), and a
**consistency** rule (amount can't collapse below 5% of the account's own 30-day
average — a $0.01 "big purchase" isn't realistic fraud).

The attack itself ([src/adv_fraud/attack.py](src/adv_fraud/attack.py)) is a
hand-rolled, numpy-only **greedy finite-difference descent** — the tabular
analogue of FGSM/PGD with no attack library. The sklearn pipeline isn't
differentiable, so each step estimates `d(score)/d(feature)` by central finite
differences over the *mutable* features only, steps downhill in fraud-score
space, then projects back into the feasible set:

```python
grad[:, i] = (score(X + h·e_i) - score(X - h·e_i)) / (2h)   # finite diff
X[:, mutable] -= step · grad[:, mutable] / ||grad||         # normalized step
X = project(X, X0)   # clip bounds, round ints, revert immutables, enforce amount floor
```

The **defense** ([src/adv_fraud/defense.py](src/adv_fraud/defense.py)) is
iterative adversarial training (a tabular take on Madry et al.'s min-max loop):
attack the current model, fold the crafted evasions back in **still labelled
fraud**, refit, repeat. The hardened head defaults to gradient boosting, which
can carve out the bounded fraud region a single hyperplane cannot.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make run            # train -> attack -> harden -> figures + metrics.json + REPORT_CARD.md
make test           # fast smoke tests (-m "not slow")
make run ARGS=...    # see flags below

python scripts/run_capstone.py --model logreg --rounds 3 --steps 40
python scripts/run_capstone.py --linear-defense   # keep the hardened model linear (harder defense)
```

Outputs land in [results/](results/):
- `figures/robustness_before_after.png` — the **money plot**: ASR collapses while clean PR-AUC rises.
- `figures/score_shift.png` — the attack pushing caught-fraud scores below the alert threshold.
- `metrics.json` — clean PR-AUC/ROC-AUC, ASR_before, ASR_after, feasibility & consistency rates.
- `REPORT_CARD.md` — the one-page robustness report card.

## What the result shows

With the default seed: the baseline logistic model has clean **PR-AUC ≈ 0.42 /
ROC-AUC ≈ 0.92**, yet the feasibility-constrained attack reaches **ASR = 100%**
on the frauds it caught — every counted evasion is feasible (feasibility = 1.0),
i.e. realizable by an actual fraudster. After 3 rounds of adversarial training
the hardened (gradient-boosted) model drops **ASR to 0%** *and* improves clean
**PR-AUC to ≈ 0.65** with recall-at-budget rising from 0.63 to 0.85 — robustness
and detection both go up. The honest caveat printed on the card: ~13% of the
*old* baseline-crafted evasions still slip past the hardened model, so this is
not a clean sweep.

## Interview story (3 sentences)

> I trained a fraud classifier and then attacked it with a hand-rolled,
> numpy-only evasion search that only perturbs the fields a real fraudster
> controls — amount, timing, merchant — within plausibility and consistency
> bounds, and drove its attack-success-rate to 100%. I then closed the gap with
> iterative adversarial training, cutting ASR to 0% while *raising* clean PR-AUC,
> and reported the residual transfer risk honestly on a one-page report card.
> It's the same min-max story as the adversarial-IDS capstone, but with finance's
> feature-mutability constraints that make the threat model realistic.

## Layout

```
src/adv_fraud/   utils.py (seeds, CPU) · data.py (synthetic gen + threat model) ·
                 model.py (sklearn pipeline) · metrics.py (PR-AUC, p@k, recall@FPR) ·
                 attack.py (feasibility-constrained evasion) · defense.py (adv training)
scripts/         run_capstone.py  (train -> attack -> harden -> figures/metrics/report)
tests/           test_smoke.py    (fast invariants + one @slow end-to-end)
results/         figures/*.png + metrics.json + REPORT_CARD.md   (committed)
data/ models/    git-ignored (synthetic data is generated in-memory at runtime)
```

## References

- Goodfellow, Shlens, Szegedy. *Explaining and Harnessing Adversarial Examples.* ICLR 2015. [arXiv:1412.6572](https://arxiv.org/abs/1412.6572)
- Madry et al. *Towards Deep Learning Models Resistant to Adversarial Attacks.* ICLR 2018. [arXiv:1706.06083](https://arxiv.org/abs/1706.06083)
- Ballet et al. *Imperceptible Adversarial Attacks on Tabular Data.* 2019. [arXiv:1911.03274](https://arxiv.org/abs/1911.03274) (feature-mutability for tabular attacks)
- Optional real benchmark: ULB/Worldline *Credit Card Fraud Detection* (Kaggle, DbCL v1.0) — see [data/README.md](data/README.md).
