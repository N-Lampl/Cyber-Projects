#!/usr/bin/env python3
"""Train fraud classifiers on the seeded synthetic transaction table, pick the
best by PR-AUC, tune a decision threshold, and write the three money figures +
metrics.json. Run via `make detect`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: no display needed
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.metrics import precision_recall_curve  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fraud_detection import (  # noqa: E402
    build_models,
    confusion_at,
    make_transactions,
    pr_auc,
    precision_at_k,
    predict_scores,
    recall_precision_from_confusion,
    roc_auc,
    set_seed,
    split_xy,
    threshold_at_fpr,
)

PROJECT = Path(__file__).resolve().parents[1]
FIG_DIR = PROJECT / "results" / "figures"
METRICS = PROJECT / "results" / "metrics.json"


def _plot_pr_curve(y, scores, ap: float, model_name: str) -> Path:
    prec, rec, _ = precision_recall_curve(y, scores)
    base_rate = float(np.mean(y))
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(rec, prec, color="#2c3e50", linewidth=2, label=f"{model_name} (PR-AUC={ap:.3f})")
    ax.axhline(base_rate, color="#c0392b", ls="--", lw=1, label=f"chance (base rate={base_rate:.3f})")
    ax.set_xlabel("recall (fraud caught)")
    ax.set_ylabel("precision (alerts that are real fraud)")
    ax.set_title(f"Precision-Recall: fraud detection (base rate {base_rate * 100:.2f}%)", pad=12)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    out = FIG_DIR / "precision_recall_curve.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def _plot_confusion(c: dict[str, int], threshold: float) -> Path:
    mat = np.array([[c["tn"], c["fp"]], [c["fn"], c["tp"]]])
    fig, ax = plt.subplots(figsize=(4.6, 4.2))
    ax.imshow(mat, cmap="Blues")
    labels = ["legit", "fraud"]
    ax.set_xticks([0, 1], labels=[f"pred {x}" for x in labels])
    ax.set_yticks([0, 1], labels=[f"true {x}" for x in labels])
    vmax = mat.max()
    for i in range(2):
        for j in range(2):
            ax.text(
                j,
                i,
                f"{mat[i, j]:,}",
                ha="center",
                va="center",
                color="white" if mat[i, j] > vmax / 2 else "black",
                fontsize=12,
                fontweight="bold",
            )
    ax.set_title(f"Confusion matrix @ threshold={threshold:.3f}", pad=10)
    fig.tight_layout()
    out = FIG_DIR / "confusion_matrix.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def _plot_precision_at_k(y, scores, ks: list[int]) -> tuple[Path, dict[str, float]]:
    pak = {f"p@{k}": precision_at_k(y, scores, k) for k in ks}
    fig, ax = plt.subplots(figsize=(6, 4))
    names = list(pak.keys())
    vals = [pak[n] for n in names]
    bars = ax.bar(names, vals, color="#16a085")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("precision among top-k flagged")
    ax.set_title("Precision@k: quality of the analyst review queue", pad=12)
    ax.grid(True, axis="y", alpha=0.3)
    for b, v in zip(bars, vals):
        ax.annotate(f"{v:.2f}", (b.get_x() + b.get_width() / 2, v), ha="center",
                    va="bottom", fontsize=9)
    fig.tight_layout()
    out = FIG_DIR / "precision_at_k.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out, pak


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", type=str, default=None, help="path to real ULB creditcard.csv (V1..V28, Amount, Class)")
    ap.add_argument("--n", type=int, default=30_000, help="number of synthetic transactions")
    ap.add_argument("--fraud-rate", type=float, default=0.01, help="target fraud base rate")
    ap.add_argument("--target-fpr", type=float, default=0.01, help="false-positive budget for recall")
    ap.add_argument("--ks", type=int, nargs="+", default=[50, 100, 200], help="precision@k values")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    set_seed(args.seed)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    if args.real:
        from fraud_detection.data import load_creditcard_csv

        df = load_creditcard_csv(args.real)
        y = df["is_fraud"].astype(int)
        feat = [c for c in df.columns if c not in ("is_fraud", "Class")]
        x = df[feat].astype(float)
        source = f"ULB creditcard.csv (real, {len(df):,} txns)"
    else:
        df = make_transactions(n=args.n, fraud_rate=args.fraud_rate, seed=args.seed)
        x, y = split_xy(df)
        source = "synthetic"

    x_tr, x_te, y_tr, y_te = train_test_split(
        x, y, test_size=0.3, stratify=y, random_state=args.seed
    )
    if args.real:  # standardize anonymized PCA features + Amount/Time (fit on TRAIN only)
        scaler = StandardScaler().fit(x_tr)
        x_tr, x_te = scaler.transform(x_tr), scaler.transform(x_te)
    print(
        f"{source}: {len(df):,} txns, fraud rate {y.mean() * 100:.3f}% | "
        f"train fraud={int(y_tr.sum())}, test fraud={int(y_te.sum())}"
    )

    # --- train every available model, rank by PR-AUC -------------------------
    results: dict[str, dict] = {}
    scores_by_model: dict[str, np.ndarray] = {}
    for name, model in build_models().items():
        model.fit(x_tr, y_tr)
        s = np.asarray(predict_scores(model, x_te))
        scores_by_model[name] = s
        results[name] = {"pr_auc": pr_auc(y_te, s), "roc_auc": roc_auc(y_te, s)}
        print(f"  {name:<9} PR-AUC={results[name]['pr_auc']:.4f}  ROC-AUC={results[name]['roc_auc']:.4f}")

    best_name = max(results, key=lambda k: results[k]["pr_auc"])
    best_scores = scores_by_model[best_name]
    print(f"best by PR-AUC: {best_name}")

    # --- operating point: threshold at the false-positive budget -------------
    threshold, recall_at_fpr = threshold_at_fpr(y_te, best_scores, args.target_fpr)
    conf = confusion_at(y_te, best_scores, threshold)
    recall, precision = recall_precision_from_confusion(conf)

    # --- figures -------------------------------------------------------------
    pr_fig = _plot_pr_curve(y_te, best_scores, results[best_name]["pr_auc"], best_name)
    cm_fig = _plot_confusion(conf, threshold)
    pak_fig, pak = _plot_precision_at_k(y_te, best_scores, args.ks)

    summary = (
        f"{best_name} on {source} (fraud rate "
        f"{y.mean() * 100:.3f}%): PR-AUC={results[best_name]['pr_auc']:.3f}, "
        f"ROC-AUC={results[best_name]['roc_auc']:.3f}; at a {args.target_fpr * 100:.0f}% "
        f"false-positive budget it catches {recall * 100:.0f}% of fraud at "
        f"{precision * 100:.0f}% alert precision; p@100={pak.get('p@100', float('nan')):.2f}."
    )

    metrics = {
        "project": "p1-fraud-detection",
        "summary": summary,
        "source": source,
        "best_model": best_name,
        "seed": args.seed,
        "n_transactions": int(len(df)),
        "n_features": int(x.shape[1]),
        "fraud_rate_realized": float(y.mean()),
        "target_fpr": args.target_fpr,
        "operating_threshold": threshold,
        "pr_auc": results[best_name]["pr_auc"],
        "roc_auc": results[best_name]["roc_auc"],
        "recall_at_fpr": recall_at_fpr,
        "recall_at_threshold": recall,
        "precision_at_threshold": precision,
        "confusion": conf,
        "precision_at_k": pak,
        "models": results,
        "figures": [
            str(pr_fig.relative_to(PROJECT)),
            str(cm_fig.relative_to(PROJECT)),
            str(pak_fig.relative_to(PROJECT)),
        ],
    }
    METRICS.write_text(json.dumps(metrics, indent=2) + "\n")
    print("\n" + summary)
    for p in (pr_fig, cm_fig, pak_fig, METRICS):
        print(f"wrote {p.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
