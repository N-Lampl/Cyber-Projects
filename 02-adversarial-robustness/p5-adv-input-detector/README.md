# p5 · Runtime adversarial-input detector (feature squeezing + sklearn)

The defense side of the FGSM story (p1): instead of making the model robust, put a **cheap runtime
guard in front of it** that flags inputs that look adversarial *before* they're trusted. Built with
torch + scikit-learn only — no attack/defense libraries.

**Authorized use only.** The target is a model I trained myself on synthetic / public data, and the
FGSM examples are generated against my own model. See [../../ETHICS.md](../../ETHICS.md).

## The idea

**Feature squeezing** (Xu, Evans, Qi — NDSS 2018). Adversarial perturbations hide in the
high-precision, high-frequency corners of input space that don't matter for clean classification. So
"squeeze" the input to a coarser version and compare predictions:

```
score(x) = max over squeezers s of  || softmax(f(x)) - softmax(f(s(x))) ||_1
```

If a small squeeze causes a big swing in the model's output, the input was probably riding a fragile
adversarial direction. Two classic squeezers, both plain torch:

- **bit-depth reduction** — round each pixel to `bits` bits of precision (erases tiny ±ε steps).
- **median blur** (k×k) — replace each pixel by its neighborhood median (erases FGSM speckle).

We add four cheap **input statistics** (total variation, pixel std, mid-gray fraction, mean) because
FGSM's near-uniform ±ε noise inflates high-frequency energy. That gives a **7-dimensional feature
vector** per input, on which we train a scikit-learn **LogisticRegression** detector
(clean = 0, successful FGSM = 1). At deployment we pick a **threshold** that holds clean
false-positives under a target budget (default 5%).

```
input x ──► feature squeezing (bit-depth, median) ─┐
        └─► input statistics (TV, std, ...) ────────┴─► [7 feats] ─► scaler ─► LogReg ─► P(adv) ─► threshold
```

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make detect                          # OFFLINE DEFAULT: synthetic digits, no download
make detect ARGS="--dataset mnist"   # OPTIONAL: real MNIST (~11MB auto-download)
make detect ARGS="--epsilon 0.3 --bits 1 --target-fpr 0.02"
make test                            # fast smoke tests
```

The **default path is fully offline**: it uses a deterministic synthetic 28×28 "digit" dataset and
needs only `torch, scikit-learn, numpy, matplotlib`. The optional `--dataset mnist` path lazily
imports `torchvision`; if the download fails it falls back to synthetic automatically.

Outputs land in [results/](results/):
- `figures/detector_roc.png` — ROC with the chosen operating point marked.
- `figures/detector_pr.png` — precision/recall curve.
- `figures/feature_separation.png` — why it works: squeeze-shift vs total-variation scatter.
- `metrics.json` — ROC-AUC, average precision, and the operating point (precision/recall/FPR + confusion).

## What the result shows

The detector separates clean inputs from *successful* FGSM attacks with high ROC-AUC, and at a fixed
~5% clean false-positive rate it catches the large majority of attacks. The driving signals are exactly
what the theory predicts: adversarial inputs swing more under feature squeezing and carry extra
high-frequency energy (total variation / mid-gray pixels) from the ±ε speckle — you can see this in
`detector_coefficients` in metrics.json and in the `feature_separation.png` scatter. Concrete numbers
for this run are in [results/metrics.json](results/metrics.json) (`summary` field).

> On the offline synthetic dataset the two classes are very cleanly separable (ROC-AUC ≈ 1.0); on real
> MNIST (`--dataset mnist`) expect a still-strong but more realistic AUC. The point of the synthetic
> default is a zero-download, deterministic demo of the full detection pipeline.

> Note: feature squeezing is a *detection* heuristic, not a guarantee — an adaptive attacker who knows
> the squeezers can partially evade it. It's a cheap first line of defense, layered with the
> robustness work elsewhere in this track.

## Interview story (3 sentences)

> I built a runtime detector that flags adversarial inputs before a model trusts them, using feature
> squeezing (bit-depth reduction + median blur) plus a few input statistics fed to a logistic-regression
> classifier trained on clean vs FGSM examples. I evaluate it the way a defender actually deploys it —
> ROC-AUC plus the precision/recall at a fixed clean false-positive budget, picking an explicit
> operating threshold. It pairs directly with my FGSM-from-scratch attack project to tell a complete
> attack-then-defend story.

## Layout

```
src/adv_detector/  utils.py (seeds) · model.py (SmallCNN) · data.py (synthetic + optional MNIST)
                   attack.py (FGSM) · squeeze.py (squeezers + features) · detector.py (sklearn)
scripts/           run_detector.py
tests/             test_smoke.py  (fast invariants + one @slow end-to-end)
results/           figures/*.png + metrics.json  (committed)
data/ models/      git-ignored (downloaded / produced at runtime)
```

## References

- Xu, Evans, Qi. *Feature Squeezing: Detecting Adversarial Examples in Deep Neural Networks.* NDSS 2018.
  [arXiv:1704.01155](https://arxiv.org/abs/1704.01155).
- Goodfellow, Shlens, Szegedy. *Explaining and Harnessing Adversarial Examples.* ICLR 2015.
  [arXiv:1412.6572](https://arxiv.org/abs/1412.6572).
- scikit-learn `LogisticRegression`, `roc_curve`, `precision_recall_curve` docs.
