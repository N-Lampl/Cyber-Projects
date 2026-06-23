"""Run the unsupervised anomaly detectors and write figures + metrics.json.

    python scripts/run_detect.py            # default IsolationForest
    python scripts/run_detect.py --ae       # also run the optional autoencoder
    python scripts/run_detect.py --n 20000  # bigger synthetic stream
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from txn_anomaly import (  # noqa: E402
    AutoencoderDetector,
    IForestDetector,
    evaluate_scores,
    feature_matrix,
    make_transactions,
    set_seed,
    torch_available,
)

RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"


def plot_score_distribution(scores, y, path):
    fig, ax = plt.subplots(figsize=(7, 4))
    normal = scores[y == 0]
    anom = scores[y == 1]
    lo, hi = np.percentile(scores, [0.5, 99.5])
    bins = np.linspace(lo, hi, 60)
    ax.hist(normal, bins=bins, alpha=0.6, label=f"normal (n={len(normal)})", color="#4C72B0")
    ax.hist(anom, bins=bins, alpha=0.8, label=f"injected anomaly (n={len(anom)})", color="#C44E52")
    ax.set_xlabel("anomaly score (higher = more anomalous)")
    ax.set_ylabel("count")
    ax.set_title("Anomaly-score distribution: normal vs injected")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_precision_at_k(scores, y, path):
    order = np.argsort(-scores)
    y_sorted = y[order]
    ks = np.arange(1, min(500, len(y)) + 1)
    cum_hits = np.cumsum(y_sorted[: len(ks)])
    precision = cum_hits / ks
    total_pos = max(1, int(y.sum()))
    recall = cum_hits / total_pos
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(ks, precision, label="precision@k", color="#4C72B0")
    ax.plot(ks, recall, label="recall@k", color="#55A868")
    ax.axvline(total_pos, ls="--", color="gray", lw=1, label=f"k = #anomalies ({total_pos})")
    ax.set_xlabel("k (top-k flagged for analyst review)")
    ax.set_ylabel("fraction")
    ax.set_ylim(0, 1.02)
    ax.set_title("Precision@k / Recall@k (analyst alert queue)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_timeline(df, scores, thr, path):
    fig, ax = plt.subplots(figsize=(9, 4))
    t = df["timestamp"]
    y = df["is_anomaly"].to_numpy()
    ax.scatter(
        t[y == 0], scores[y == 0], s=6, alpha=0.25, color="#4C72B0", label="normal"
    )
    types = df["anomaly_type"].to_numpy()
    colors = {"amount_spike": "#C44E52", "off_hours": "#DD8452", "velocity": "#8172B3"}
    for atype, c in colors.items():
        m = (y == 1) & (types == atype)
        if m.any():
            ax.scatter(t[m], scores[m], s=30, color=c, edgecolor="k", lw=0.3, label=atype)
    ax.axhline(thr, ls="--", color="black", lw=1, label="operating threshold")
    ax.set_xlabel("transaction time")
    ax.set_ylabel("anomaly score")
    ax.set_title("Anomaly timeline (color = injected type)")
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def _plot_real_timeline(time, scores, y, thr, path):
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.scatter(time[y == 0], scores[y == 0], s=5, alpha=0.2, color="#4C72B0", label="legit")
    ax.scatter(time[y == 1], scores[y == 1], s=26, color="#C44E52", edgecolor="k", lw=0.3, label="fraud")
    ax.axhline(thr, ls="--", color="black", lw=1, label="operating threshold")
    ax.set_xlabel("transaction time (s)")
    ax.set_ylabel("anomaly score")
    ax.set_title("Anomaly score over time (real ULB; red = true fraud)")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def run_real(args) -> None:
    """Unsupervised anomaly detection on the REAL ULB creditcard.csv, scored
    against the real fraud labels (labels are used ONLY for evaluation)."""
    import pandas as pd
    from sklearn.preprocessing import StandardScaler

    set_seed(args.seed)
    FIGURES.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(args.real)
    y = df["Class"].to_numpy().astype(int)
    feat = [c for c in df.columns if c != "Class"]
    X = StandardScaler().fit_transform(df[feat].astype(float).to_numpy())
    base = float(y.mean())
    cont = max(base, 0.005)
    print(f"real ULB: {len(df):,} txns, {int(y.sum())} frauds (base rate {base:.4%})")

    det = IForestDetector(contamination=cont, seed=args.seed).fit(X)
    scores = det.score(X)
    m = evaluate_scores(y, scores, cont)
    print(f"IsolationForest  PR-AUC={m['pr_auc']}  ROC-AUC={m['roc_auc']}  "
          f"recall@{int(m['fpr_budget'] * 100)}%FPR={m['recall_at_fpr_budget']}")

    plot_score_distribution(scores, y, FIGURES / "score_distribution.png")
    plot_precision_at_k(scores, y, FIGURES / "precision_at_k.png")
    _plot_real_timeline(df["Time"].to_numpy(), scores, y, m["operating_threshold"],
                        FIGURES / "anomaly_timeline.png")

    summary = (
        f"Label-free IsolationForest on the REAL ULB creditcard stream "
        f"({len(df):,} txns, {int(y.sum())} frauds, base rate {base:.3%}): "
        f"PR-AUC={m['pr_auc']}, ROC-AUC={m['roc_auc']} — no labels used to train; "
        f"the labels only score it. Unsupervised detection is much harder than the "
        f"supervised model in p1 (that gap is the whole point)."
    )
    out = {
        "project": "p2-transaction-anomaly",
        "summary": summary,
        "source": f"ULB creditcard.csv (real, {len(df):,} txns)",
        "seed": args.seed,
        "n_transactions": int(len(df)),
        "n_anomalies": int(y.sum()),
        "base_rate": round(base, 5),
        "contamination": cont,
        "default_detector": "iforest",
        "pr_auc": m["pr_auc"],
        "roc_auc": m["roc_auc"],
        "recall_at_fpr_budget": m["recall_at_fpr_budget"],
        "fpr_budget": m["fpr_budget"],
        "operating_threshold": m["operating_threshold"],
        "precision_at_k": m["precision_at_k"],
        "recall_at_k": m["recall_at_k"],
        "figures": [
            "results/figures/score_distribution.png",
            "results/figures/precision_at_k.png",
            "results/figures/anomaly_timeline.png",
        ],
    }
    (RESULTS / "metrics.json").write_text(json.dumps(out, indent=2))
    print("\n" + summary)
    print(f"wrote {RESULTS / 'metrics.json'} and 3 figures")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--real", type=str, default=None, help="path to real ULB creditcard.csv")
    ap.add_argument("--n", type=int, default=12000, help="number of transactions")
    ap.add_argument("--contamination", type=float, default=0.012)
    ap.add_argument("--ae", action="store_true", help="also run the optional autoencoder")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    if args.real:
        run_real(args)
        return

    set_seed(args.seed)
    FIGURES.mkdir(parents=True, exist_ok=True)

    df = make_transactions(n=args.n, contamination=args.contamination, seed=args.seed)
    X = feature_matrix(df)
    y = df["is_anomaly"].to_numpy().astype(int)
    print(f"stream: {len(df)} txns, {int(y.sum())} injected anomalies "
          f"(base rate {y.mean():.4f})")

    # --- default detector: IsolationForest ------------------------------
    det = IForestDetector(contamination=args.contamination, seed=args.seed).fit(X)
    scores = det.score(X)
    metrics_if = evaluate_scores(y, scores, args.contamination)
    print(f"IsolationForest  PR-AUC={metrics_if['pr_auc']}  ROC-AUC={metrics_if['roc_auc']}  "
          f"recall@1%FPR={metrics_if['recall_at_fpr_budget']}")

    thr = metrics_if["operating_threshold"]
    fig_dist = FIGURES / "score_distribution.png"
    fig_pk = FIGURES / "precision_at_k.png"
    fig_tl = FIGURES / "anomaly_timeline.png"
    plot_score_distribution(scores, y, fig_dist)
    plot_precision_at_k(scores, y, fig_pk)
    plot_timeline(df, scores, thr, fig_tl)

    # per-anomaly-type recall in the top-k queue (k = #anomalies)
    k = max(1, int(y.sum()))
    top = np.argsort(-scores)[:k]
    flagged_types = df.iloc[top]["anomaly_type"].value_counts().to_dict()
    type_totals = df[df["is_anomaly"]]["anomaly_type"].value_counts().to_dict()
    recall_by_type = {
        t: round(flagged_types.get(t, 0) / type_totals[t], 4) for t in type_totals
    }

    detectors = {"iforest": metrics_if}

    # --- optional autoencoder -------------------------------------------
    ae_backend = "torch" if torch_available() else "not-installed"
    if args.ae:
        ae = AutoencoderDetector(contamination=args.contamination, seed=args.seed).fit(X)
        ae_scores = ae.score(X)
        metrics_ae = evaluate_scores(y, ae_scores, args.contamination)
        metrics_ae["backend"] = ae.backend
        detectors["autoencoder"] = metrics_ae
        ae_backend = ae.backend
        print(f"Autoencoder({ae.backend})  PR-AUC={metrics_ae['pr_auc']}  "
              f"ROC-AUC={metrics_ae['roc_auc']}")

    summary = (
        f"Label-free IsolationForest on a {len(df)}-txn synthetic stream "
        f"({int(y.sum())} injected anomalies, base rate {y.mean():.3%}): "
        f"PR-AUC={metrics_if['pr_auc']}, ROC-AUC={metrics_if['roc_auc']}; "
        f"a top-{k} analyst queue catches "
        f"{int(metrics_if['recall_at_fpr_budget'] * 100)}% of anomalies at a 1% FP budget."
    )

    out = {
        "project": "p2-transaction-anomaly",
        "summary": summary,
        "source": "synthetic",
        "seed": args.seed,
        "n_transactions": int(len(df)),
        "n_anomalies": int(y.sum()),
        "base_rate": round(float(y.mean()), 5),
        "contamination": args.contamination,
        "default_detector": "iforest",
        "autoencoder_backend": ae_backend,
        "pr_auc": metrics_if["pr_auc"],
        "roc_auc": metrics_if["roc_auc"],
        "recall_at_fpr_budget": metrics_if["recall_at_fpr_budget"],
        "fpr_budget": metrics_if["fpr_budget"],
        "operating_threshold": metrics_if["operating_threshold"],
        "precision_at_k": metrics_if["precision_at_k"],
        "recall_at_k": metrics_if["recall_at_k"],
        "confusion_at_threshold": metrics_if["confusion"],
        "recall_by_anomaly_type": recall_by_type,
        "detectors": detectors,
        "figures": [
            "results/figures/score_distribution.png",
            "results/figures/precision_at_k.png",
            "results/figures/anomaly_timeline.png",
        ],
    }
    (RESULTS / "metrics.json").write_text(json.dumps(out, indent=2))
    print(f"wrote {RESULTS / 'metrics.json'} and 3 figures to {FIGURES}")


if __name__ == "__main__":
    main()
