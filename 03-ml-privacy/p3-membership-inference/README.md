# p3 · Membership inference with a small online LiRA

Given a single example, can you tell whether it was in a model's **training set**?
That's *membership inference* — the canonical privacy attack on ML. This project
implements the **Likelihood Ratio Attack (LiRA)** of Carlini et al. (S&P 2022) in
the **online, warm-started-shadows** flavour, against a model I trained myself, and
reports the metrics that actually matter for privacy: **TPR @ 1% FPR**, **AUC**, and
a log-log **ROC**.

**Authorized use only.** The target is a model I train myself on synthetic
(or, optionally, public Fashion-MNIST) data. No real user data is involved. See
[../../ETHICS.md](../../ETHICS.md).

## The idea

A model that **memorises** its training data behaves differently on members vs
non-members: it is *more confident* on examples it has seen. A naive attack just
thresholds that confidence globally — but "confident" means different things for an
easy example vs a hard one. LiRA fixes this with a **per-example, calibrated
hypothesis test**.

For each query `z = (x, y)`:

1. Train many **shadow models** on random halves of a population pool. By
   construction `z` is IN ~half of them and OUT of the other half (this is the
   *online* variant — both worlds are estimated empirically, no analytic OUT model).
2. Record each shadow's **logit-scaled confidence** on `z`'s true label
   (`φ = log(p_y / (1 − p_y))`), which is ~Gaussian, and split it into
   IN ~ `N(μ_in, σ_in²)` and OUT ~ `N(μ_out, σ_out²)`.
3. Score the **target's** confidence `φ*` by the likelihood ratio:

```
            N(φ* ; μ_in,  σ_in²)
  Λ(z)  =  ─────────────────────      →  high  ⇒  predict "member"
            N(φ* ; μ_out, σ_out²)
```

Sweeping a threshold on `Λ` over all queries gives the ROC. We report **TPR at 1%
FPR** because a real attacker cares about confident hits, not average-case AUC.

The core test ([src/lira_mia/attack.py](src/lira_mia/attack.py)) is just a per-example
two-Gaussian log-likelihood ratio.

**Warm-started shadows (the CPU trick):** every shadow is fine-tuned from one shared,
cheaply-pretrained checkpoint, so each converges in a handful of epochs. That's what
makes 16 shadows affordable on a laptop.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make attack                              # default: synthetic data, 16 warm-started shadows (~80s on CPU)
make attack ARGS='--n-shadows 8'         # smaller / faster
make attack ARGS='--no-warm-start'       # ablate the warm-start trick
make attack ARGS='--dataset fashion_mnist'   # OPTIONAL: real images (needs torchvision + ~30MB download)
make test                                # fast smoke tests
```

Outputs land in [results/](results/):
- `figures/lira_roc.png` — ROC (linear **and** log-log), LiRA vs the confidence
  baseline, annotated with AUC and TPR@1%FPR. The **money plot**.
- `figures/lira_score_hist.png` — member vs non-member LiRA score distributions.
- `metrics.json` — AUC, TPR@1%FPR, the target's train/test gap (committed as evidence).

## What the result shows

On the default synthetic run (3000-example pool, a deliberately over-fit MLP target,
16 warm-started shadows):

| attack               | AUC   | TPR @ 1% FPR |
|----------------------|-------|--------------|
| **LiRA (online)**    | 0.870 | **0.112**    |
| confidence baseline  | 0.705 | 0.028        |

The target hits **train acc 1.00 / test acc 0.60** — a 0.40 generalisation gap, i.e.
heavy memorisation. LiRA flags **~11% of true members at a 1% false-positive rate, 4×
the naive baseline**: per-example calibration is exactly what buys you the low-FPR
regime that the global threshold can't reach (see the log-log ROC).

**Honest about scale:** this is a *small* LiRA — 16 shadows, a tiny MLP, a single
target — meant to be correct, readable and CPU-runnable, not to reproduce the paper's
hundreds-of-shadows numbers. The qualitative story (LiRA ≫ global threshold, especially
at low FPR; leakage tracks the train/test gap) is the same; the absolute numbers would
climb with more shadows and a larger target. The attack strength is intentionally
driven by an over-fit target — a well-regularised model leaks far less, which is the
defense takeaway.

## Interview story (3 sentences)

> I implemented online LiRA from scratch — warm-started shadow models plus a
> per-example Gaussian likelihood-ratio test on logit-scaled confidence — to decide
> whether a given record was in a model's training set. On a self-trained, over-fit
> model it flags 11% of members at a 1% false-positive rate, roughly 4× a naive
> confidence threshold, because per-example calibration is what unlocks the low-FPR
> regime that actually matters for privacy. The same machinery is how you'd audit a
> production model's memorisation and justify defenses like DP-SGD or early stopping.

## Layout

```
src/lira_mia/   utils.py (seeds) · data.py (synthetic pool / optional Fashion-MNIST)
                model.py (SmallMLP + logit_confidence signal) · scipy_stub.py (Gaussian log-pdf)
                shadows.py (warm-start + target + shadow drivers) · attack.py (LiRA + ROC/AUC/TPR)
scripts/        run_lira.py   (end-to-end: produces figures + metrics.json)
tests/          test_smoke.py (fast invariants + one @slow end-to-end)
results/        figures/*.png + metrics.json   (committed)
data/ models/   git-ignored (default run needs neither; Fashion-MNIST downloads here)
```

## Offline / dependency notes

- **Default path is fully offline** and uses only `torch`, `scikit-learn`, `numpy`,
  `matplotlib` (no scipy — the Gaussian log-pdf is a 3-line local helper).
- **Fashion-MNIST is the only path that needs a download** (and `torchvision`,
  imported lazily). CPU-only throughout; no GPU anywhere.

## References

- Carlini, Chien, Nasr, Song, Terzis, Tramèr. *Membership Inference Attacks From
  First Principles.* IEEE S&P 2022. [arXiv:2112.03570](https://arxiv.org/abs/2112.03570).
- Shokri, Stronati, Song, Shmatikov. *Membership Inference Attacks Against Machine
  Learning Models.* IEEE S&P 2017. [arXiv:1610.05820](https://arxiv.org/abs/1610.05820).
- Ye et al. *Enhanced Membership Inference Attacks against Machine Learning Models.*
  ACM CCS 2022 (shadow-model calibration).
