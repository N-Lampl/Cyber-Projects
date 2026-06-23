# p2 · Model extraction (model stealing) — from scratch

Train a victim classifier, expose it as a **black-box, label-only API**, then train a separate
**thief** model using *only the victim's query responses*. Sweep the attacker's query budget to draw
the **fidelity-vs-query-budget** curve, then turn on a **rate-limit / query-budget defense** and watch
it cap the thief. No ART, no foolbox — the attack is ~30 lines.

**Authorized use only.** The victim is a model I trained myself on synthetic (or public MNIST) data,
queried through my own in-process API. No third-party model or service is touched. See
[../../ETHICS.md](../../ETHICS.md).

## The idea

A deployed model that answers prediction queries leaks itself. If an attacker can send inputs `x` and
read back the model's predicted label `f(x)`, they can build a labelled training set
`{(x_i, f(x_i))}` and fit their own model `f'` to imitate `f` — no weights, no training data, no
architecture knowledge required (Tramèr et al., 2016). The metric that matters is not the thief's task
accuracy but its **fidelity**: how often it reproduces the *victim's* decision.

```
fidelity(f', f) = (1/N) Σ  1[ argmax f'(x_i) == argmax f(x_i) ]      over a held-out test set
```

The whole attack ([src/model_extraction/extract.py](src/model_extraction/extract.py)):

```python
pool = splits.attack_x[:budget]                 # inputs the attacker can sample
qx, qy = label_pool_with_victim(api, pool)      # query the API for HARD labels
thief = make_thief(...)                          # a DIFFERENT-sized net than the victim
train(thief, loader(qx, qy))                     # supervised fit on the victim's answers
fidelity = agreement(thief, victim, test_set)    # how often the clone matches the victim
```

The thief is deliberately given a different hidden width than the victim, to show extraction does not
need the victim's architecture — only its input/output interface.

### The defense

The victim is reached through [`VictimAPI`](src/model_extraction/victim_api.py), which (a) returns only
**hard labels** (the most information-poor response), and (b) enforces a **query budget**: once a client
has spent its quota, further requests raise `QueryBudgetExceeded` — modelling a server that
rate-limits / cuts off a client that has queried too much. Capping the budget directly caps the size of
the training set the thief can build, and therefore its fidelity.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make attack            # trains victim (if needed), runs the budget sweep + defense, writes figures + metrics.json
make test              # fast smoke tests
make train             # just train + save the victim
make attack ARGS="--dataset mnist"        # OPTIONAL: real MNIST (needs torchvision, downloads ~11 MB)
make attack ARGS="--defense-cap 2000"     # change the rate-limit cap
```

The **default path is fully offline**: it builds a synthetic image dataset with scikit-learn (no
download) and needs only `torch`, `scikit-learn`, `numpy`, `matplotlib`. The MNIST path is an optional
enhancement (`torchvision` imported lazily). CPU-only throughout; the full sweep is ~15 s on a laptop.

Outputs land in [results/](results/):
- `figures/fidelity_vs_budget.png` — the **money plot**: fidelity climbing with query budget, and the
  rate-limit line flat-lining once throttled.
- `figures/accuracy_and_fidelity.png` — thief task accuracy + fidelity vs budget, against the victim's
  accuracy.
- `metrics.json` — victim accuracy, per-budget thief accuracy/fidelity, defended vs undefended.

## What the result shows

On the default synthetic dataset (seed 42): the victim hits **~99%** test accuracy. With **no defense**,
a thief trained on **1,000** label queries already reaches **~84%** fidelity, and by **4,000** queries it
reaches **~99%** — an almost perfect functional clone built purely from the API's answers. Turn on a
**1,000-query rate limit** and the same attacker is throttled at **768** served queries, capping fidelity
at **~55%**. The takeaway: a prediction API is a model-disclosure channel, and **query budgeting /
rate-limiting is a cheap, effective first-line defense** (paired with returning hard labels rather than
full probabilities).

## Interview story (3 sentences)

> I hand-rolled a model-extraction attack: I stood up a victim classifier behind a label-only query API,
> then trained a differently-sized "thief" network on nothing but the victim's predicted labels and
> measured fidelity (agreement) rather than raw accuracy. The fidelity-vs-query-budget curve shows a near-
> perfect clone emerging after a few thousand queries, which is exactly why prediction APIs are a model-
> disclosure risk. I then implemented a query-budget rate limit on the API and showed it throttles the
> attacker and caps achievable fidelity — a concrete, low-cost defense.

## Layout

```
src/model_extraction/  utils.py (seeds) · data.py (synthetic + optional MNIST splits) ·
                       model.py (victim/thief MLPs) · train.py (train/eval/agreement) ·
                       victim_api.py (black-box API + rate-limit defense) · extract.py (the attack)
scripts/               train_victim.py · run_extraction.py
tests/                 test_smoke.py  (fast invariants + one @slow end-to-end)
results/               figures/*.png + metrics.json  (committed)
data/ models/          git-ignored (generated / downloaded at runtime)
```

## References

- Tramèr, Zhang, Juels, Reiter, Ristenpart. *Stealing Machine Learning Models via Prediction APIs.*
  USENIX Security 2016. [arXiv:1609.02943](https://arxiv.org/abs/1609.02943).
- Orekondy, Schiele, Fritz. *Knockoff Nets: Stealing Functionality of Black-Box Models.* CVPR 2019.
  [arXiv:1812.02766](https://arxiv.org/abs/1812.02766).
- Jagielski, Carlini, Berthelot, Kurakin, Papernot. *High Accuracy and High Fidelity Extraction of
  Neural Networks.* USENIX Security 2020. [arXiv:1909.01838](https://arxiv.org/abs/1909.01838).
