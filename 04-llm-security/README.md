# 04 · LLM Security

The most market-aligned track ("GenAI red team / AI application security"). Build to the **highest
polish**. API path is first-class (you have a key); Ollama small-models are the zero-cost CPU fallback.

Authorized use only — see [../ETHICS.md](../ETHICS.md). Targets are apps you build (`p4`) and
endpoints on your own API key. **Build the vulnerable target before attacking it.**

## Projects

| Project | Build | Status |
|---|---|---|
| `p1-owasp-threat-lab/` | OWASP LLM Top 10 (2025) map + reusable `AUTHORIZATION.md` template | |
| `p2-garak-scan/` | `garak` v0.15.x scan; API vs Ollama; bootstrap-CI ASR charts | |
| `p3-promptfoo-redteam/` | promptfoo `owasp:llm` preset; eval-as-code | |
| `p4-vulnerable-rag/` | **Build the authorized target first:** a RAG app with planted PII, a leaky prompt, a mock tool | |
| `p5-attack-rag-pyrit/` | PyRIT v0.14.x: indirect injection, exfil-to-outbound-channel; capped Crescendo/TAP | |
| `p6-agent-tool-abuse/` | Small agent-with-tools + confused-deputy / tool-abuse (the 2026 frontier) | |
| `p7-defend-rag/` | NeMo-Guardrails + a **from-scratch ML prompt-injection detector**; before/after ASR | |
| `CAPSTONE-appsec-ci/` | CI-gated red-team (smoke-on-push, full-on-schedule) + dashboard + threat report | |
| `p8-refusal-direction-interp/` | Mechanistic interp of refusal ("abliteration") + alignment-robustness analysis | |

## Notes

- **Cost control:** default to a cheap API model for multi-turn attacks; hard-cap TAP/Crescendo turns
  & branching (`MAX_TURNS`, `MAX_BRANCHES` in `.env`); publish a per-run token estimate.
- **CI capstone:** fast smoke suite on push (probe allowlist + generation cap), full suite on schedule.
  This is the single best "walk-me-through-it" interview artifact.
- **`p8` is interpretability, not uncensoring** — the committed artifact is the analysis + safety-robustness
  writeup on a small open-weight model, **never a redistributed modified model**. See [../ETHICS.md](../ETHICS.md).
  This one is GPU-preferred (white-box): use smallest models on CPU or a free Colab/Kaggle T4 for the heavy pass.
