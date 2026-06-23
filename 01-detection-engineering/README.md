# 01 · Detection Engineering (ML for security)

Your data-science strength, pointed at security telemetry. **The highest-job-probability track** —
SOC / detection-engineer / security-data-scientist roles. Mostly classical ML → CPU-friendly.

Authorized use only — see [../ETHICS.md](../ETHICS.md). Datasets are public; downloaded by code.

## Projects

| Project | Build | Status |
|---|---|---|
| `shared/ids_pipeline/` | The tabular IDS built **once** and imported by the capstone | |
| `p1-nids-baseline/` | Network intrusion detection on NSL-KDD → CICIDS2017; leak-free splits, SOC metrics | |
| `p2-malware-ember/` | Malware classification on EMBER2018 v2 with LightGBM (memmap, `num_threads<=4`) | |
| `p3-phishing-url/` | Phishing/URL detection (PhiUSIIL): lexical XGBoost vs char-CNN, generalization test | |
| `p4-dga-detection/` | DGA domain detection: char-RNN vs n-gram, leave-one-family-out eval | |
| `p5-log-ueba/` | Auth-log anomaly detection / UEBA (LANL slice + LogHub); IsolationForest/AE; precision@k | |
| `p6-threat-informed/` | ATT&CK-mapped detections + **Sigma rules** + a detection-as-code dashboard | |
| `p7-drift-monitoring/` | Concept-drift / model monitoring **as a security control** | |
| `CAPSTONE-adversarial-ids/` | Evade your OWN IDS (ART, feature-mutability constraints) → harden → re-measure | |

## Notes

- **Build the IDS once** in `shared/ids_pipeline` and import it in the capstone — don't rebuild.
- **Metrics that matter to a SOC:** precision@k, alert volume, time-to-detect — not just ROC-AUC,
  which is misleading under heavy class imbalance.
- The Sigma/detection-as-code project (`p6`) is the one that reframes "DS who touched security data"
  into "detection engineer" — prioritize its polish.
