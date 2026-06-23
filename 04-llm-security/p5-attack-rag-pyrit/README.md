# p5 · Attack the RAG (prompt injection & exfiltration)

Red-team the deliberately-vulnerable RAG lab from [`../p4-vulnerable-rag`](../p4-vulnerable-rag):
craft prompt-injection and data-exfiltration attacks, and **measure attack-success-rate (ASR) per
technique** so [`../p7-defend-rag`](../p7-defend-rag) can show a quantified before/after reduction.

**Authorized use only.** Every attack targets a self-built lab app on **synthetic** data with an
offline **mock** model. No third-party or production system, no real network calls. See
[../../ETHICS.md](../../ETHICS.md).

## Techniques (→ OWASP LLM Top 10)

| Technique | Idea | OWASP |
|---|---|---|
| `direct_injection` | Attacker-controlled question carries an "ignore previous instructions" override | LLM01 |
| `indirect_injection` | A *benign* question retrieves the planted poisoned doc, which carries the override | LLM01 |
| `poisoned_document` | Attacker **uploads** a poisoned KB doc (a supply-chain-flavored injection) | LLM01 |
| `secret_exfiltration` | Coax out the planted API key, then smuggle it via a **mock** outbound channel | LLM06 |
| `pii_exfiltration` | Retrieved customer PII is echoed into the answer (no output filter), then smuggled | LLM06/LLM02 |
| `multi_turn_escalation` | Capped Crescendo/TAP-style escalation; stops on first success or `MAX_TURNS` | LLM01 |

A `benign_control` query is run too — it must **not** leak (true-negative sanity check).

## Run it

```bash
make attack     # offline: runs every attack vs the p4 mock, writes metrics + figures
make test       # fast smoke tests
```

Outputs in [results/](results/): `figures/attack_success.png` (ASR per technique),
`figures/exfiltration.png` (secrets captured), and `metrics.json`.

Against the **undefended** lab target the ASR is ~100% — that's the point. The story is the delta once
`p7-defend-rag` adds guardrails + an injection detector.

## Optional: real tooling (your own key / Ollama)

The default path is offline + deterministic. To run against a real model or with real frameworks:

```bash
cp ../p4-vulnerable-rag/.env.example ../p4-vulnerable-rag/.env   # add YOUR key
export RAG_PROVIDER=anthropic        # or openai / ollama
# Microsoft PyRIT v0.14.x for orchestrated multi-turn (TAP/Crescendo), capped by MAX_TURNS/MAX_BRANCHES
pip install pyrit-redteam==0.14.*
```

Multi-turn orchestrators make many sequential model calls — turns are **hard-capped** (`MAX_TURNS` in
`.env`) so cost can't run away. See [`../p2-garak-scan`](../p2-garak-scan) for the garak scanner.

## Interview story

> I red-teamed a RAG app I built, implementing direct + indirect prompt injection and data
> exfiltration, and measured a ~100% attack-success-rate against the undefended target with a mock
> model so it runs offline and deterministically. The harness emits ASR per OWASP-LLM category, which
> my defense project then drives down — the before/after delta is the headline. It cleanly separates
> the *target*, the *attacks*, and the *defenses* so each is reusable and the metric is honest.

## Layout

```
src/attack_rag/   target.py (loads p4) · attacks.py (the suite) · exfil.py (mock channel) · utils.py
scripts/          run_attacks.py
tests/            test_smoke.py
results/          figures/*.png + metrics.json  (committed)
```

## References

OWASP Top 10 for LLM Applications 2025 (LLM01 Prompt Injection, LLM06 Sensitive Information
Disclosure). Microsoft PyRIT (microsoft.github.io/PyRIT). NVIDIA garak (github.com/NVIDIA/garak).
