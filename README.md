# ml-security-portfolio

> A data scientist's pivot into ML security: a CPU-only monorepo that **attacks _and_ defends** real
> ML systems — detection engineering, adversarial evasion, model privacy, LLM red-teaming, and ML
> supply-chain security — every project self-contained, reproducible, and grounded in
> **MITRE ATLAS / ATT&CK** and the **OWASP LLM Top 10**.

**Authorized use only.** Every technique here runs against models, data, and apps I own or am
licensed to test. See **[ETHICS.md](ETHICS.md)**.

**Interactive results dashboard** (React/Vite) in [`dashboard/`](dashboard/) — headline
before/after results, every project's metrics + figures, and a build-on-this roadmap. Deploys to
GitHub Pages (`npm install && npm run dev` to run locally).

---

## Why this repo exists

I'm a data scientist moving into a security-focused role. ML is my strength; this portfolio builds
the security half — the attacker mindset, the frameworks, and the defensive engineering — by
*doing*. Each project ships a strong README, a reproducible run (`make attack`), a committed
"money plot" + `metrics.json`, and a short interview story. Everything is built to run on a
**CPU-only laptop** (small models, pretrained targets, classical ML, data subsets, and API/small-Ollama
for LLMs).

## Project index

**44 projects across 7 tracks — all built, every one passing its fast test suite.** Each runs
**offline & deterministically** out of the box (synthetic data / mock LLM fallbacks); real datasets,
LLM API keys, or a GPU *enhance* specific projects but are never required to see them work.

Legend: built & tested · flagship = interview pieces

| Track | Projects | What it demonstrates | Maps to | Status |
|---|---|---|---|---|
| **00 foundations** | attack-atlas, stride-ml, network-labs, web-appsec, crypto-lab, certpath | Security vocabulary, threat modeling, the frameworks every track references | ATT&CK · ATLAS | done |
| **01 detection** | ids_pipeline, nids-baseline, malware-ember, phishing-url, dga, log-ueba, threat-informed, drift | ML on security telemetry; detection-as-code (Sigma) | ATT&CK | done |
| **01 detection** | CAPSTONE-adversarial-ids | Evade my **own** IDS under feature-mutability constraints → harden → re-measure | ATLAS AML.T0015 | done |
| **02 adversarial** | p1-fgsm-mnist, attack-zoo, pretrained-foolbox, transfer-blackbox, adv-input-detector, adv-training, randomized-smoothing | FGSM/PGD/C&W/DeepFool, black-box, defenses, certified robustness | ATLAS AML.T0043 | done |
| **03 privacy** | api-threat-model, model-extraction, membership-inference (LiRA), inversion, llm-privacy, DP-defenses | Stealing models & training data; differential privacy | ATLAS AML.T0024/T0048 | done |
| **04 llm-security** | owasp-lab, garak-scan, promptfoo, vulnerable-rag, attack-rag-pyrit, agent-tool-abuse, p8-refusal-interp | Prompt injection, jailbreaks, RAG/agent attacks, alignment-robustness interp | OWASP LLM Top 10 | done |
| **04 llm-security** | p7-defend-rag, CAPSTONE-appsec-ci | Guardrails + ML injection detector; CI-gated red-team with ASR thresholds | OWASP LLM01/02 | done |
| **05 supply-chain** | secure-ml-pipeline | pickle-RCE PoC → safetensors → ModelScan → Sigstore signing → CI gate | ATLAS AML.T0010 | done |
| **06 financial** | fraud-detection, transaction-anomaly, aml-typologies, credit-risk-scoring, market-manipulation | Financial-crime & risk ML: imbalanced fraud, anomaly detection, AML graphs, calibration | fraud · AML · risk | done |
| **06 financial** | CAPSTONE-adversarial-fraud | Evade my **own** fraud model under feature-mutability constraints → harden → re-measure | ATLAS AML.T0015 | done |

The full rationale, 30-week learning roadmap, and scope decisions live in
[`docs/ROADMAP.md`](docs/ROADMAP.md). The interactive showcase **dashboard** (React/Vite) is the planned
final deliverable.

## Quickstart

```bash
# 1) (recommended) install uv — https://docs.astral.sh/uv/  — or just use system python3
make setup                      # ruff + pytest + pre-commit

# 2) run the seed project end-to-end (CPU, a couple of minutes)
cd 02-adversarial-robustness/p1-fgsm-mnist
make attack                     # trains a small MNIST CNN, runs FGSM, writes results/figures + metrics.json
```

Every project follows the **same skeleton** (`src/`, `scripts/`, `tests/`, `results/figures/`,
git-ignored `data/` + `models/`), so once you've read one you can read them all.

## Repo layout

```
00-foundations/        # security fundamentals as artifacts; every track links back here
01-detection-engineering/
02-adversarial-robustness/
03-ml-privacy/
04-llm-security/
05-ml-supply-chain/
docs/                  # ROADMAP.md, shared ATLAS/ATT&CK navigator layers, top-level plots
```

## Conventions

- **Reproducible:** every project pins deps and seeds RNGs (`set_seed(42)`); `make attack` regenerates
  the committed figure + `metrics.json`.
- **No data/weights in git:** datasets and model weights are downloaded by code (`src/data.py`,
  SHA-256 verified) and git-ignored. Only small figures + `metrics.json` are committed as evidence.
- **CI never trains:** GitHub Actions runs lint + fast smoke tests; heavy work is `@pytest.mark.slow`.
- **Ethics first:** see [ETHICS.md](ETHICS.md) and [SECURITY.md](SECURITY.md).

## License

Code: [MIT](LICENSE). Datasets and pretrained weights retain their own licenses (see each
`data/README.md`).
