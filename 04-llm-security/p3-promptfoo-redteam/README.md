# p3 · promptfoo red team (OWASP-LLM, eval-as-code)

Treat LLM red-teaming like a test suite: declare adversarial probes as **code**,
run them against a target, and get a pass/fail report you can diff in CI. This
project does that two ways — a real **promptfoo** `owasp:llm` config (the
industry eval-as-code tool) and a **pure-python offline harness** that runs the
same OWASP-LLM probe library against the local vulnerable RAG with zero Node,
zero network, zero API keys.

**Authorized use only.** Every probe targets a RAG app I built myself
(`../p4-vulnerable-rag`) running a deterministic offline mock LLM over fully
synthetic, planted data. See [../../ETHICS.md](../../ETHICS.md).

## The idea

[promptfoo](https://www.promptfoo.dev/) lets you express red-team evals
declaratively. Its `redteam` mode takes a **purpose** + a plugin preset
(`owasp:llm` expands to the OWASP LLM Top-10 plugins), *generates* adversarial
inputs, runs them through your target, and grades each with assertions. The
output is a structured report: attack-success-rate per category.

```
purpose + owasp:llm preset ─▶ generate probes ─▶ target.query() ─▶ grade ─▶ report
   (jailbreak, injection,        (per plugin)      (mock RAG)      (assertions)
    PII, sys-prompt leak, ...)
```

`promptfoo` is a **Node** CLI (needs `node`/`npx`), so to keep the portfolio
runnable on a bare Python box the **default path** reimplements the same loop in
~150 lines of Python:

- `src/promptfoo_redteam/probes.py` — a hand-written probe library tagged by
  OWASP-LLM category (LLM01 injection/jailbreak, LLM02 sensitive-info, LLM06
  excessive agency, LLM07 system-prompt leakage) + a benign control.
- `src/promptfoo_redteam/harness.py` — loads the **real p4 RAG** target (falls
  back to a built-in mock), runs every probe, aggregates per-category success.
- `src/promptfoo_redteam/grader.py` — the success oracle: an attack "lands" when
  the answer contains a **planted** artifact (the `HUNTER2-LAB` system-prompt
  passphrase, the `sk-LAB-FAKE…` API key, a `NNN-NN-NNNN` SSN / card number) or
  an injection marker (`PWNED`, leaked system prompt). Matching known planted
  artifacts makes the grader precise, not a fuzzy heuristic.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make redteam     # OFFLINE default: run the OWASP-LLM harness vs p4, write figures + metrics.json
make test        # fast smoke tests (-m "not slow")

# OPTIONAL eval-as-code path (needs node + npx, no API keys — target is local):
make promptfoo   # cd promptfoo && npx promptfoo@latest redteam run -o results.json
make parse       # parse promptfoo/results.json -> the same metrics.json shape + chart
```

Outputs land in [results/](results/):
- `figures/owasp_success_by_category.png` — attack-success-rate per OWASP-LLM category.
- `figures/probe_outcomes.png` — per-probe strip (red = attack landed, grey = defended, green = benign ok).
- `metrics.json` — per-category + per-probe results, committed as evidence.

## What the result shows

Against the deliberately-vulnerable p4 RAG, **9/9 attack probes land (100%)
across all four exercised OWASP-LLM categories, with 0 false positives on the
benign control**. The standout finding: the poisoned document `kb-099` (an
*indirect* injection planted in the knowledge base) is retrieved into context
for almost every query, so even a plain PII or secret request gets the model to
also dump the system prompt and append `PWNED` — one bad document contaminates
the whole app. That 100% number is the *point*: it's the un-defended baseline
that the defenses project (p7) has to drive down, and this harness is the
regression test that proves it did.

## Interview story (3 sentences)

> I built LLM red-teaming as eval-as-code: an OWASP-LLM probe library (jailbreaks,
> prompt injection, PII and system-prompt leakage) graded by a precise oracle that
> looks for *planted* secrets, runnable both through promptfoo and a Node-free
> Python harness. Run against my deliberately-vulnerable RAG it shows a 100% attack
> success baseline and surfaces that a single poisoned retrieved document
> compromises every query via indirect injection. Because it emits a structured
> per-category metrics.json, it doubles as a CI regression gate for the defenses I
> add later — red-team results you can diff, not a one-off manual probe.

## Layout

```
src/promptfoo_redteam/  utils.py (seeds) · probes.py (OWASP-LLM library) ·
                        grader.py (leak oracle) · harness.py (target + runner)
scripts/                run_redteam.py (offline) · parse_promptfoo.py (node path)
promptfoo/              promptfooconfig.yaml (owasp:llm preset) · target_provider.py · README
tests/                  test_smoke.py (fast invariants + one @slow end-to-end)
results/                figures/*.png + metrics.json  (committed)
data/ models/           git-ignored; this project needs neither (attacks p4)
```

## References

- OWASP. *Top 10 for LLM Applications (2025).*
  <https://genai.owasp.org/llm-top-10/>
- promptfoo. *LLM red teaming / eval-as-code.*
  <https://www.promptfoo.dev/docs/red-team/> ·
  <https://www.promptfoo.dev/docs/red-team/owasp-llm-top-10/>
- Greshake et al. *Not what you've signed up for: Compromising Real-World LLM-Integrated
  Applications with Indirect Prompt Injection.* 2023. [arXiv:2302.12173](https://arxiv.org/abs/2302.12173).
- Sibling target: [../p4-vulnerable-rag](../p4-vulnerable-rag) (the app under test).
