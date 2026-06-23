# p2 · Attack zoo — PGD vs C&W vs DeepFool (from scratch)

After [FGSM](../p1-fgsm-mnist) (one gradient step), this project implements the three classic
**iterative** white-box evasion attacks **by hand** — no attack library — and benchmarks them head to
head on a small CNN: success rate, perturbation size (L2 / L∞) and runtime. The point is to make the
*trade-offs* concrete: cheap-but-blunt vs slow-but-minimal.

**Authorized use only.** The target is a model I trained myself on synthetic (or public) data.
See [../../ETHICS.md](../../ETHICS.md).

## The attacks

All three nudge an input `x` (true label `y`) until the model is wrong, but they optimize different
things:

**PGD — Projected Gradient Descent** (Madry et al. 2018). Multi-step FGSM: take a small signed-gradient
step, then *project* back into an L∞ ε-ball, repeat. Strong, fast, but every pixel can move up to ε.
```
δ ← Uniform(−ε, ε);   repeat:  δ ← clip_ε( δ + α·sign(∇ₓ L(x+δ, y)) ),   x+δ ∈ [0,1]
```

**C&W — Carlini & Wagner L2** (2017). The gold-standard *minimal-L2* attack. Optimize an unconstrained
`w` with `x_adv = ½(tanh(w)+1)` (always a valid image, no clipping) to minimize
`‖x_adv − x‖₂² + c·f(x_adv)`, where `f` drives the true-class logit below the best other logit. Slow
(an Adam loop per batch) but finds tiny perturbations.

**DeepFool** (Moosavi-Dezfooli et al. 2016). Linearize every class boundary around the current point
and step to the *nearest* one; iterate. Approximates the minimal L2 perturbation geometrically.

The implementations are ~1 function each in [src/attack_zoo/attacks.py](src/attack_zoo/attacks.py).

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make attack            # trains the target if needed, runs all 3 attacks, writes figures + metrics.json
make test              # fast smoke tests (attack invariants)
make attack ARGS='--source cifar10'   # OPTIONAL real-data path (downloads CIFAR-10, slower)
make attack ARGS='--source mnist'     # OPTIONAL real-data path (downloads MNIST)
```

**Default path is fully offline** — it trains the SmallCNN on a deterministic **synthetic** image
dataset (no download) and runs all three attacks in well under a minute on CPU. The whole `make attack`
(train + 3 attacks + figures) is ~30s on a laptop CPU. The optional `--source cifar10|mnist` paths use
real `torchvision` datasets (a 3-class subset, 3 epochs) and are the only paths that touch the network.

Outputs land in [results/](results/):
- `figures/attack_comparison.png` — success rate + runtime per attack.
- `figures/perturbation_sizes.png` — mean L2 / L∞ per attack (the stealth axis).
- `figures/clean_vs_attacks.png` — same images under each attack, with (mis)predictions.
- `metrics.json` — the full comparison table (committed as evidence).

## What the result shows

On the default synthetic run (clean accuracy **100%**, 200 eval images, seed 42):

| attack    | success | mean L2 | mean L∞ | runtime |
|-----------|--------:|--------:|--------:|--------:|
| PGD       |  97.5%  |  5.31   | **0.100** | **2.4s** |
| C&W-L2    | **100%**| **3.87**|  0.248  |  10.6s  |
| DeepFool  |  81.5%  |  4.11   |  0.377  |   7.7s  |

The trade-off is exactly the textbook one: **PGD** is the cheapest and stays inside its L∞ budget but
moves a lot of L2 mass; **C&W** is the most reliable and has the **smallest L2** (stealthiest in that
norm) but is the slowest; **DeepFool** sits in between as a fast minimal-L2 approximation. All three
drive a 100%-accurate model to mostly-wrong with perturbations bounded by the budget — reinforcing
[p1](../p1-fgsm-mnist)'s lesson that clean accuracy says nothing about robustness, and giving us the
attack toolkit the defenses later in track 02 have to survive.

## Interview story (3 sentences)

> I hand-implemented the three canonical iterative evasion attacks — PGD (L∞), Carlini-Wagner (L2) and
> DeepFool — and benchmarked them on the same classifier so the trade-offs are measurable, not folklore.
> The table shows PGD is fast but blunt, C&W is slow but finds the smallest L2 perturbation, and
> DeepFool is a quick minimal-L2 approximation — the exact knobs a red team weighs when picking an
> attack. Building them from scratch (not calling a library) means I understand the gradient math well
> enough to port it to non-image targets like the tabular IDS in my capstone.

## Layout

```
src/attack_zoo/   utils.py (seeds) · model.py (SmallCNN) · data.py (synthetic + opt CIFAR/MNIST)
                  train.py · attacks.py (pgd / cw_l2 / deepfool) · evaluate.py (run_attack metrics)
scripts/          train_target.py · run_attacks.py
tests/            test_smoke.py  (fast invariants + one @slow end-to-end)
results/          figures/*.png + metrics.json  (committed)
data/ models/     git-ignored (synthetic is in-memory; real data downloaded on demand)
```

## Optional enhanced path

`torchattacks==3.5.1` (in `requirements.txt`, commented out) can be used as a reference to cross-check
the from-scratch PGD via `pgd(model, x, y, backend="torchattacks")`. It is imported **lazily** inside
the function, so the package imports and the default run works without it installed.

## References

- Madry, Makelov, Schmidt, Tsipras, Vladu. *Towards Deep Learning Models Resistant to Adversarial
  Attacks.* ICLR 2018. [arXiv:1706.06083](https://arxiv.org/abs/1706.06083) (PGD).
- Carlini, Wagner. *Towards Evaluating the Robustness of Neural Networks.* IEEE S&P 2017.
  [arXiv:1608.04644](https://arxiv.org/abs/1608.04644) (C&W).
- Moosavi-Dezfooli, Fawzi, Frossard. *DeepFool: a simple and accurate method to fool deep neural
  networks.* CVPR 2016. [arXiv:1511.04599](https://arxiv.org/abs/1511.04599).
