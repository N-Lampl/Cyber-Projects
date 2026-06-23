# p4 · Transferability + black-box attacks (from scratch)

Real attackers rarely have your model's gradients. This project shows the two
ways they win anyway: (1) **transfer** — craft adversarials on a *surrogate* you
control and fire them blind at the target, and (2) **query-based black-box** —
poke the target with a *capped query budget* and let random search do the rest.
Two different small classifiers, all attacks hand-rolled in torch/numpy (no ART,
foolbox or torchattacks).

**Authorized use only.** Both models are trained by me on synthetic / public
data, attacked locally. See [../../ETHICS.md](../../ETHICS.md).

## The idea

We train **two deliberately different** nets so transfer is non-trivial:

| role | model | why |
|------|-------|-----|
| surrogate (white-box) | `SmallCNN` — 2 conv layers, ReLU | what the attacker *can* differentiate |
| target (black-box)    | `SmallMLP` — fully-connected, Tanh | what the attacker actually wants to break |

**1. Transfer.** With white-box access to the surrogate we run L∞ **PGD**
(Madry et al. 2018) — iterated FGSM projected back into the ε-ball:

```
x_{t+1} = clip_[0,1]( proj_ε( x_t + α · sign( ∇_x L(f_surrogate(x_t), y) ) ) )
```

Then we evaluate those *same* images on the target. The drop in target accuracy
is the transfer rate — no target gradients used.

**2. Query-based black-box.** The target is hidden behind a `QueryOracle` that
*counts every call* and exposes only scores or labels. Two classic attacks,
written from scratch, each stopping at a fixed `query_budget`:

- **Square Attack** (Andriushchenko et al. 2020) — *score-based*, L∞. Each step
  flips a random square patch to ±ε; keep the change only if the margin loss
  improves. Pure random search, zero gradients.
- **Boundary Attack** (Brendel et al. 2018) — *decision-based*, L2. Needs only
  the predicted **label**. Start from an adversarial point, random-walk along the
  decision boundary while contracting toward the original image.

```
QueryOracle.scores(x) -> logits   (score-based, +len(x) queries)
QueryOracle.labels(x) -> argmax    (decision-based, +len(x) queries)
```

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make attack                 # trains BOTH models (if needed) + transfer + black-box + figures + metrics.json
make train                  # just train the CNN surrogate + MLP target
make test                   # fast smoke tests (attack invariants, query budget caps)

# optional REAL-MNIST path (needs torchvision; downloads ~11MB to data/):
python scripts/run_attacks.py --real
```

**Default path is fully offline** — synthetic 8×8 digit glyphs, only
torch/numpy/matplotlib needed. Real MNIST is an opt-in enhancement.

Outputs land in [results/](results/):
- `figures/transfer_vs_epsilon.png` — surrogate (white-box) vs target (transfer)
  accuracy as ε grows.
- `figures/blackbox_vs_budget.png` — Square vs Boundary success rate vs query budget.
- `metrics.json` — clean accuracies, transfer curves, per-budget success rates,
  average queries used (committed as evidence).

## What the result shows

From the committed run (synthetic glyphs, seed 42):

- **Transfer is real but weaker than white-box.** PGD drives the surrogate to
  ~0% accuracy by ε=0.2, yet the *different-architecture* target still holds
  ~97% there — and only collapses to ~29% at ε=0.4. Transfer works, but you pay
  for not having the target's gradients (the classic white-box ≥ transfer gap).
- **Query attacks are devastating under a tiny budget.** The score-based Square
  attack climbs 42% → 95% success as the budget grows 25 → 400 queries/image;
  the decision-based Boundary attack finds adversarial points almost immediately
  (label-only access is enough on this small target). Capping queries directly
  trades attacker success for stealth — which is exactly the dial a defender's
  rate-limiting turns.

## Interview story (3 sentences)

> I built a transfer + black-box attack study: I train two different small
> classifiers, craft PGD adversarials on a CNN surrogate, and show they transfer
> to a fully-connected target even though the attacker never touches the target's
> gradients. Then I hand-roll the Square (score-based) and Boundary
> (decision-based) attacks behind a query-counting oracle and plot success rate
> versus a capped query budget. It makes concrete that "no gradient access" is
> not a defense, and that query rate-limiting is a real, measurable mitigation.

## Layout

```
src/transfer_blackbox/  utils.py (seeds) · data.py (synthetic glyphs + real MNIST)
                        model.py (SmallCNN + SmallMLP) · train.py
                        attacks.py (PGD/transfer + QueryOracle + Square + Boundary)
scripts/                train_models.py · run_attacks.py
tests/                  test_smoke.py (fast invariants + one @slow end-to-end)
results/                figures/*.png + metrics.json  (committed)
data/ models/           git-ignored (synthetic at runtime / MNIST downloaded / weights produced)
```

## References

- Goodfellow, Shlens, Szegedy. *Explaining and Harnessing Adversarial Examples.*
  ICLR 2015. [arXiv:1412.6572](https://arxiv.org/abs/1412.6572).
- Madry et al. *Towards Deep Learning Models Resistant to Adversarial Attacks.*
  ICLR 2018. [arXiv:1706.06083](https://arxiv.org/abs/1706.06083). (PGD)
- Papernot, McDaniel, Goodfellow. *Transferability in Machine Learning.*
  [arXiv:1605.07277](https://arxiv.org/abs/1605.07277).
- Andriushchenko et al. *Square Attack: a query-efficient black-box adversarial
  attack via random search.* ECCV 2020. [arXiv:1912.00049](https://arxiv.org/abs/1912.00049).
- Brendel, Rauber, Bethge. *Decision-Based Adversarial Attacks (Boundary Attack).*
  ICLR 2018. [arXiv:1712.04248](https://arxiv.org/abs/1712.04248).
