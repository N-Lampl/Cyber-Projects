# 06 · Financial Crime & Risk ML

ML pointed at **financial crime and risk** — fraud, money-laundering, market manipulation, and credit
risk. It's the same "ML for security" mindset as the detection track, applied to money: heavy class
imbalance, anomaly detection, adversaries who adapt, and metrics that actually matter to a risk team
(PR-AUC, precision@k, calibration) rather than raw accuracy.

Authorized use only — see [../ETHICS.md](../ETHICS.md). Datasets are NOT committed; they're
downloaded by code. Each project also ships an offline synthetic generator as a fallback.

## Projects — and what each runs on

Four of six run on **real public data**; the two that don't have an honest reason (below).

| Project | Real result | Data |
|---|---|---|
| `p1-fraud-detection/` | Supervised fraud — **PR-AUC 0.84, ROC-AUC 0.98**, 88% caught @1% FPR | **REAL** ULB credit-card fraud (284,807 txns) |
| `p2-transaction-anomaly/` | Unsupervised IsolationForest — **PR-AUC 0.13**, ROC-AUC 0.94 (the cost of no labels) | **REAL** ULB credit-card fraud |
| `p4-credit-risk-scoring/` | Calibrated GBM — **ROC-AUC 0.80**, Brier 0.16, +4.6% approval gap for under-25s | **REAL** UCI German Credit (1,000 borrowers) |
| `p5-market-manipulation/` | Flags the Aug-2015 crash + earnings gaps on real prices | **REAL** AAPL daily OHLCV 2015–2017 |
| `p3-aml-typologies/` | Structuring + layering detection on a transaction graph | Synthetic — *no real public labeled AML data exists; even industry uses sims (AMLSim/PaySim)* |
| `CAPSTONE-adversarial-fraud/` | Evasion ASR **100% → 0%** after adversarial training | Synthetic — *the feature-mutability attack needs interpretable features; ULB's PCA features can't express "a fraudster changes the amount." Real fraud numbers live in p1/p2* |

## Notes

- **Imbalanced metrics, not accuracy.** Fraud/AML are needle-in-haystack — report PR-AUC, precision@k,
  recall at a fixed false-positive budget, and calibration. A 99.9%-accurate fraud model is useless.
- **Adversaries adapt.** The capstone treats fraud as adversarial (a fraudster mutates amount/timing
  to slip past the model), mirroring the adversarial-IDS capstone in the detection track.
- **CPU-friendly.** Classical ML (sklearn) by default; xgboost / a small torch autoencoder / networkx
  are optional enhancements imported lazily.

## Reproduce the real-data runs

```bash
# p1 + p2 — ULB credit-card fraud (no Kaggle account needed; HuggingFace mirror)
curl -L -o p1-fraud-detection/data/creditcard.csv \
  https://huggingface.co/datasets/David-Egea/Creditcard-fraud-detection/resolve/main/creditcard.csv
python3 p1-fraud-detection/scripts/run_detection.py --real p1-fraud-detection/data/creditcard.csv
python3 p2-transaction-anomaly/scripts/run_detect.py --real p1-fraud-detection/data/creditcard.csv

# p4 — UCI German Credit
curl -o p4-credit-risk-scoring/data/german.data \
  https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.data
python3 p4-credit-risk-scoring/scripts/run_scoring.py --real-csv p4-credit-risk-scoring/data/german.data

# p5 — real AAPL OHLCV (GitHub-raw mirror; Yahoo/stooq are anti-bot in many envs)
python3 p5-market-manipulation/scripts/run_detect.py --ticker AAPL
```

Each project still falls back to its offline synthetic generator (`make run` / no flag) so tests and CI
need no network. Datasets are git-ignored, never committed.
