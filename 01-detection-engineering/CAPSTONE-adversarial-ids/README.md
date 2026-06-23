# CAPSTONE · Adversarial IDS — evade it, then harden it

The flagship of the detection-engineering track. Take the **shared `ids_pipeline`
RandomForest** intrusion detector, craft network flows that **evade it under
realistic feature-mutability constraints**, measure how often the attack
succeeds, then **harden** the model and re-measure — producing an **IDS
Robustness Report Card** (markdown + figure + `metrics.json`).

**Authorized use only.** The target is an IDS I trained myself on synthetic /
self-downloaded data. The attack only crafts inputs against my own model in this
repo. See [../../ETHICS.md](../../ETHICS.md).

## The problem

A NIDS with 93% clean accuracy looks production-ready. But an attacker does not
send random noise — they *craft* traffic to slip past the model. Unlike an image
attack, they cannot perturb pixels freely: they can only change features they
physically control (pad bytes, hold a connection open, split connections) and
the result must remain a **valid, self-consistent flow** or it is dropped by a
sanity check long before it reaches the model.

This project shows that, under those realistic constraints, **83% of the attacks
the IDS originally caught can be made to evade it** — and that a targeted defense
drives that to **~0%** with **no loss of clean accuracy**.

## The method

```
                 query labels                 input gradient            transfer
 RandomForest ──────────────▶ Logistic        ──────────────▶ constrained ──────────▶ RandomForest
 IDS (target)   (black-box)   SUBSTITUTE        ∇ₓ loss        FGSM (mutable           IDS (target)
 non-diff.                     (differentiable)                feats only)             measure ASR
```

1. **Train** the shared leak-free RandomForest IDS on synthetic flows.
2. **Substitute** — the tree has no input gradient, so fit a logistic regression
   to the target's *predictions* (Papernot et al. 2017). For a logistic head the
   raw-space gradient is closed-form: `∇ₓ L = (p − y)·w / scale`.
3. **Constrained FGSM** — step along the gradient sign, but only on **mutable**
   features, only in **attacker-feasible directions**, projected back into the
   per-feature **validity box** after every step:

   ```
   δ      = step · sign(∇ₓ L)
   δ      = mask(δ)                  # immutable features → 0; increase-only → max(δ,0)
   x_adv  = clip(x + δ, ε-box)       # L∞ budget = ε · feature-std
   x_adv  = clip(x_adv, valid_box)   # rates∈[0,1], counts≥0, …
   ```

   | mutable (attacker-controlled) | immutable (held fixed) |
   |---|---|
   | duration, src_bytes (increase-only) | serror_rate, rerror_rate |
   | dst_bytes, count, srv_count (bidirectional) | same/diff_srv_rate, dst_host_count |
   | | protocol_type / service / flag (connection identity) |

4. **Transfer & measure** the examples against the *deployed* RandomForest →
   genuine transfer **attack-success-rate (ASR)**, counting only flows that
   stayed feasible and consistent.
5. **Harden** (adversarial training by default; diverse-ensemble alternative)
   and re-run the whole attack against the new model.

The hand-rolled FGSM is the **default offline path** (numpy + scikit-learn only).
**IBM ART** (`adversarial-robustness-toolbox==1.20.1`) is an optional drop-in
(`--use-art`) wrapped in try/except — if it is missing the run transparently
falls back to the hand-rolled attack.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make attack                         # train → attack → harden → write the report card
make attack ARGS='--defense ensemble'   # harden with a diverse ensemble instead
make attack ARGS=--use-art          # use IBM ART if installed (else falls back)
make test                           # fast smoke tests
```

Outputs land in [results/](results/):
- `report_card.md` — the **IDS Robustness Report Card** (graded A–F).
- `figures/report_card.png` — ASR before/after + clean metrics retained.
- `figures/perturbation_by_feature.png` — which features the attack moved
  (mutable in red; immutable untouched).
- `metrics.json` — clean accuracy, `asr_before`, `asr_after`, constraint
  compliance (committed as evidence).

## What the result shows (default synthetic run, seed 42)

| | Before hardening | After hardening (adv. training) |
|---|---|---|
| Clean accuracy | 0.926 | 0.924 |
| Clean ROC-AUC | 0.968 | 0.966 |
| **Attack success rate** | **83.2%** | **0.0%** |

- The constrained attack evades **485 / 583** originally-detected attacks while
  keeping **100%** of flows feasible and immutable features untouched.
- **Adversarial training** crushes ASR to ~0% with a −0.002 hit to clean
  accuracy. The cheaper **diverse-ensemble** defense only gets ASR to ~76% —
  a useful, honest contrast: re-training on the attack distribution beats merely
  roughening the model.

## Interview story (3 sentences)

> I evaded a 93%-accurate RandomForest intrusion detector by training a
> differentiable substitute, running a from-scratch FGSM that only perturbs the
> features an attacker actually controls, and transferring those flows back to
> the real model — 83% of caught attacks slipped through while staying valid
> network flows. Then I hardened the IDS with constrained adversarial training
> and drove the attack-success-rate to near zero with no loss of clean accuracy,
> and packaged the whole before/after as a graded "robustness report card." It
> proves clean accuracy is not a security metric, and shows the substitute +
> feature-constraint + adversarial-training loop that makes a detector
> deployable.

## Layout

```
src/adversarial_ids/  constraints.py (mutability + validity) · surrogate.py
                      (differentiable substitute) · attack.py (constrained FGSM
                      + optional ART) · harden.py (adv. training / ensemble) ·
                      report.py · utils.py (seeds + loads shared ids_pipeline)
scripts/              run_capstone.py  (the one-shot money target)
tests/                test_smoke.py    (fast invariants + one @slow end-to-end)
results/              report_card.md · figures/*.png · metrics.json  (committed)
data/ models/         git-ignored (synthetic by default; NSL-KDD optional)
```

The leak-free preprocessing + RandomForest live in
[`../shared/ids_pipeline`](../shared/ids_pipeline) and are imported **by path**,
so `p1-nids-baseline` and this capstone attack *exactly* the same model.

## References

- Goodfellow, Shlens, Szegedy. *Explaining and Harnessing Adversarial Examples.*
  ICLR 2015. [arXiv:1412.6572](https://arxiv.org/abs/1412.6572).
- Papernot et al. *Practical Black-Box Attacks against Machine Learning.* ASIA
  CCS 2017 (substitute-model transfer). [arXiv:1602.02697](https://arxiv.org/abs/1602.02697).
- Madry et al. *Towards Deep Learning Models Resistant to Adversarial Attacks.*
  ICLR 2018 (adversarial training). [arXiv:1706.06083](https://arxiv.org/abs/1706.06083).
- Sheatsley et al. *On the Robustness of Domain Constraints* (constrained
  adversarial examples for NIDS), and the NSL-KDD benchmark (Tavallaee 2009).
- IBM **Adversarial Robustness Toolbox** v1.20.1 (optional attack backend).
