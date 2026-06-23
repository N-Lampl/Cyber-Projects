# p1 · OWASP LLM Top 10 — threat lab & repo map

The anchor for the LLM-security track. It pins the **OWASP Top 10 for LLM Applications (2025)** as the
single source of truth and maps each risk to the repo projects that **attack** or **defend** it — so
the track has a coherent threat model and honest coverage accounting, not a pile of disconnected demos.

It also ships [`AUTHORIZATION.md`](AUTHORIZATION.md), the reusable scope template every attack project links.

**Authorized use only** — see [../../ETHICS.md](../../ETHICS.md) and [AUTHORIZATION.md](AUTHORIZATION.md).

## Run it

```bash
make map     # build results/owasp_map.json + coverage figure + metrics.json
make test    # fast smoke tests
```

Outputs: `results/owasp_map.json` (each LLM01–LLM10 → projects), `results/figures/owasp_coverage.png`,
`results/metrics.json` (coverage %).

## The map (2025)

| Risk | Addressed by |
|---|---|
| **LLM01** Prompt Injection | p4-vulnerable-rag, p5-attack-rag-pyrit, p2-garak-scan, p3-promptfoo-redteam, p7-defend-rag |
| **LLM02** Sensitive Info Disclosure | p5-attack-rag-pyrit, 03-ml-privacy/p5-llm-privacy, p7-defend-rag |
| **LLM03** Supply Chain | 05-ml-supply-chain/secure-ml-pipeline |
| **LLM04** Data & Model Poisoning | *partial* — poisoning kept as a stretch repo |
| **LLM05** Improper Output Handling | p4-vulnerable-rag, p7-defend-rag |
| **LLM06** Excessive Agency | p6-agent-tool-abuse |
| **LLM07** System Prompt Leakage | p4-vulnerable-rag, p5-attack-rag-pyrit |
| **LLM08** Vector & Embedding Weaknesses | p4-vulnerable-rag, p7-defend-rag |
| **LLM09** Misinformation | p7-defend-rag, 01-detection/p7-drift-monitoring |
| **LLM10** Unbounded Consumption | CAPSTONE-appsec-ci, 03-ml-privacy/p1-api-threat-model |

## Interview story

> I anchored the LLM-security track to the OWASP LLM Top 10 (2025) and built a coverage map tying each
> risk to a concrete attack or defense project, with an honest note on the one risk I only partially
> cover. It shows I think in threat-model terms, not just demos — and the reusable authorization
> template keeps every attack project explicitly in-scope.

## Layout

```
src/owasp_threat_lab/   mapping.py (framework + repo coverage)
scripts/                build_owasp_map.py
AUTHORIZATION.md        reusable scope template (linked by attack projects)
results/                owasp_map.json + figures/owasp_coverage.png + metrics.json
```

## Reference

OWASP Top 10 for LLM Applications 2025 — genai.owasp.org/llm-top-10.
