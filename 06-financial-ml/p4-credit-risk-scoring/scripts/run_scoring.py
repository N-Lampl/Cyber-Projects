#!/usr/bin/env python3
"""Train + calibrate LogReg and GradientBoosting credit-risk models, then write
ROC / reliability / score-distribution figures and metrics.json. Run via
`make run`. Default path is fully offline (seeded synthetic data).
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
from sklearn.metrics import roc_curve  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from credit_risk import (  # noqa: E402
    build_model,
    calibration,
    confusion_at_threshold,
    discrimination,
    fairness_at_threshold,
    fit_predict_proba,
    make_credit_data,
    set_seed,
    threshold_for_default_rate,
    train_test_split_df,
)

PROJECT = Path(__file__).resolve().parents[1]
FIG_DIR = PROJECT / "results" / "figures"
METRICS = PROJECT / "results" / "metrics.json"

MODELS = {"logreg": "LogisticRegression", "gbm": "GradientBoosting"}


def _plot_roc(results: dict, y_test: np.ndarray) -> Path:
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot([0, 1], [0, 1], "--", color="#888", linewidth=1, label="chance")
    colors = {"logreg": "#2980b9", "gbm": "#c0392b"}
    for kind, r in results.items():
        fpr, tpr, _ = roc_curve(y_test, r["proba"])
        ax.plot(fpr, tpr, color=colors[kind], linewidth=2,
                label=f"{MODELS[kind]} (AUC={r['disc']['roc_auc']:.3f})")
    ax.set_xlabel("false positive rate")
    ax.set_ylabel("true positive rate")
    ax.set_title("ROC curve: default discrimination", pad=12)
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out = FIG_DIR / "roc_curve.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def _plot_reliability(results: dict) -> Path:
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot([0, 1], [0, 1], "--", color="#888", linewidth=1, label="perfectly calibrated")
    colors = {"logreg": "#2980b9", "gbm": "#c0392b"}
    for kind, r in results.items():
        c = r["cal"]["curve"]
        ax.plot(c["mean_predicted"], c["observed_rate"], "o-", color=colors[kind],
                linewidth=2, label=f"{MODELS[kind]} (Brier={r['cal']['brier_score']:.3f})")
    ax.set_xlabel("mean predicted probability of default")
    ax.set_ylabel("observed default rate")
    ax.set_title("Reliability curve (calibrated PD)", pad=12)
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out = FIG_DIR / "reliability_curve.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def _plot_score_dist(best_kind: str, results: dict, y_test: np.ndarray) -> Path:
    proba = results[best_kind]["proba"]
    fig, ax = plt.subplots(figsize=(6, 5))
    bins = np.linspace(0, 1, 30)
    ax.hist(proba[y_test == 0], bins=bins, alpha=0.6, color="#27ae60",
            label="repaid (y=0)", density=True)
    ax.hist(proba[y_test == 1], bins=bins, alpha=0.6, color="#c0392b",
            label="defaulted (y=1)", density=True)
    thr = results[best_kind]["threshold"]
    ax.axvline(thr, color="#2c3e50", linestyle="--", linewidth=1.5,
               label=f"operating thr={thr:.3f}")
    ax.set_xlabel("predicted probability of default")
    ax.set_ylabel("density")
    ax.set_title(f"Score distribution by outcome — {MODELS[best_kind]}", pad=12)
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out = FIG_DIR / "score_distribution.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def run_real(args, csv_path: str) -> None:
    """Score the REAL UCI German Credit data (1000 borrowers, 20 attributes).

    Uses the data's real features (categoricals one-hot encoded) and a genuine
    protected attribute: applicant age < 25 ("young") vs older. Labels: 1=good,
    2=bad -> default=1. Reuses the same calibration/discrimination/fairness code.
    """
    import pandas as pd
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    set_seed()
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    cols = [f"a{i}" for i in range(1, 21)] + ["label"]
    raw = pd.read_csv(csv_path, sep=r"\s+", header=None, names=cols)
    y = (raw["label"] == 2).astype(int).to_numpy()  # 2 = bad credit = default
    groups = np.where(raw["a13"].astype(int) < 25, "young", "older")  # a13 = age
    feat = raw.drop(columns=["label"])
    cat_cols = [c for c in feat.columns if feat[c].dtype == object]
    X = pd.get_dummies(feat, columns=cat_cols).astype(float).to_numpy()

    x_tr, x_te, y_tr, y_test, _, groups_test = train_test_split(
        X, y, groups, test_size=0.3, stratify=y, random_state=42
    )
    default_rate = float(y.mean())
    source = f"real: UCI German Credit (n={len(raw)}, age<25 as protected group)"
    print(f"source={source}  base default rate={default_rate:.3f}  "
          f"young={int((groups == 'young').sum())}")

    estimators = {
        "logreg": make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=2000, class_weight="balanced")
        ),
        "gbm": GradientBoostingClassifier(random_state=42),
    }
    results: dict[str, dict] = {}
    for kind, clf in estimators.items():
        model = CalibratedClassifierCV(clf, method=args.method, cv=3)
        model.fit(x_tr, y_tr)
        proba = model.predict_proba(x_te)[:, 1]
        disc = discrimination(y_test, proba)
        cal = calibration(y_test, proba, n_bins=8)
        thr = threshold_for_default_rate(proba, args.decline_rate)
        conf = confusion_at_threshold(y_test, proba, thr)
        fair = fairness_at_threshold(y_test, proba, groups_test, thr)
        results[kind] = {"proba": proba, "disc": disc, "cal": cal,
                         "threshold": thr, "confusion": conf, "fairness": fair}
        print(f"[{MODELS[kind]}] ROC-AUC={disc['roc_auc']:.4f} KS={disc['ks_statistic']:.4f} "
              f"Gini={disc['gini']:.4f} Brier={cal['brier_score']:.4f} "
              f"approval-gap={fair['approval_rate_gap']:.4f}")

    best_kind = max(results, key=lambda k: results[k]["disc"]["roc_auc"])
    roc = _plot_roc(results, y_test)
    rel = _plot_reliability(results)
    dist = _plot_score_dist(best_kind, results, y_test)
    b = results[best_kind]
    summary = (
        f"Calibrated {MODELS[best_kind]} on REAL UCI German Credit: "
        f"ROC-AUC={b['disc']['roc_auc']:.3f}, KS={b['disc']['ks_statistic']:.3f}, "
        f"Gini={b['disc']['gini']:.3f}, Brier={b['cal']['brier_score']:.3f}; declining the "
        f"riskiest {int(args.decline_rate * 100)}% leaves a {b['fairness']['approval_rate_gap']:.3f} "
        f"approval-rate gap between younger and older applicants."
    )

    def _clean(r: dict) -> dict:
        return {"discrimination": r["disc"],
                "calibration": {"brier_score": r["cal"]["brier_score"], "ece": r["cal"]["ece"],
                                "reliability_curve": r["cal"]["curve"]},
                "operating_threshold": r["threshold"], "confusion": r["confusion"],
                "fairness": r["fairness"]}

    metrics = {
        "project": "p4-credit-risk-scoring", "summary": summary, "source": source, "seed": 42,
        "n_total": len(raw), "n_train": len(x_tr), "n_test": len(x_te),
        "base_default_rate": default_rate, "calibration_method": args.method,
        "decline_rate": args.decline_rate, "best_model": best_kind,
        "models": {kind: _clean(r) for kind, r in results.items()},
        "figures": [str(roc.relative_to(PROJECT)), str(rel.relative_to(PROJECT)),
                    str(dist.relative_to(PROJECT))],
    }
    METRICS.write_text(json.dumps(metrics, indent=2) + "\n")
    print("\n" + summary)
    for p in (roc, rel, dist, METRICS):
        print(f"wrote {p.relative_to(PROJECT)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12000, help="synthetic borrowers")
    ap.add_argument("--decline-rate", type=float, default=0.20,
                    help="operating point: decline the riskiest fraction of applicants")
    ap.add_argument("--method", default="isotonic", choices=["isotonic", "sigmoid"],
                    help="probability calibration method")
    ap.add_argument("--real-csv", default=None,
                    help="optional path to a real credit CSV (see data/README.md)")
    args = ap.parse_args()

    set_seed()
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    if args.real_csv:
        run_real(args, args.real_csv)
        return

    source = "synthetic"
    df = make_credit_data(n=args.n, seed=42)

    train_df, test_df = train_test_split_df(df, test_size=0.3, seed=42)
    y_test = test_df["default"].to_numpy()
    groups_test = test_df["group"].to_numpy()
    default_rate = float(df["default"].mean())
    print(f"source={source}  n={len(df)}  base default rate={default_rate:.3f}")

    results: dict[str, dict] = {}
    for kind in ("logreg", "gbm"):
        model = build_model(kind=kind, calibrate=True, method=args.method)
        model, proba = fit_predict_proba(model, train_df, test_df)
        disc = discrimination(y_test, proba)
        cal = calibration(y_test, proba, n_bins=10)
        thr = threshold_for_default_rate(proba, args.decline_rate)
        conf = confusion_at_threshold(y_test, proba, thr)
        fair = fairness_at_threshold(y_test, proba, groups_test, thr)
        results[kind] = {
            "proba": proba, "disc": disc, "cal": cal,
            "threshold": thr, "confusion": conf, "fairness": fair,
        }
        print(f"\n[{MODELS[kind]}]")
        print(f"  ROC-AUC={disc['roc_auc']:.4f}  KS={disc['ks_statistic']:.4f}  "
              f"Gini={disc['gini']:.4f}")
        print(f"  Brier={cal['brier_score']:.4f}  ECE={cal['ece']:.4f}")
        print(f"  thr={thr:.4f}  approval-rate gap={fair['approval_rate_gap']:.4f}  "
              f"TPR gap={fair['tpr_gap']:.4f}")

    # Best model by ROC-AUC drives the score-distribution figure + summary.
    best_kind = max(results, key=lambda k: results[k]["disc"]["roc_auc"])
    roc = _plot_roc(results, y_test)
    rel = _plot_reliability(results)
    dist = _plot_score_dist(best_kind, results, y_test)

    b = results[best_kind]
    summary = (
        f"Calibrated {MODELS[best_kind]} scores synthetic credit default: "
        f"ROC-AUC={b['disc']['roc_auc']:.3f}, KS={b['disc']['ks_statistic']:.3f}, "
        f"Gini={b['disc']['gini']:.3f}, Brier={b['cal']['brier_score']:.3f}; "
        f"declining the riskiest {int(args.decline_rate * 100)}% leaves an approval-rate "
        f"gap of {b['fairness']['approval_rate_gap']:.3f} between protected groups."
    )

    def _clean(r: dict) -> dict:
        return {
            "discrimination": r["disc"],
            "calibration": {"brier_score": r["cal"]["brier_score"], "ece": r["cal"]["ece"],
                            "reliability_curve": r["cal"]["curve"]},
            "operating_threshold": r["threshold"],
            "confusion": r["confusion"],
            "fairness": r["fairness"],
        }

    metrics = {
        "project": "p4-credit-risk-scoring",
        "summary": summary,
        "source": source,
        "seed": 42,
        "n_total": len(df),
        "n_train": len(train_df),
        "n_test": len(test_df),
        "base_default_rate": default_rate,
        "calibration_method": args.method,
        "decline_rate": args.decline_rate,
        "best_model": best_kind,
        "models": {kind: _clean(r) for kind, r in results.items()},
        "figures": [
            str(roc.relative_to(PROJECT)),
            str(rel.relative_to(PROJECT)),
            str(dist.relative_to(PROJECT)),
        ],
    }
    METRICS.write_text(json.dumps(metrics, indent=2) + "\n")
    print(f"\nbest model: {MODELS[best_kind]}")
    for p in (roc, rel, dist, METRICS):
        print(f"wrote {p.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
