# p8 · Refusal direction (mechanistic interp of "abliteration")

Refusal in aligned LLMs is, empirically, mediated by **a single linear direction** in the residual
stream (Arditi et al., 2024). This project reproduces the *methodology* — extract that direction,
ablate it at inference time, and measure what happens to refusals vs capability — as **safety /
interpretability research**, entirely on CPU, with **no model weights downloaded** by default.

> **Authorized use only — analysis, not a jailbreak release.** The committed artifact is an
> *analysis* (a direction vector, metrics, figures). This project **never** writes out or
> redistributes a modified ("abliterated") model. The default path runs against a **synthetic**
> self-built model; the optional real-model path runs only against an open-weight model **you** load
> yourself. Understanding *how* a safety behaviour is encoded is what lets you make it more robust.
> See [../../ETHICS.md](../../ETHICS.md).

## The idea

Treat the last-token residual activation `h ∈ ℝ^d` as the model's "state of mind" before it answers.
Across many prompts, the difference between *will-refuse* and *will-answer* states concentrates on one
axis. Three steps:

**1. Extract** — difference-in-means refusal direction:
```
r = mean(h | harmful)  −  mean(h | harmless)        r̂ = r / ‖r‖
```

**2. Ablate** — remove that axis from every activation (orthogonal projection), applied live via a
forward hook on the residual stream ("abliteration"):
```
h' = h − (h · r̂) r̂
```

**3. Measure** — refusal rate before vs after, **plus a capability-retention proxy**, to show the
intervention is *surgical*: refusals collapse while general capability is largely preserved.

The whole method is ~15 lines ([src/refusal_interp/direction.py](src/refusal_interp/direction.py)):
```python
r = h_harmful.mean(0) - h_harmless.mean(0)        # extract
r_hat = r / r.norm()
h_ablated = h - (h @ r_hat).unsqueeze(-1) * r_hat # ablate (orthogonal projection)
```

### Why a synthetic model is a *fair* default

Downloading + running an instruct model to harvest activations is GPU-preferred and >50 MB, so the
default path simulates it. [src/refusal_interp/synthetic.py](src/refusal_interp/synthetic.py) builds a
frozen toy model whose residual stream contains a **planted** refusal axis `r_true` (orthogonal to a
separate "content/capability" subspace) plus noise. The experiment is honest, not circular:
- difference-in-means must **recover** `r_true` from data alone — we report `|cos(r̂, r_true)|`;
- a frozen behaviour head computes `P(refuse)` (keyed on the refusal axis) and `P(capable)` (keyed on
  the orthogonal content subspace), so we can show ablation is surgical rather than asserting it.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make abliterate   # REAL: abliterate Qwen2.5-0.5B-Instruct on CPU (downloads ~1GB the first time)
make run          # offline synthetic extract -> ablate -> measure (no download; for CI/quick demo)
make test         # fast smoke tests
```

The **committed `results/` come from `make abliterate`** (the real run). `make abliterate` needs the
optional extras: `pip install transformers accelerate`.

Outputs in [results/](results/):
- `figures/refusal_vs_capability.png` — the **money plot**: harmful-prompt refusal collapses, benign
  behaviour + perplexity barely move.
- `figures/projection_histograms.png` — harmful vs harmless activations on the recovered axis.
- `metrics.json` — refusal/capability before & after; `refusal_direction.json` — the extracted vector.

## Real-model result (verified on CPU)

`make abliterate` ([scripts/run_real_abliteration.py](scripts/run_real_abliteration.py)) ran the full
pipeline on **`Qwen/Qwen2.5-0.5B-Instruct`** (24 layers, direction at layer 14), CPU-only:

| metric | before | after |
|---|---|---|
| refusal on harmful prompts | **100%** | **0%** |
| refusal on harmless prompts | 0% | 0% |
| benign perplexity | 11.6 | 13.3 |

Ablating **one** direction removed every refusal on held-out cyber-harmful prompts while leaving normal
behaviour intact and capability **~87% retained** (perplexity rose modestly). The harmful/harmless
activations separate cleanly on that single axis (mean projection 5.2 vs 0.6).

Responsible-execution details: cyber-themed stimuli; we generate only a short prefix and classify
*refuse vs comply* — the model's completions for harmful prompts are **never stored or printed**; no
modified weights are written. Larger models (`--model Qwen/Qwen2.5-1.5B-Instruct`) work too but are
slower on CPU; a GPU (free Colab/Kaggle) handles 1–3B comfortably.

### Why the synthetic path also exists

`make run` ([synthetic.py](src/refusal_interp/synthetic.py)) plants a **known** refusal axis `r_true`
in a toy model's residual stream, so difference-in-means must *recover* it from data alone
(`|cos(r̂, r_true)| ≈ 1.0`). It validates the extractor against ground truth and runs offline in CI
with zero downloads. (Running `make run` overwrites `results/` with the synthetic numbers; re-run
`make abliterate` to restore the real ones.)

## What the result shows

Refusal in an aligned model concentrates on a single linear feature: project it out and refusals
vanish while general capability is largely preserved. The security takeaway — **safety alignment that
lives in one direction is brittle to weight/activation edits** — is the core argument for caution
around open-weight release and for building guardrails that don't depend on a single fragile feature.

## Interview story (3 sentences)

> I reproduced the "refusal is a single direction" result as interpretability research: extract the
> axis by difference-in-means over harmful vs harmless residual activations, ablate it with a forward
> hook, and measure that refusals collapse while a capability proxy is retained. I built it on a
> synthetic model with a *planted* direction so the whole extract→ablate→measure pipeline runs offline
> on CPU and I can verify the extractor actually recovers the ground-truth axis. The point is
> defensive — if a safety behaviour is one rank-1 feature, it's fragile, which tells you where to
> harden alignment.

## Layout

```
src/refusal_interp/  direction.py (extract/ablate/measure + hook, model-agnostic)
                     real_model.py (load model + capture residuals) · eval.py (generate + refusal classifier)
                     prompts.py (harmful/harmless sets) · synthetic.py (toy model + planted axis) · utils.py
scripts/             run_real_abliteration.py (REAL run -> committed results) · run_analysis.py (synthetic)
tests/               test_smoke.py    (fast invariants + one @slow end-to-end)
results/             figures/*.png + metrics.json + refusal_direction.json  (committed; from the real run)
data/ models/        git-ignored (model weights downloaded to HF cache, never committed)
```

## References

- Arditi, Obeso, Syed, Paleka, Panickssery, Gurnee, Nanda. *Refusal in Language Models Is Mediated by
  a Single Direction.* NeurIPS 2024. [arXiv:2406.11717](https://arxiv.org/abs/2406.11717).
- Zou et al. *Universal and Transferable Adversarial Attacks on Aligned Language Models* (AdvBench),
  2023. [arXiv:2307.15043](https://arxiv.org/abs/2307.15043).
- Taori et al. *Stanford Alpaca: An Instruction-following LLaMA model*, 2023.
- nostalgebraist, *interpreting GPT: the logit lens*, 2020 (residual-stream readout intuition).
