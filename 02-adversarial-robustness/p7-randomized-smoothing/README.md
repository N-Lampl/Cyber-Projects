# p7 · Certified L2 robustness via randomized smoothing

Most of track 02 is cat-and-mouse: attack, defend, stronger attack. This project flips to a
**certificate** — a *provable* guarantee that **no** L2 perturbation below a radius `R` can change the
prediction. We implement **randomized smoothing** (Cohen, Rosenfeld, Kolter, 2019) by hand: Gaussian
sampling, a Clopper-Pearson lower bound, and the exact radius formula — then plot certified accuracy
vs radius on a small subset.

**Authorized use only.** The target is a model I trained myself on synthetic data (or my own MNIST
download). See [../../ETHICS.md](../../ETHICS.md).

## The idea

Given any base classifier `f`, define the **smoothed** classifier as the most likely label when the
input is corrupted by Gaussian noise:

```
g(x) = argmax_c  P_{e ~ N(0, sigma^2 I)} [ f(x + e) = c ]
```

`g` is harder to fool because a small input shift barely changes the noise distribution. Cohen et al.
prove that if the top class `cA` is returned with probability at least `pA`, then `g` is **constant**
inside an L2 ball of radius

```
R = sigma * Phi^{-1}(pA)            (Phi^{-1} = standard-normal quantile)
```

We can't know `pA` exactly, so we **estimate it from samples and use a high-confidence LOWER bound** —
that keeps the certificate sound:

**CERTIFY (Algorithm 1)** for one point `x`:
1. **Select** the winning class `cA` from `n0` noisy forward passes (majority vote).
2. **Estimate** `nA = #{ f(x+e) = cA }` over `n` *fresh* noisy samples (default `n = 1000`).
3. **Clopper-Pearson** one-sided lower bound `pA_bar` on `P(f(x+e)=cA)` at confidence `1 - alpha`.
4. If `pA_bar > 1/2`: **certify** `cA` with radius `R = sigma * Phi^{-1}(pA_bar)`. Else **ABSTAIN**.

The Clopper-Pearson bound is the exact-binomial quantile `Beta(alpha; nA, n - nA + 1)`, so the whole
certificate holds with probability `>= 1 - alpha` over the sampling. The core
([src/rand_smoothing/smoothing.py](src/rand_smoothing/smoothing.py)):

```python
counts0 = self._sample_counts(x, n0, batch)    # selection
c_a     = int(counts0.argmax())
counts  = self._sample_counts(x, n, batch)     # estimation (fresh samples)
p_a_lower = clopper_pearson_lower(int(counts[c_a]), n, alpha)
if p_a_lower > 0.5:
    return c_a, self.sigma * norm_ppf(p_a_lower)   # R = sigma * Phi^-1(pA)
return ABSTAIN, 0.0
```

**Why train with noise?** `f` only sees noisy inputs at certification time, so it's trained with
Gaussian augmentation at the same `sigma` ([train.py](src/rand_smoothing/train.py)).

## Offline by default

The default path is **fully offline** and uses only always-installed libs (`torch`, `numpy`,
`matplotlib`): a deterministic **synthetic** "digit-like" dataset and a from-scratch Clopper-Pearson /
normal-quantile implementation. `scipy` (exact quantiles) and `torchvision` (real MNIST) are
**optional** — imported lazily, with a numpy fallback — and listed in `requirements.txt`.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make certify                                  # synthetic data, N=1000, offline — writes figures + metrics.json
make test                                     # fast smoke tests
make certify ARGS="--n 2000 --num-points 200" # more MC samples / points (slower, tighter)
make certify ARGS="--dataset mnist"           # OPTIONAL: real MNIST (needs torchvision + download)
make certify ARGS="--sigma 0.5"               # larger noise -> larger radii, lower clean accuracy
```

Key flags: `--sigma` (noise level), `--n0`/`--n` (selection/MC samples), `--alpha` (1 - confidence),
`--num-points`, `--dataset {synthetic,mnist}`.

Outputs land in [results/](results/):
- `figures/certified_accuracy_vs_radius.png` — the **money plot**: % of points provably correct at
  each L2 radius (monotonically non-increasing — a hallmark of a sound certificate).
- `figures/radius_histogram.png` — distribution of certified radii over the test points.
- `metrics.json` — certified clean accuracy, certified accuracy at `r ∈ {0, .25, .5, .75, 1}`, mean
  radius, abstain rate (committed as evidence).

## What the result shows

The curve starts at the **certified clean accuracy** (points correctly predicted with a positive
radius) and decays as `r` grows: beyond some radius no point can be guaranteed. There is a real
**accuracy-robustness trade-off** — larger `sigma` pushes the curve rightward (bigger certified radii)
but lowers the starting accuracy and raises the abstain rate. Unlike an empirical attack-evaluation,
every point under the curve is a *theorem*: no L2 attack of that size exists, full stop.

## Interview story (3 sentences)

> I implemented randomized smoothing from scratch — Gaussian sampling, a Clopper-Pearson lower
> confidence bound, and the `R = sigma·Φ⁻¹(pA)` radius — to turn an ordinary CNN into a classifier
> with a *provable* L2 robustness certificate per input. The certified-accuracy-vs-radius curve makes
> the accuracy-robustness trade-off concrete and, unlike attack benchmarks, gives guarantees that hold
> against *any* bounded adversary rather than the one attack you happened to test. It contrasts
> directly with the empirical FGSM/PGD work elsewhere in the track: certificates over arms races.

## Layout

```
src/rand_smoothing/  utils.py (seeds) · model.py (SmallCNN) · data.py (synthetic + optional MNIST)
                     train.py (noise-augmented) · smoothing.py (SmoothedClassifier, CP bound, radius)
scripts/             train_base.py · run_certify.py
tests/               test_smoke.py  (fast statistical invariants + one @slow end-to-end)
results/             figures/*.png + metrics.json  (committed)
data/ models/        git-ignored (synthetic at runtime / MNIST downloaded / weights produced)
```

## References

- Cohen, Rosenfeld, Kolter. *Certified Adversarial Robustness via Randomized Smoothing.* ICML 2019.
  [arXiv:1902.02918](https://arxiv.org/abs/1902.02918).
- Clopper & Pearson (1934), *The use of confidence or fiducial limits...* Biometrika — the exact
  binomial interval used for the sound lower bound.
- Lecuyer et al. (2019), *Certified Robustness to Adversarial Examples with Differential Privacy* —
  earlier smoothing-style bound.
