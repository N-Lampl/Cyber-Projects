# p3 · Inference-time evasion on a (pre)trained model — FGSM & PGD from scratch

Take a model that is already trained, hand it a few images it gets **100% right**, and flip its
predictions with an L∞ perturbation too small to change what the picture *means*. No retraining of
the target, no attack library required — just the model's own input gradients (FGSM and its iterative
cousin PGD). foolbox v3 is wired in as an **optional** cross-check.

**Authorized use only.** Targets are a model I trained myself on synthetic data (default) or a
public ImageNet-pretrained ResNet-18 I run locally (optional). Never run this against a model or
service you don't own. See [../../ETHICS.md](../../ETHICS.md).

## The idea

A classifier is trained by descending the loss gradient w.r.t. its **weights**. An evasion attack
ascends the loss gradient w.r.t. the **input pixels** instead — same calculus, opposite target.

**FGSM** (Goodfellow, Shlens, Szegedy 2015) — one step:

```
x_adv = clip( x + ε · sign( ∇_x L(f(x), y) ), 0, 1 )
```

**PGD** (Madry et al. 2018) — FGSM applied iteratively and projected back into the ε-ball:

```
repeat:  x ← clip_[x₀-ε, x₀+ε]( x + α · sign( ∇_x L ) );  x ← clip(x, 0, 1)
```

Both are **L∞** (every pixel moves by at most ε) and **white-box**. The target model folds its own
normalization in (see [`src/pretrained_foolbox/model.py`](src/pretrained_foolbox/model.py)) so ε is a
fraction of full pixel intensity — the only space where a human can judge "how big is this edit". The
attack code ([`src/pretrained_foolbox/attack.py`](src/pretrained_foolbox/attack.py)) is byte-for-byte
identical whether the victim is the offline SmallCNN or a pretrained ResNet-18.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make attack        # OFFLINE default: train SmallCNN on synthetic data, run FGSM/PGD sweep + figures + metrics.json
make test          # fast smoke tests (attack invariants)
make pretrained    # OPTIONAL online: attack torchvision ResNet-18 on CIFAR (~45MB weights); auto-falls back offline
```

The **default `make attack` runs fully offline** with only torch/torchvision/numpy/matplotlib —
synthetic data and a self-trained target, no downloads. `make pretrained` is the
"attack-a-PRETRAINED-model" path from the spec: it downloads ImageNet ResNet-18 weights and a few
CIFAR-10 images. **GPU is not needed** (no training of the big model; inference + gradients on a
handful of images is fast on CPU). If the weight/dataset download fails (offline, proxy), the script
prints a notice and transparently falls back to the offline SmallCNN, recording `used_pretrained:
false` in `metrics.json`.

Outputs land in [results/](results/):
- `figures/accuracy_confidence_vs_epsilon.png` — accuracy collapse (FGSM vs PGD) **and** the
  confidence-in-true-class collapse.
- `figures/clean_vs_adversarial.png` — the same images, clean vs FGSM, with predicted label +
  confidence (red = flipped).
- `metrics.json` — clean accuracy, accuracy/confidence at each ε for both attacks (committed evidence).

## What the result shows

On the committed offline run: the target is **100% accurate and ~99% confident** on clean images, yet
**FGSM** drives accuracy to **0%** by ε≈0.16, and the iterative **PGD** is strictly stronger
(45% vs 81% accuracy at ε=0.04 — it finds the worst point inside the same ε-budget). Mean confidence
in the true class falls from **98.5% → 0.1%**. The lesson generalizes directly to the optional
ResNet-18 path: high inference accuracy says **nothing** about robustness, and "pretrained and
deployed" is not "safe to trust on adversarial input".

## Interview story (3 sentences)

> I attacked a model at inference time — no retraining — by ascending the loss gradient w.r.t. the
> input pixels, implementing both single-step FGSM and iterative PGD from scratch and showing PGD is
> the stronger threat model. A target that was 100% accurate and 99% confident collapsed to 0%
> accuracy under an L∞ perturbation too small to change the image's meaning, and its confidence
> collapsed with it. The same code attacks a torchvision ImageNet ResNet-18 unchanged, which is the
> point: shipping a pretrained model says nothing about its adversarial robustness.

## Layout

```
src/pretrained_foolbox/  utils.py (seeds) · model.py (SmallCNN + ResNet-18 loader, folded Normalize)
                         · data.py (synthetic + optional CIFAR) · train.py · attack.py (FGSM/PGD + foolbox)
scripts/                 run_attack.py  (offline default; --pretrained for the online path)
tests/                   test_smoke.py  (fast attack invariants + one @slow end-to-end)
results/                 figures/*.png + metrics.json  (committed)
data/ models/            git-ignored (synthetic in-code; downloads only on the optional path)
```

## References

- Goodfellow, Shlens, Szegedy. *Explaining and Harnessing Adversarial Examples.* ICLR 2015.
  [arXiv:1412.6572](https://arxiv.org/abs/1412.6572).
- Madry, Makelov, Schmidt, Tsipras, Vladu. *Towards Deep Learning Models Resistant to Adversarial
  Attacks (PGD).* ICLR 2018. [arXiv:1706.06083](https://arxiv.org/abs/1706.06083).
- foolbox v3 — Rauber et al., *Foolbox Native.* [github.com/bethgelab/foolbox](https://github.com/bethgelab/foolbox).
- torchvision pretrained models. [pytorch.org/vision/stable/models.html](https://pytorch.org/vision/stable/models.html).
