# CAPSTONE · CI-gated LLM AppSec red-team pipeline

The track-04 flagship: wire the offline red-team harnesses from the earlier
projects into a **GitHub Actions gate** that red-teams the vulnerable RAG on
every PR and **blocks the merge if attack-success rate (ASR) exceeds a
threshold** — then trends ASR per OWASP category and ships a consulting-style
threat-model + remediation report.

**Authorized use only.** Every probe targets a self-built, deliberately
vulnerable lab app over synthetic data (fake PII, fake `sk-...` keys). See
[../../ETHICS.md](../../ETHICS.md).

## The problem

LLM apps regress silently: a prompt tweak, a new retrieved doc, or a new tool can
re-open a prompt-injection or data-leak hole that a previous fix closed. Manual
red-teaming doesn't catch that. The fix is the same one AppSec already uses for
code: **a security test in CI that fails the build.** This project is that gate
for an LLM RAG app, mapped to the **OWASP LLM Top-10 (2025)**.

## The idea

```
  PR opened
     │
     ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  ci-redteam.yml  (GitHub Actions)                             │
  │                                                              │
  │   p3 promptfoo-style probes ─┐                               │
  │   p2 garak-style probes ─────┼─▶  target = p4 VulnerableRAG   │
  │                              │      │                         │
  │                              ▼      ▼                         │
  │                       normalise → ASR per OWASP category      │
  │                              │                               │
  │                              ▼                               │
  │            gate: overall ASR > threshold ?  ── yes ─▶ exit 1 │ block merge
  │                              │  no                            │
  │                              ▼                               │
  │                           exit 0                              │ allow merge
  └──────────────────────────────────────────────────────────────┘
```

- **Reuse, don't reinvent:** `src/appsec_ci/harness.py` imports the OFFLINE probe
  libraries + graders already built in `../p2-garak-scan` and
  `../p3-promptfoo-redteam`, runs them against `../p4-vulnerable-rag`, and
  normalises both into one `ProbeResult` shape keyed by OWASP category.
- **The gate** (`gate.py`): `ASR = attacks_landed / attack_probes` (benign
  controls excluded). `evaluate(results, threshold)` returns `passed`, which the
  runner turns into the process **exit code** — that is what fails the CI job.
- **Before/after:** the same harness runs against the remediated app
  (`../p7-defend-rag`, the `DefendedRAG` guardrails) to prove the fixes work. If
  p7's optional detector isn't installed, a deterministic *simulated* hardened
  target stands in so the comparison always runs.
- **Offline-first everywhere:** numpy + matplotlib only. No Node, no network, no
  API keys, no model downloads. If a sibling project is missing, a built-in
  fallback keeps the gate running.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make run               # full pipeline -> figures + threat_model_report.md + metrics.json
make gate              # the CI gate vs the VULNERABLE RAG -> exits 1 (FAIL), by design
make gate-remediated   # the same gate vs the HARDENED RAG  -> exits 0 (PASS)
make test              # fast smoke tests (gate invariants)
```

Outputs land in [results/](results/):
- `figures/asr_by_category.png` — the money plot: **ASR per OWASP category,
  vulnerable (100%) vs remediated (0%)**.
- `figures/asr_trend.png` — ASR per category **trending down** across a 5-run fix
  rollout (the dashboard view).
- `threat_model_report.md` — the consulting deliverable (STRIDE threats,
  findings table, prioritised remediations, residual risk), generated from the
  live gate numbers.
- `metrics.json` — gate verdict + per-OWASP ASR (committed as evidence).

The CI workflow itself is [`ci-redteam.yml`](ci-redteam.yml) (also under
`.github/workflows/`): a **PR/push gate job** (fast smoke, blocking) plus a
**scheduled nightly full-suite job** (p2 garak + p3 promptfoo, trends ASR). To
enable repo-wide, copy it to the repository-root `.github/workflows/`.

## What the result shows

Against the vulnerable RAG the gate reports **overall ASR 100%** — every OWASP
category (LLM01 injection, LLM02 info-disclosure, LLM06 excessive-agency, LLM07
system-prompt-leak) is fully exploited — so the build **fails (exit 1)** and the
merge is blocked. Pointed at the remediated app the same gate reports **ASR 0%
with 0 false positives** and **passes (exit 0)**. That delta is the whole value
proposition: the gate would have caught the vulnerable app before it shipped, and
proves the fixes closed every category.

## Interview story (3 sentences)

> I built the capstone that turns ad-hoc LLM red-teaming into a CI control: a
> GitHub Actions gate that reuses my garak- and promptfoo-style offline harnesses
> to attack a vulnerable RAG, computes attack-success rate per OWASP LLM
> category, and fails the build (exit 1) when ASR exceeds a threshold. On the
> vulnerable app it blocks the merge at 100% ASR; on the remediated app the same
> gate passes at 0% ASR with no false positives, and it auto-generates a
> trend dashboard plus a consulting threat-model/remediation report. It's the
> piece that makes every other project in the track a *continuous* assurance
> control instead of a one-off test.

## Layout

```
src/appsec_ci/   utils.py (seeds) · harness.py (reuse p2/p3 vs p4/p7) ·
                 gate.py (ASR + PASS/FAIL) · dashboard.py (figures + trend) ·
                 report.py (markdown threat model)
scripts/         run_pipeline.py  (gate + figures + report + metrics.json)
tests/           test_smoke.py    (gate invariants + one @slow end-to-end)
configs/         gate_policy.yaml  (per-OWASP thresholds)
.github/workflows/ci-redteam.yml  (the CI gate; copy committed at project root too)
results/         figures/*.png + metrics.json + threat_model_report.md  (committed)
data/ models/    nothing to download (synthetic corpus + mock provider)
```

## References

- OWASP Top 10 for LLM Applications (2025). <https://genai.owasp.org/>
- NVIDIA garak — LLM vulnerability scanner. <https://github.com/NVIDIA/garak>
- promptfoo `redteam` (owasp:llm preset). <https://www.promptfoo.dev/docs/red-team/>
- MITRE ATLAS — adversarial ML threat matrix. <https://atlas.mitre.org/>
- NIST AI 600-1 — Generative AI Profile (AI RMF).
