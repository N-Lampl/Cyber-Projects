# p4 · Model inversion + attribute inference

Two classic ML-privacy attacks implemented from scratch, both showing the same
uncomfortable fact: **a trained model leaks information about the data it was
trained on.** No attack library — just gradients and probabilities.

**Authorized use only.** Every target here is a model **I trained myself** on
**synthetic data**. No real people, no third-party models, no downloads on the
default path. See [../../ETHICS.md](../../ETHICS.md).

## 1 · Model inversion (gradient ascent)

Given only query access to an image classifier `f`, reconstruct an input that is
*representative of a target class* — recovering the visual signature the model
memorised (Fredrikson, Jha, Ristenpart, CCS 2015).

It is the mirror image of FGSM. FGSM perturbs a real input to *break* its
prediction; inversion optimises a **whole image from scratch** to *maximise* a
class score:

```
minimize_x   L(x) = CrossEntropy( f(x), c )  +  λ · ||x||²
x  <-  clip( x − step · ∇_x L(x), 0, 1 )      # gradient w.r.t. PIXELS, not weights
```

- `∇_x` — gradient of the loss w.r.t. the **input pixels** (model weights frozen).
- `λ·||x||²` — a weak prior keeping the image in range; a periodic Gaussian blur
  is added as an image prior so reconstructions look like the class, not noise.

The whole attack lives in [src/inversion_attribute/inversion.py](src/inversion_attribute/inversion.py).
To make the leakage *measurable* offline, the target is trained on a synthetic
10-class set where each class has a known prototype shape — so we can score how
well each reconstruction correlates with the **true** class signature.

## 2 · Attribute inference (tabular, scikit-learn)

A released classifier predicts a benign label `y` from features that include a
**sensitive attribute S**. An adversary knows a target's other features and the
model's output, but **not S**. Can they recover it?

MAP attribute-inference estimator: for each candidate value `v` of `S`, plug it
into the model and pick the `v` whose induced prediction best matches the
observed output, weighted by the marginal prior `P(S=v)`:

```
Ŝ = argmax_v  [ −| f(x with S=v) − observed |  +  log P(S=v) ]
```

We compare against a **majority-class baseline**; the *lift over baseline* is the
leakage. We sweep how strongly `S` drives the label and watch leakage rise — and
confirm that with **no** dependence (`s_signal=0`) the attack does **not** beat
the baseline. Code: [src/inversion_attribute/attribute.py](src/inversion_attribute/attribute.py).

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make run          # BOTH attacks -> figures + merged results/metrics.json   (default, fully OFFLINE)
make invert       # model inversion only
make attribute    # attribute inference only
make test         # fast smoke tests

# OPTIONAL enhanced path: invert a classifier trained on REAL MNIST (downloads ~12MB)
python3 scripts/run_inversion.py --mnist
```

Outputs land in [results/](results/):
- `figures/inversion_reconstructions.png` — true prototype (top) vs **recovered** image (bottom) per class.
- `figures/attribute_inference_sweep.png` — sensitive-attribute recovery vs the baseline as leakage grows.
- `metrics.json` — merged headline metrics (+ per-attack `metrics_inversion.json`, `metrics_attribute.json`).

## What the result shows

Inversion reconstructs every class's signature from nothing but the frozen
model's gradients (high recovery confidence + high prototype-match rate) — query
access alone leaks the training distribution. Attribute inference recovers the
sensitive attribute well above the majority baseline **exactly when** the model
relies on it, and gains nothing when it doesn't — leakage tracks dependence,
which is the principled way to reason about it. Both motivate the defenses in the
rest of track 03 (membership inference, DP-SGD).

## Interview story (3 sentences)

> I implemented two from-scratch privacy attacks: gradient-ascent model inversion
> that reconstructs class-representative images from a frozen classifier's input
> gradients, and a MAP attribute-inference attack that recovers a sensitive
> tabular feature from a released model's outputs. Both quantify *training-data
> leakage* — inversion against a known-prototype synthetic target so the
> reconstruction quality is measurable, and attribute inference scored as lift
> over a majority baseline across a dependence sweep. Together they show why
> "the model is just numbers" is wrong, and they set up the DP-SGD defense work
> in the same track.

## Layout

```
src/inversion_attribute/  utils.py (seeds) · model.py (SmallCNN) · data.py (synthetic+MNIST)
                          train.py · inversion.py (the attack) · attribute.py (sklearn attack)
scripts/                  run_inversion.py · run_attribute.py · run_all.py (merges metrics)
tests/                    test_smoke.py (fast invariants + one @slow end-to-end)
results/                  figures/*.png + metrics*.json  (committed)
data/ models/             git-ignored (synthetic in-memory; MNIST/weights at runtime)
```

## References

- Fredrikson, Jha, Ristenpart. *Model Inversion Attacks that Exploit Confidence
  Information and Basic Countermeasures.* ACM CCS 2015.
- Fredrikson et al. *Privacy in Pharmacogenetics …* (attribute inference). USENIX Security 2014.
- Shokri et al. *Membership Inference Attacks Against Machine Learning Models.* IEEE S&P 2017.
