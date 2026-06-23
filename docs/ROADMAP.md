# Roadmap

A ~30-week, phase-by-phase build order. Lead with the data-science strength (detection), build to the
attack-and-defend flagships, finish the most market-aligned work (LLM security) to highest polish.

| Phase | Weeks | Focus | Milestone |
|---|---|---|---|
| **0 — Foundations & scaffolding** | 1–4 (then ongoing) | Stand up the monorepo. Build the ONE canonical ATT&CK/ATLAS Navigator layer + authorization template every track reuses. Start Security+ SY0-701. | Repo public, coherent README, green CI, shared Navigator layer. Security+ study underway. |
| **1 — Detection engineering** | 4–9 | Lead with classical ML on security telemetry. Build the tabular IDS ONCE in `01-.../shared/ids_pipeline` and reuse it. Web-appsec + crypto modules in parallel evenings. | 4–5 polished detection repos with SOC metrics; the Sigma/detection-as-code project reframes you as a *detection engineer*. |
| **2 — Adversarial robustness + capstone** | 9–15 | Quick win first (FGSM-from-scratch done, then pretrained-Foolbox demo), building to the flagship: evade your OWN IDS under feature-mutability constraints → harden → re-measure. | Attack-and-defend-your-own-IDS flagship with a before/after robustness report card; one certified-defense depth piece. |
| **3 — LLM security** | 15–22 | API-first (cheap model), Ollama fallback. Build the vulnerable RAG target BEFORE attacking it. Add agent/tool-abuse + injection→tool-call→exfiltration. Land defend-the-RAG + CI-gated AppSec capstone. | End-to-end LLM AppSec story: threat-model → scan → build target → attack → defend (quantified ASR drop) → CI gate + dashboard + threat report. |
| **4 — Supply-chain + privacy** | 22–30 | Promote the supply-chain capstone (high MLSecOps hireability). Then privacy as depth; CPU-heavy LiRA/DP-SGD last as overnight batch. | Supply-chain capstone is a headline artifact; privacy rounds out depth. Security+ exam sat. |

## Final deliverable — showcase dashboard (build LAST)

After the projects exist, build an **interactive portfolio dashboard** as a **React/Vite SPA**,
deployed free on **GitHub Pages**. It should auto-discover each project (status from the track
READMEs, results from each `results/metrics.json` + `results/figures/*.png`) so it renders the
money plots and key metrics per project and maps them to MITRE ATLAS / OWASP LLM Top 10. This is
the capstone showcase / "click this link" interview artifact — intentionally built at the end, not now.

## Scope discipline (deliberately deferred)

- **No standalone foundations or poisoning track.** Foundations is consolidated in `00-foundations`;
  poisoning overlaps detection + RAG and its best pieces are CPU-heavy. Keep **BadNets + Neural-Cleanse
  (MNIST 10-class)** as an *optional stretch repo* if you finish early.
- **Depth-flex:** do **one** of certified randomized smoothing *or* full DP-SGD-across-budgets well.
- **CPU caps:** RobustBench eval = APGD-CE on ~50–100 images (cite leaderboard for full AutoAttack);
  LiRA reports TPR@1%FPR + AUC (not 0.1%); DP capstone = 2–3 ε points, shared shadow set, overnight batch.

## Pinned tooling (verified June 2026)

`adversarial-robustness-toolbox==1.20.1` · `torchattacks==3.5.1` · `foolbox` v3 · RobustBench from master ·
garak v0.15.x · PyRIT v0.14.x · promptfoo (MIT) · NeMo-Guardrails (`github.com/NVIDIA-NeMo/Guardrails`) ·
Opacus (`meta-pytorch/opacus`) · safetensors · `protectai/modelscan` · Sigstore Cosign.

## Dataset mirrors (official links flake — use these)

NSL-KDD + CICIDS2017 → dhoogla cleaned Kaggle CSVs · EMBER2018 v2 → dhoogla parquet (numpy memmap,
`num_threads<=4`) · PhiUSIIL → UCI #967 via `ucimlrepo` · LANL + LogHub (`logpai/loghub`) → stream-filter
to a labeled few-day slice; report precision@k, not ROC-AUC.

## Key resources

OWASP LLM Top 10 2025 · MITRE ATLAS + ATT&CK Navigator · ART 1.20.1 docs · garak/PyRIT/promptfoo ·
Security+ SY0-701 (Professor Messer; refreshed objectives live 2026-07-01) · TryHackMe Pre-Security/SOC-1.
Papers: Goodfellow 2015 FGSM (1412.6572), Madry 2018 PGD (1706.06083), Carlini 2022 LiRA (2112.03570),
Cohen 2019 smoothing (1902.02918), Abadi 2016 DP-SGD (1607.00133), Arditi 2024 refusal direction (2406.11717).
