# p6 · PGD adversarial training

The defense that answers p1's attack: train a model on its own worst-case inputs so it stops
falling apart. I implement **Projected Gradient Descent (PGD)** from scratch, then **adversarially
train** a small CNN against it (Madry et al. 2018) and put a standard model and the robust model on
the same robustness curve. No attack/defense library — just torch.

The default run is fully **offline**: it uses a deterministic synthetic 28x28 "digit-like" dataset
(torch only, no download). Pass `ARGS=--real` to run the exact same code on real MNIST.

**Authorized use only.** Targets are models I trained myself on synthetic / public data. See
[../../ETHICS.md](../../ETHICS.md).

## The idea

A standard classifier minimizes loss on *clean* data and, as p1 (FGSM) showed, collapses under a
tiny L∞ perturbation. Adversarial training reframes the objective as a **saddle-point** problem
(Madry et al.): minimize the loss of the *worst-case* perturbed input.

```
min_θ  E_(x,y) [  max_{‖δ‖∞ ≤ ε}  L( f_θ(x + δ), y )  ]
        └── outer: train weights        └── inner: find the strongest attack
```

The inner `max` is approximated each minibatch by **PGD** — multi-step FGSM with a random start and
projection back into the ε-ball:

```
x₀   = clip( x + Uniform(-ε, ε), 0, 1 )                      # random start in the ε-ball
xₜ₊₁ = clip( xₜ + α·sign(∇ₓ L(f(xₜ), y)) )                   # gradient-ascent step
xₜ₊₁ = clip( x + clip(xₜ₊₁ - x, -ε, +ε), 0, 1 )             # project to ε-ball ∩ valid image
```

Then we take the normal optimizer step on those adversarial examples. Setting `ε = 0` recovers
ordinary training — that's exactly how the "standard" baseline is produced, so the only difference
between the two models is the inner attack.

Core attack in [src/adv_training/attack.py](src/adv_training/attack.py); the AT loop is the few
extra lines in [src/adv_training/train.py](src/adv_training/train.py) guarded by `adv_epsilon > 0`.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make run                 # trains both models if needed, runs the PGD ε-sweep, writes figures + metrics.json
make test                # fast smoke tests (attack invariants, synthetic-data checks)
make run ARGS=--real     # OPTIONAL: same experiment on real MNIST (needs torchvision)
make train               # just train + save standard.pt and adversarial.pt
```

CPU-only by design (~1 minute end-to-end on a laptop: 4 epochs each, 7-step PGD, 6k synthetic train
images). Nothing here is GPU-preferred; for real MNIST at full size you'd want more epochs, which is
the only place a GPU would help — bump `--epochs` and it still runs on CPU, just slower.

Outputs land in [results/](results/):
- `figures/robustness_curves.png` — the **money plot**: accuracy-under-PGD vs ε for both models.
- `figures/clean_vs_robust_bars.png` — clean accuracy vs robust accuracy, standard vs adversarial.
- `metrics.json` — clean + robust accuracy for both models at every ε (committed as evidence).

## What the result shows

On the default synthetic task (PGD ε-sweep, 7 steps, 1000 eval images), both models hit **100% clean
accuracy**, but under attack they diverge sharply:

| PGD ε | standard | adversarial (trained @ ε=0.1) |
|------:|---------:|------------------------------:|
| 0.00  | 100.0%   | 100.0% |
| 0.05  |  99.6%   | 100.0% |
| 0.10  |  64.3%   |  **93.1%** |
| 0.15  |  11.0%   |  56.0% |
| 0.20  |   0.1%   |  14.7% |

At the training budget (ε=0.1) adversarial training lifts robust accuracy from **64.3% → 93.1%** (a
**+28.8-point** gain) **for free on clean accuracy**. The curve also shows AT's known limits: the
robustness it buys is concentrated around the ε it trained on and still erodes for much larger
budgets — robustness is a budget you pay for, not a switch you flip.

## Interview story (3 sentences)

> After showing in p1 that a tiny L∞ perturbation destroys a normally-trained CNN, I implemented PGD
> from scratch and adversarially trained a model on its own worst-case inputs (Madry's min-max
> objective), then plotted both models on one robustness curve. Adversarial training raised
> robust accuracy at the training budget from ~64% to ~93% with no clean-accuracy cost, while the
> curve made the trade-off honest — the gains are local to the trained ε and fade for larger
> perturbations. The whole pipeline is library-free and runs offline on synthetic data in about a
> minute, with a one-flag switch to real MNIST.

## Layout

```
src/adv_training/  utils.py (seeds) · model.py (SmallCNN) · data.py (synthetic + optional MNIST)
                   attack.py (PGD) · train.py (standard + adversarial training)
scripts/           train_models.py · run_compare.py (the money target)
tests/             test_smoke.py  (fast invariants + one @slow end-to-end "AT beats standard")
results/           figures/*.png + metrics.json  (committed)
data/ models/      git-ignored (synthetic is in-memory; MNIST/weights produced at runtime)
```

## References

- Madry, Makelov, Schmidt, Tsipras, Vladu. *Towards Deep Learning Models Resistant to Adversarial
  Attacks.* ICLR 2018. [arXiv:1706.06083](https://arxiv.org/abs/1706.06083). (PGD + adversarial training)
- Goodfellow, Shlens, Szegedy. *Explaining and Harnessing Adversarial Examples.* ICLR 2015.
  [arXiv:1412.6572](https://arxiv.org/abs/1412.6572). (FGSM — the single-step special case; see p1)
