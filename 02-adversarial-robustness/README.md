# 02 · Adversarial Robustness (evasion & defenses)

Attacking and defending models at inference time. Start here for the **quick win**, then build the
attack-and-defend arc that culminates in the detection capstone (track 01).

Authorized use only — see [../ETHICS.md](../ETHICS.md). All targets are self-trained or public
pretrained weights.

## Projects

| Project | Build | Status |
|---|---|---|
| **`p1-fgsm-mnist/`** | **SEED** — FGSM from scratch (~30 lines); accuracy-vs-ε curve | done |
| `p3-pretrained-foolbox/` | Attack a pretrained ResNet at inference with Foolbox (cheap, dramatic — do early) | |
| `p2-attack-zoo/` | `torchattacks==3.5.1`: PGD / C&W / DeepFool on a small CIFAR CNN (200–500 img eval) | |
| `p4-transfer-blackbox/` | Transfer + Boundary/Square attacks under a capped query budget | |
| `p5-adv-input-detector/` | Runtime adversarial-input **detector** (feature squeezing / OOD) — plays to DS strength | |
| `p6-adv-training/` | PGD adversarial training on MNIST; RobustBench eval (APGD-CE, ~50–100 imgs; cite leaderboard) | |
| `p7-randomized-smoothing/` | Certified L2 robustness (N=1000, MNIST subset) | |

**Depth-flex:** do **one** of `p6` / `p7` well, not both. (The tabular IDS-evasion idea lives in
track 01's capstone — "attack your own detector" is the stronger framing.)

## Start with `p1-fgsm-mnist`

It's the quick win: implement the gradient-sign attack by hand, see it flip a 99%-accurate classifier,
and prove the whole repo skeleton (seeds, Makefile, figures, metrics, CI) on a tiny CPU project before
the flagships depend on it. → [`p1-fgsm-mnist/`](p1-fgsm-mnist/)
