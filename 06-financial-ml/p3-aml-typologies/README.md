# p3 · AML typology detection on a transaction graph

Money laundering doesn't look like one weird payment — it looks like a *pattern of
relationships* between accounts. This project builds a synthetic transaction **graph**
with two classic laundering **typologies** planted into it, engineers graph features
per account, and detects the suspicious accounts with both an unsupervised baseline
and a rules + RandomForest hybrid — scored with the metrics an AML team actually uses
(PR-AUC, precision@k, recall at a fixed false-positive budget), not accuracy.

**Authorized use only.** All data is synthetic and the models are my own. See
[../../ETHICS.md](../../ETHICS.md).

## The idea

Accounts are **nodes**; transfers are directed, timestamped, valued **edges**. On a
background of benign payments we plant:

- **STRUCTURING / smurfing** — a *funnel* account receives many deposits each kept
  just **under a reporting threshold** (here $10,000, like a US CTR) from a fleet of
  mule accounts, then forwards the aggregate. Signature: high fan-in + many
  sub-threshold deposits.
- **LAYERING** — funds move rapidly through a **chain** of intermediaries (half of
  them closing into a **cycle**), each hop passing through ~90–98% of what it
  received. Signature: pass-through ratio ≈ 1 on large amounts + cycle participation.

We compute per-account features — in/out degree, fan-in/fan-out, rapid pass-through
ratio, **cycle participation**, sub-threshold-deposit count, in/out balance — then
rank accounts by suspicion. Cycle detection uses **networkx** if installed and a
pure-python Tarjan SCC fallback if not (the project imports and runs either way).

Imbalance is handled honestly: the positive class is ~17% and rare in reality, so the
RandomForest is `class_weight="balanced"` and its probability is produced
**out-of-fold** (`cross_val_predict`, 5-fold) so the reported score isn't inflated by
scoring the rows it trained on.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make detect            # generate the graph, run both detectors, write figures + metrics.json
make test              # fast smoke tests (-m "not slow")
make detect ARGS="--fpr-budget 0.05"   # loosen the analyst alert budget
```

Outputs land in [results/](results/):
- `figures/pr_curves.png` — the **money plot**: precision-recall for both detectors
  vs. the prevalence baseline (PR-AUC is the headline rare-class metric).
- `figures/feature_importances.png` — which graph features flag a laundering account.
- `figures/laundering_ring.png` — a detected **layering ring** drawn as a graph
  (or an adjacency heatmap if networkx is absent).
- `metrics.json` — full scorecard (committed as evidence).

## What the result shows

On the default synthetic graph (1,500 accounts, ~9,300 transfers, 261 suspicious
accounts in 5 layering rings + 12 structuring funnels):

| detector | PR-AUC | ROC-AUC | recall @ 1% FPR | precision@100 |
|---|---|---|---|---|
| **rules + RandomForest** (out-of-fold) | **0.94** | **0.99** | **0.59** | **0.95** |
| IsolationForest (unsupervised) | 0.53 | 0.82 | 0.17 | 0.69 |

The supervised hybrid recovers nearly all laundering accounts with very few false
alerts: at an analyst budget of **1% false positives** it still catches **~59%** of
launderers, and **95 of its top 100 alerts are real**. The unsupervised baseline is
the realistic "no labels yet" floor — useful but far weaker — which is exactly why
typology-aware features + supervision matter. The dominant features are the planted
signatures: sub-threshold-deposit count, fan-in, and pass-through/cycle flags.

## Interview story (3 sentences)

> I modeled money laundering as a graph problem: I planted structuring and layering
> typologies into a synthetic transaction graph, engineered per-account graph features
> (fan-in, rapid pass-through, cycle participation, sub-threshold-deposit counts), and
> ranked accounts with a class-weighted RandomForest scored **out-of-fold** so the
> numbers are honest. I reported it the way an AML team would — PR-AUC, precision@k,
> and recall at a fixed false-positive budget — getting 0.94 PR-AUC and ~59% of
> launderers caught at a 1% alert budget, versus a 0.53-PR-AUC unsupervised baseline.
> The cycle detection degrades gracefully from networkx to a pure-python SCC fallback,
> so the tool runs anywhere.

## Layout

```
src/aml_typologies/  utils.py (seeds) · graph.py (synthetic typologies) ·
                     features.py (graph features + cycle detection) · detect.py (detectors + metrics)
scripts/             detect_aml.py  (graph -> features -> detectors -> figures + metrics.json)
tests/               test_smoke.py  (fast invariants + one @slow end-to-end)
results/             figures/*.png + metrics.json  (committed)
data/ models/        git-ignored (synthetic graph is generated at runtime)
```

## References

- FATF. *Money Laundering Typologies* — structuring/smurfing and layering definitions.
- Altman et al. *Realistic Synthetic Financial Transactions for AML Models* (IBM,
  NeurIPS 2023) — the public **IBM Transactions for AML** dataset (optional real path;
  see [data/README.md](data/README.md)).
- Weber et al. *Anti-Money Laundering in Bitcoin* (Elliptic) — graph features for AML.
