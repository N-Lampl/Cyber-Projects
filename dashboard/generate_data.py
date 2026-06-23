#!/usr/bin/env python3
"""Aggregate every project's results into one JSON the dashboard renders.

Walks the six tracks, reads each project's results/metrics.json + README title,
copies its figures into the dashboard's public/ assets, and writes
src/data/projects.json. Re-run any time projects change:  python3 generate_data.py
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

DASH = Path(__file__).resolve().parent
ROOT = DASH.parent
PUBLIC_FIG = DASH / "public" / "figures"
OUT = DASH / "src" / "data" / "projects.json"

TRACKS = [
    ("00-foundations", "Foundations",
     "Security fundamentals as artifacts: ATT&CK/ATLAS, threat modeling, networking, web/appsec, crypto."),
    ("01-detection-engineering", "Detection Engineering",
     "ML on security telemetry: intrusion / malware / phishing / DGA detection, UEBA, detection-as-code."),
    ("02-adversarial-robustness", "Adversarial Robustness",
     "Evasion attacks and defenses: FGSM/PGD/C&W, black-box, adversarial training, certified robustness."),
    ("03-ml-privacy", "ML Privacy",
     "Stealing models and training data, and defending with differential privacy."),
    ("04-llm-security", "LLM Security",
     "Prompt injection, RAG/agent attacks, guardrails, CI red-team, alignment-robustness interpretability."),
    ("05-ml-supply-chain", "ML Supply Chain",
     "Securing the model supply chain: pickle-RCE, safetensors, scanning, Sigstore signing, CI gates."),
    ("06-financial-ml", "Financial Crime & Risk",
     "ML for financial crime and risk: fraud, anomaly detection, AML typologies, credit risk, market manipulation."),
]

FLAGSHIPS = {
    "CAPSTONE-adversarial-ids", "CAPSTONE-appsec-ci", "CAPSTONE-dp-defenses",
    "p7-defend-rag", "secure-ml-pipeline",
}
SEED = {"p1-fgsm-mnist"}

NOISE_KEYS = {"project", "summary", "figures", "seed", "note", "source", "track",
              "method", "path", "attack", "defense", "attack_engine", "accountant",
              "default_backend"}


def pct(x: float) -> str:
    return f"{x * 100:.0f}%" if abs(x) < 1.0001 else f"{x:.2f}"


def read_title(proj_dir: Path, fallback: str) -> str:
    readme = proj_dir / "README.md"
    if readme.exists():
        for line in readme.read_text(errors="ignore").splitlines():
            if line.startswith("# "):
                # strip leading "pN . " noise, keep the human title
                return re.sub(r"^p\d+\s*[.·-]\s*", "", line[2:].strip())
    return fallback


def read_blurb(proj_dir: Path) -> str:
    """First human tagline from the README (the '>' blockquote or first prose line)."""
    readme = proj_dir / "README.md"
    if not readme.exists():
        return ""
    seen_title = False
    for line in readme.read_text(errors="ignore").splitlines():
        s = line.strip()
        if s.startswith("# "):
            seen_title = True
            continue
        if not seen_title or not s:
            continue
        if s.startswith(("![", "|", "```", "Authorized", "Note:")):
            continue
        s = s.lstrip("> ").strip()
        if s:
            s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)  # strip md links
            return s.replace("**", "").replace("`", "")  # strip emphasis/code ticks
    return ""


def scalar_metrics(m: dict) -> list[dict]:
    """Top-level scalar metrics suitable for compact chips."""
    out = []
    for k, v in m.items():
        if k in NOISE_KEYS or isinstance(v, (dict, list)):
            continue
        if isinstance(v, bool):
            out.append({"k": k, "v": "yes" if v else "no"})
        elif isinstance(v, (int, float)):
            hint = any(t in k for t in ("rate", "acc", "auc", "asr", "pct", "cosine",
                                        "retention", "fraction", "reduction"))
            out.append({"k": k, "v": pct(float(v)) if (hint and abs(v) <= 1.0001) else f"{v:g}"})
        elif isinstance(v, str) and len(v) <= 40:
            out.append({"k": k, "v": v})
    return out[:6]


def load_metrics(proj_dir: Path) -> dict | None:
    f = proj_dir / "results" / "metrics.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text())
    except json.JSONDecodeError:
        return None


def copy_figures(proj_dir: Path, pid: str) -> list[dict]:
    figs = []
    fdir = proj_dir / "results" / "figures"
    if not fdir.is_dir():
        return figs
    dest = PUBLIC_FIG / pid
    for png in sorted(fdir.glob("*.png")):
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(png, dest / png.name)
        figs.append({"name": png.stem.replace("_", " "), "url": f"figures/{pid}/{png.name}"})
    return figs


def find_projects(track_id: str) -> list[Path]:
    base = ROOT / track_id
    out = []
    for metrics in base.rglob("results/metrics.json"):
        out.append(metrics.parent.parent)
    return sorted(out)


def build_highlights(by_id: dict) -> list[dict]:
    """Curated headline wins, pulled from REAL metric values (skip if absent)."""
    H = []

    def g(pid, *keys):
        m = by_id.get(pid, {}).get("raw", {})
        for k in keys:
            if isinstance(m, dict) and k in m:
                m = m[k]
            else:
                return None
        return m

    fgsm_clean = g("02-adversarial-robustness__p1-fgsm-mnist", "clean_accuracy")
    fgsm_eps = g("02-adversarial-robustness__p1-fgsm-mnist", "accuracy_by_epsilon", "0.3")
    if fgsm_clean is not None and fgsm_eps is not None:
        H.append({"title": "FGSM breaks a 99% MNIST classifier",
                  "before": pct(fgsm_clean), "after": pct(fgsm_eps),
                  "label": "accuracy", "project": "02-adversarial-robustness__p1-fgsm-mnist",
                  "blurb": "A tiny imperceptible perturbation collapses accuracy."})

    asr_b = g("04-llm-security__p7-defend-rag", "asr_before")
    asr_a = g("04-llm-security__p7-defend-rag", "asr_after")
    if asr_b is not None and asr_a is not None:
        H.append({"title": "Guardrails kill RAG prompt-injection",
                  "before": pct(asr_b), "after": pct(asr_a),
                  "label": "attack success", "project": "04-llm-security__p7-defend-rag",
                  "blurb": "Layered guardrails + a from-scratch injection detector."})

    ids_b = g("01-detection-engineering__CAPSTONE-adversarial-ids", "attack_before", "attack_success_rate")
    ids_a = g("01-detection-engineering__CAPSTONE-adversarial-ids", "attack_after", "attack_success_rate")
    if ids_b is not None and ids_a is not None:
        H.append({"title": "Harden your own IDS against evasion",
                  "before": pct(ids_b), "after": pct(ids_a),
                  "label": "evasion rate", "project": "01-detection-engineering__CAPSTONE-adversarial-ids",
                  "blurb": "Constrained adversarial flows, then adversarial training."})

    p8 = "04-llm-security__p8-refusal-direction-interp"
    ref_b = g(p8, "refusal_rate_harmful_before")
    ref_a = g(p8, "refusal_rate_harmful_after")
    if ref_b is None:  # fall back to the synthetic-path key names
        ref_b, ref_a = g(p8, "refusal_rate_before"), g(p8, "refusal_rate_after")
    cap = g(p8, "capability_retention")
    model = g(p8, "model_id")
    if ref_b is not None and ref_a is not None:
        tail = f" on {model.split('/')[-1]}" if isinstance(model, str) else ""
        H.append({"title": "Abliteration: refusal lives on one axis",
                  "before": pct(ref_b), "after": pct(ref_a),
                  "label": "refusal rate", "project": p8,
                  "blurb": f"Ablating one direction removes refusals{tail}; "
                           f"capability retained {pct(cap) if cap else 'n/a'}."})

    fr = "06-financial-ml__CAPSTONE-adversarial-fraud"
    fr_b = g(fr, "attack", "asr_before")
    fr_a = g(fr, "attack", "asr_after")
    if fr_b is not None and fr_a is not None:
        H.append({"title": "Harden a fraud model vs evasion",
                  "before": pct(fr_b), "after": pct(fr_a),
                  "label": "evasion rate", "project": fr,
                  "blurb": "Feasibility-constrained adversarial transactions, then adversarial training."})

    return H


ROADMAP = [
    {"title": "Wire in real datasets",
     "detail": "Swap synthetic fallbacks for EMBER / CICIDS / NSL-KDD / LANL on the detection track and re-measure."},
    {"title": "Run against real LLMs",
     "detail": "Drop your API key (or local Ollama) into .env and re-run the LLM-security attacks/defenses on a real model."},
    {"title": "Abliterate a real open-weight model",
     "detail": "Enable the p8 real-model path (transformers + a small Qwen/Llama) on a free Colab/Kaggle GPU."},
    {"title": "Ship the CI-gated red-team",
     "detail": "Turn on the appsec-ci GitHub Action so every commit runs a red-team and fails on ASR regressions."},
    {"title": "Deploy this dashboard",
     "detail": "Publish to GitHub Pages for a shareable 'click this link' portfolio artifact."},
    {"title": "Deepen a flagship",
     "detail": "Pick one capstone, harden it to interview depth, and write the threat-model report."},
]


def main() -> None:
    if PUBLIC_FIG.exists():
        shutil.rmtree(PUBLIC_FIG)
    PUBLIC_FIG.mkdir(parents=True, exist_ok=True)

    projects, tracks_out = [], []
    total_figs = 0
    for track_id, track_name, blurb in TRACKS:
        ids = []
        for proj_dir in find_projects(track_id):
            slug = str(proj_dir.relative_to(ROOT / track_id))
            pid = f"{track_id}__{slug.replace('/', '__')}"
            m = load_metrics(proj_dir) or {}
            figs = copy_figures(proj_dir, pid)
            total_figs += len(figs)
            short = slug.split("/")[-1]
            kind = "flagship" if short in FLAGSHIPS else ("seed" if short in SEED else "project")
            summary_raw = m.get("summary")
            summary = summary_raw if isinstance(summary_raw, str) else read_blurb(proj_dir)
            chips = scalar_metrics(m)
            if isinstance(summary_raw, dict):  # some projects parked numbers under "summary"
                chips = (scalar_metrics(summary_raw) + chips)[:6]
            projects.append({
                "id": pid, "track": track_id, "trackName": track_name, "slug": slug,
                "name": read_title(proj_dir, short), "shortName": short,
                "summary": summary, "kind": kind,
                "metrics": chips, "figures": figs,
                "raw": m,
                "repoPath": f"{track_id}/{slug}",
            })
            ids.append(pid)
        tracks_out.append({"id": track_id, "name": track_name, "blurb": blurb, "projectIds": ids})

    by_id = {p["id"]: p for p in projects}
    data = {
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "repoUrl": "https://github.com/N-Lampl/Cyber-Projects",
        "totals": {"projects": len(projects), "tracks": len(tracks_out), "figures": total_figs},
        "tracks": tracks_out,
        "projects": projects,
        "highlights": build_highlights(by_id),
        "roadmap": ROADMAP,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(DASH)}: {len(projects)} projects, {total_figs} figures, "
          f"{len(data['highlights'])} highlights")


if __name__ == "__main__":
    main()
