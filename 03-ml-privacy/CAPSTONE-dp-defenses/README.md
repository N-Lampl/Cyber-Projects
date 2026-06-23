# CAPSTONE · Differential privacy as a defense (DP-SGD vs MIA + model extraction)

The track-03 capstone. Earlier projects showed how to **attack** a model's privacy
(p3 membership inference, p2 model extraction). This one **defends** it: retrain the
same target with **DP-SGD** at several privacy budgets `ε ∈ {∞, 3, 1}`, then re-run
*both* attacks against each version with a **shared, fixed shadow set** so the only
thing that changes is the target's training procedure. The result is the textbook
**privacy-utility tradeoff** — measured end-to-end, on a CPU, with no Opacus and no
data download.

**Authorized use only.** Every model here (DP targets, shadow models, extraction
thieves) is trained by me on synthetic data I generated. The attacks are run only
against my own models. See [../../ETHICS.md](../../ETHICS.md).

## The idea

DP-SGD (Abadi et al., 2016) makes each training step differentially private by
bounding then hiding each example's influence:

```
for each minibatch B:
    g_i  = ∇θ L(x_i, y_i)                          # PER-SAMPLE gradient
    ĝ_i  = g_i / max(1, ‖g_i‖₂ / C)                # clip to L2 norm C  (bounds sensitivity)
    g~   = (1/|B|) ( Σ_i ĝ_i + N(0, (σC)² I) )     # add Gaussian noise, average
    θ    = θ − η · g~                              # ordinary SGD step on the noised grad
```

- **Clipping** to `C` caps how much any single example can move the weights
  (sensitivity), so no record dominates the update.
- **Gaussian noise** `N(0,(σC)²)` masks whether any one record was in the batch.
- Over `T` steps with Poisson sampling rate `q = B/N`, a **subsampled-Gaussian RDP
  accountant** converts `(σ, q, T)` into an `(ε, δ)` guarantee. Smaller `ε` ⇒ more
  noise / smaller useful signal ⇒ stronger privacy, lower utility.

We pick `σ` to **hit a requested ε** by bisecting the accountant (the same thing
Opacus's `make_private_with_epsilon` does), so the privacy claim is the budget we
asked for, not whatever fell out.

### Why it should defeat the attacks

Membership inference and (indirectly) extraction feed on **memorisation** — the gap
between how the model treats training vs unseen points. DP provably bounds that gap.
The shared shadow set ([src/dp_defenses/mia.py](src/dp_defenses/mia.py)) lets us
watch LiRA's per-example likelihood-ratio test go from "works" to "coin flip" as ε
shrinks, while extraction fidelity is capped by the now-noisier target.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make run               # DEFAULT: fast 2-point smoke sweep {inf, 1}  (~10s, tiny pool)
make run ARGS=--full   # flagship sweep {inf, 3, 1} -> the committed figures  (~35s)
make overnight         # finer grid {inf,8,3,1,0.5}, 16 shadows -> results/batches/<ts>/batch.json
make test              # fast smoke tests
```

Everything above runs **offline** with only `torch, scikit-learn, numpy, matplotlib`
— manual DP-SGD + synthetic data + a deterministic shadow set. No Opacus, no
downloads, no GPU.

Outputs land in [results/](results/):
- `figures/privacy_utility_tradeoff.png` — utility **and** attack success vs ε.
- `figures/mia_roc_by_epsilon.png` — LiRA ROC per ε, collapsing onto the diagonal.
- `metrics.json` — per-ε accounted ε, σ, accuracy, train-test gap, MIA AUC,
  TPR@1%FPR, extraction accuracy + fidelity (committed as evidence).

## What the result shows (committed `--full` run)

| ε    | test acc | train−test gap | MIA AUC | extraction fidelity |
|------|---------:|---------------:|--------:|--------------------:|
| ∞    | **0.638** | **0.205**     | **0.633** | 0.45 |
| 3    | 0.428    | 0.037          | 0.511   | 0.66 |
| 1    | 0.338    | 0.000          | 0.523   | 0.53 |

As ε falls from ∞ to 1, the **memorisation gap collapses 0.205 → 0.00** and **MIA
AUC drops from 0.63 toward the 0.50 chance line** — i.e. the membership-inference
attack stops working. The price is real: **test accuracy falls 0.64 → 0.34**. That
is the privacy-utility tradeoff, made concrete on one plot. (Extraction fidelity
moves non-monotonically because it tracks the *target's own* quality, which DP
degrades; the headline privacy win is the MIA collapse.)

The accountant lands the **requested** budget exactly (accounted ε = 3.000 and
1.000), with σ = 4.35 and 12.26 respectively.

## Interview story (3 sentences)

> I retrained a target model with hand-rolled DP-SGD (per-sample gradient clipping
> + calibrated Gaussian noise, with my own subsampled-Gaussian RDP accountant) at
> ε ∈ {∞, 3, 1}, then re-ran membership inference and model extraction against each
> version using one fixed shadow set. Tightening the budget to ε=1 drove the
> train-test memorisation gap to zero and pushed LiRA's AUC from 0.63 back to ~0.51
> (chance), at the cost of dropping test accuracy from 0.64 to 0.34. It is a clean,
> auditable demonstration of *why* differential privacy is the principled defense
> for the leakage attacks in the rest of this track — and what it actually costs.

## Differential privacy, briefly

A randomised mechanism `M` is `(ε, δ)`-DP if for any two datasets differing in one
record and any output set `S`: `Pr[M(D)∈S] ≤ e^ε · Pr[M(D')∈S] + δ`. Small ε ⇒ the
output barely depends on any single record ⇒ an attacker cannot tell if you were in
the training set. DP-SGD achieves this per-step (Gaussian mechanism on clipped
grads) and composes over steps via RDP.

## Layout

```
src/dp_defenses/
  utils.py        set_seed(42) + get_device()->cpu
  data.py         make_synthetic_pool (offline) · load_fashion_mnist_pool (optional)
  model.py        SmallMLP (shared target/shadow/thief) + LiRA confidence signal
  dp_train.py     manual DP-SGD + RDP accountant (+ optional Opacus path)
  mia.py          LiRA likelihood-ratio membership inference (shared shadows)
  experiment.py   build_shared_world · evaluate_epsilon (trains DP target, runs both attacks)
  scipy_stub.py   local Gaussian log-pdf (no scipy dependency)
scripts/
  run_tradeoff.py    the money target: sweep ε, write figures + metrics.json
  overnight_batch.py finer grid, timestamped batch output
tests/            test_smoke.py (fast invariants + accountant checks + one @slow E2E)
results/          figures/*.png + metrics.json  (committed)
data/ models/     git-ignored (synthetic data is in-memory; no checkpoints persisted)
```

## Optional enhanced paths

Both are documented and `try/except`-guarded so the module imports without them:

- **Opacus** (`opacus>=1.5`, [meta-pytorch/opacus](https://github.com/meta-pytorch/opacus)):
  `dp_train.train_dp_opacus` runs the *same* DP-SGD via `PrivacyEngine` to validate
  the manual loop and accountant against the reference implementation.
- **Fashion-MNIST** (`torchvision`): `data.load_fashion_mnist_pool` swaps the
  synthetic pool for real flattened images (~30 MB, downloaded on first use).

## References

- Abadi, Chu, Goodfellow, McMahan, Mironov, Talwar, Zhang. *Deep Learning with
  Differential Privacy.* CCS 2016. [arXiv:1607.00133](https://arxiv.org/abs/1607.00133).
- Mironov. *Rényi Differential Privacy.* CSF 2017. [arXiv:1702.07476](https://arxiv.org/abs/1702.07476).
- Mironov, Talwar, Zhang. *Rényi DP of the Sampled Gaussian Mechanism.* 2019.
  [arXiv:1908.10530](https://arxiv.org/abs/1908.10530).
- Carlini, Chien, Nasr, Song, Terzis, Tramèr. *Membership Inference Attacks From
  First Principles (LiRA).* IEEE S&P 2022. [arXiv:2112.03570](https://arxiv.org/abs/2112.03570).
- Opacus: [github.com/meta-pytorch/opacus](https://github.com/meta-pytorch/opacus).
