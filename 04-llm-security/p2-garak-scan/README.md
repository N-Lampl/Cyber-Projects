# p2 · garak-style LLM scan (offline by default, real garak optional)

[garak](https://github.com/NVIDIA/garak) (NVIDIA) is *nmap for LLMs*: it fires a
battery of **probes** at a model, captures the generations, runs **detectors** that
score each one, and writes a `report.jsonl`. This project gives you (1) a tiny
**offline** garak-style scanner that runs with zero API keys against the
[`../p4-vulnerable-rag`](../p4-vulnerable-rag) mock target, and (2) a **parser**
that turns *any* garak-shaped `report.jsonl` — ours **or** a real garak run — into
bootstrap-CI **attack-success rates** plus a bar chart.

**Authorized use only.** The default target is a deliberately-vulnerable model
I built myself; real-garak runs must point at **your own** local model / keys. See
[../../ETHICS.md](../../ETHICS.md).

## The idea

A red-team scan is just three contracts repeated over a probe battery:

```
probe  ──prompts──▶  target LLM  ──generation──▶  detector  ──▶  score ∈ {0,1}
```

- **probe** — a prompt generator for one attack class (prompt injection, secret
  leakage, PII replay, refusal bypass…).
- **detector** — a rule/classifier that decides if the generation is a *hit*
  (attack succeeded, score ≥ 0.5) — garak's convention.
- **report.jsonl** — one JSON object per *attempt* (`probe × prompt × generation`).

We summarise per probe with the **attack-success rate** and a **percentile
bootstrap 95% CI** over the per-attempt scores (resample attempts with
replacement *B*=2000×):

```
ASR(probe) = hits / attempts
CI          = [ q_2.5 , q_97.5 ]  of  mean(resample(scores))
```

Both paths emit the **same** `report.jsonl` fields, so one parser
([`src/garak_scan/report.py`](src/garak_scan/report.py)) handles both.

The built-in probe set maps 1:1 to garak's taxonomy:

| built-in probe                   | garak family   | targets (p4 weakness)        |
|----------------------------------|----------------|------------------------------|
| `promptinject.HijackPwned`       | promptinject   | indirect injection (canary)  |
| `promptinject.SystemPromptLeak`  | promptinject   | leaky system prompt          |
| `leakreplay.SecretKey`           | leakreplay     | planted API key              |
| `leakreplay.PII`                 | leakreplay     | customer SSN / PII           |
| `mitigation.MitigationBypass`    | mitigation     | model never refuses          |

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make scan      # offline built-in probes vs the p4 RAG mock -> report.jsonl, figures, metrics.json
make test      # fast smoke tests
make clean     # remove generated artefacts
```

Outputs land in [results/](results/):
- `figures/asr_by_probe.png` — **money plot**: per-probe ASR with bootstrap-CI error bars.
- `figures/asr_by_category.png` — ASR aggregated by garak category.
- `report.jsonl` — the garak-compatible scan log.
- `metrics.json` — overall + per-probe ASR/CIs (committed as evidence).

### Optional: a REAL garak scan (your own model)

The point of the offline path is to develop and demo the *parser* with no
dependencies. To run the real thing against **your own** target:

```bash
pip install "garak>=0.15,<0.16"

# Local model via Ollama (no API key, fully local):
ollama pull llama3.2
garak --model_type ollama --model_name llama3.2 \
      --probes promptinject,leakreplay,mitigation

# …or an API model with YOUR OWN key (authorized use only):
export OPENAI_API_KEY=sk-...your-own-key...
garak --model_type openai --model_name gpt-4o-mini \
      --probes promptinject

# garak prints the path to its report.jsonl; feed it to the SAME parser:
make parse REPORT=~/.local/share/garak/garak_runs/garak.<id>.report.jsonl
```

The probe names in [`configs/probe_allowlist.yaml`](configs/probe_allowlist.yaml)
match garak's, so the allowlist transfers to the `--probes` flag directly.

## What the result shows

Against the deliberately-vulnerable p4 mock the scan lands on **every** probe —
overall ASR ≈ 100% with the CI pinned at the top — because that target has no
input/output guardrails (this is the *before* picture that p7's defenses fix). On
a hardened or commercial model you would expect most probes near 0% with wide CIs
on the few prompts that occasionally slip through; the same chart makes that gap
obvious at a glance.

## Interview story (3 sentences)

> I built an offline garak-style LLM red-team scanner — probes, detectors, and a
> garak-compatible `report.jsonl` — so the whole pipeline (and its bootstrap-CI
> attack-success-rate parser) runs with no API keys against a vulnerable RAG mock.
> The parser is deliberately format-compatible with real NVIDIA garak, so the
> exact same code summarises a live scan of my own Ollama model. It turns a pile
> of raw generations into a defensible, uncertainty-aware ASR scorecard — the kind
> of artefact you'd actually hand to an LLM-security review.

## Layout

```
src/garak_scan/   utils.py (seeds) · probes.py (probes+detectors) · target.py (p4 mock / fallback)
                  scanner.py (run -> report.jsonl) · report.py (parse -> ASR + bootstrap CI)
scripts/          run_scan.py  (scan OR --report parse -> figures + metrics.json)
configs/          probe_allowlist.yaml
tests/            test_smoke.py  (fast invariants + one @slow end-to-end)
results/          report.jsonl · figures/*.png · metrics.json  (committed)
data/ models/     no datasets/weights needed (see their READMEs)
```

## References

- NVIDIA garak — *LLM vulnerability scanner.* <https://github.com/NVIDIA/garak> ·
  docs <https://docs.garak.ai>. Derczynski et al., *garak: A Framework for Security
  Probing Large Language Models*, 2024 ([arXiv:2406.11036](https://arxiv.org/abs/2406.11036)).
- Efron & Tibshirani, *An Introduction to the Bootstrap*, 1993 (percentile CI).
- OWASP Top 10 for LLM Applications (LLM01 Prompt Injection, LLM06 Sensitive
  Information Disclosure).
