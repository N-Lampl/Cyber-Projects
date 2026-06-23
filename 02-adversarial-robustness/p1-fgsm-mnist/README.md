# p1 · FGSM on MNIST (from scratch)

The first project and the quick win: implement the **Fast Gradient Sign Method** by hand against a
99%-accurate MNIST classifier and watch it fall apart. ~10 lines of attack code, no attack library.

**Authorized use only.** The target is a model I trained myself on a public dataset. See
[../../ETHICS.md](../../ETHICS.md).

## The idea

A neural net is trained by following gradients to *decrease* loss. FGSM (Goodfellow, Shlens, Szegedy,
2015) flips that: nudge the **input** in the direction that *increases* loss, so the model gets it
wrong. One step, one equation:

```
x_adv = clip( x + ε · sign( ∇_x  L(f(x), y) ), 0, 1 )
```

- `∇_x L` — gradient of the loss w.r.t. the **input pixels** (not the weights).
- `sign(...)` — take only the direction per pixel ⇒ an **L∞** attack: every pixel moves by exactly ε.
- `clip(0,1)` — keep it a valid image.

The whole attack ([src/fgsm_mnist/attack.py](src/fgsm_mnist/attack.py)):

```python
x = x.clone().detach().requires_grad_(True)
loss = loss_fn(model(x), y)
model.zero_grad(set_to_none=True)
loss.backward()                       # populates x.grad
x_adv = x + epsilon * x.grad.sign()   # step along the gradient's sign
x_adv = torch.clamp(x_adv, 0.0, 1.0)  # keep it a valid image
```

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make attack            # trains the CNN if needed, runs the ε-sweep, writes figures + metrics.json
make test              # fast smoke tests
make attack ARGS=--full   # evaluate on the full 10k test set (slower)
```

Outputs land in [results/](results/):
- `figures/accuracy_vs_epsilon.png` — the **money plot**: accuracy collapsing as ε grows.
- `figures/clean_vs_adversarial.png` — same digits, tiny perturbation, flipped predictions.
- `metrics.json` — clean accuracy + accuracy at each ε (committed as evidence).

## What the result shows

Clean accuracy is ~99%. By ε≈0.2–0.3 (a perturbation that's barely visible) the model is wrong on the
large majority of images — a vivid demonstration that high test accuracy says **nothing** about
robustness. That gap is the entire reason the rest of track 02 (and the adversarial-IDS capstone in
track 01) exists.

## Interview story (3 sentences)

> I implemented FGSM from scratch to show that a 99%-accurate MNIST CNN can be driven to near-random
> accuracy by an L∞ perturbation too small to see — using the model's own input gradients. It made
> concrete *why* standard accuracy is a misleading security metric and motivated the defense work
> (adversarial training, detectors) in the rest of the repo. The same gradient idea generalizes
> straight to evading a tabular intrusion detector, which is my capstone.

## Layout

```
src/fgsm_mnist/   utils.py (seeds) · model.py (SmallCNN) · data.py · train.py · attack.py
scripts/          train_mnist.py · run_fgsm.py
tests/            test_smoke.py  (fast invariants + one @slow end-to-end)
results/          figures/*.png + metrics.json  (committed)
data/ models/     git-ignored (downloaded / produced at runtime)
```

## Reference

Goodfellow, Shlens, Szegedy. *Explaining and Harnessing Adversarial Examples.* ICLR 2015.
[arXiv:1412.6572](https://arxiv.org/abs/1412.6572). · PyTorch "Adversarial Example Generation" tutorial.
