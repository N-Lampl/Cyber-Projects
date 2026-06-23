# 03 · ML Privacy (extraction, inference & defenses)

Stealing models and recovering training data — and defending with differential privacy. Research-depth
signal for AI-security / trust-&-safety roles. **CPU-heaviest track → sequenced last; run heavy bits as
overnight batch.**

Authorized use only — see [../ETHICS.md](../ETHICS.md). Attacks target models you trained.

## Projects

| Project | Build | Status |
|---|---|---|
| `p1-api-threat-model/` | FastAPI model service with **real** authN/Z + rate-limit + audit-log; links 00-foundations | |
| `p2-model-extraction/` | Steal a model via queries (ART CopycatCNN/KnockoffNets); fidelity-vs-query curve; rate-limit defense | |
| `p3-membership-inference/` | Shokri + **LiRA** (online, warm-started shadows); report **TPR@1%FPR + AUC** | |
| `p4-inversion-attribute/` | Model inversion (ART MIFace) + attribute inference on UCI Adult | |
| `p5-llm-privacy/` | Canary insertion + perplexity MIA; API-first, tiny-GPT2/Ollama fallback | |
| `CAPSTONE-dp-defenses/` | Opacus **DP-SGD** at ε ∈ {∞, 3, 1}; shared shadow set; overnight batch script | |

## Notes

- LiRA at this scale measures **methodology / curve shape**, not paper-matching low-FPR numbers — be
  honest about that. Cross-check with Privacy Meter's built-in LiRA.
- DP capstone: 2–3 ε points, a **shared** shadow set across defended/undefended targets, extraction as
  the cheap primary attack. Not an interactive notebook — a batch script.
- Use small targets (MNIST/Fashion-MNIST CNN, or logistic/MLP on UCI Adult) to keep CPU time sane.
