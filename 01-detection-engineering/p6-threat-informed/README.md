# p6 · Threat-informed detection-as-code

Detection rules are code, so treat them like code: version them, **validate** them in CI, and
measure what they actually cover. This project ships a handful of **Sigma** rules for real ATT&CK
techniques, a dependency-free Python **loader/validator** that maps each rule to its ATT&CK ID, and
a matplotlib **ATT&CK-coverage heatmap** that makes the gaps obvious.

**Authorized use only.** Rules here target detections of attacker behaviour on systems you own /
are authorized to monitor; the catalog and rules are synthetic/illustrative. See
[../../ETHICS.md](../../ETHICS.md).

## The idea

A threat-informed defense starts from the adversary playbook (MITRE ATT&CK) and asks: *for each
technique, do I have a detection?* Sigma is the vendor-neutral YAML format for those detections.

```
   Sigma rules (YAML)                loader/validator                 ATT&CK coverage
  ┌──────────────────┐   parse +    ┌────────────────┐   map tags   ┌──────────────────┐
  │ rules/*.yml      │ ───────────▶ │ required fields │ ───────────▶ │ technique → #rules│
  │ tags: attack.tID │   validate   │ logsource/cond. │  to ATT&CK   │ heatmap + metrics │
  └──────────────────┘              └────────────────┘              └──────────────────┘
```

Each rule carries `tags: [attack.tXXXX.YYY]`. The loader extracts that technique ID, checks it
against an embedded ATT&CK catalog, and a rule is **valid** only if it has the required Sigma fields
(`title`, `logsource` with a category/service, `detection` with a `condition`, `level`) **and** maps
to a known technique. Coverage is then `#valid rules per technique`, projected onto the ATT&CK
tactic columns.

**Offline by default.** PyYAML is optional — the loader falls back to a small built-in YAML-subset
parser, and the ATT&CK catalog is embedded, so `make detect` runs with only numpy + matplotlib.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make detect          # validate rules + map to ATT&CK + write heatmap & metrics.json
make test            # fast smoke tests
```

Optional enhanced path: `pip install pyyaml` to parse with PyYAML instead of the fallback
(same results). To grade against the *full* ATT&CK matrix, swap the embedded catalog for the
official STIX bundle (see [data/README.md](data/README.md)).

Outputs land in [results/](results/):
- `figures/attack_coverage_heatmap.png` — technique × tactic grid, cells = #rules (the money plot).
- `figures/tactic_coverage_bar.png` — techniques covered per tactic, gaps in grey.
- `metrics.json` — valid/invalid counts + technique/tactic coverage % (committed as evidence).

## What the result shows

The six shipped rules validate cleanly and cover **6 ATT&CK techniques across 6 tactics**
(Execution, Persistence, Privilege Escalation, Credential Access, Lateral Movement) — but the
heatmap is mostly empty, which is the point: it turns "we have some detections" into a quantified,
reviewable coverage gap you can drive a backlog from.

## Interview story (3 sentences)

> I built a detection-as-code pipeline that validates Sigma rules and maps each one to its MITRE
> ATT&CK technique, then renders a coverage heatmap so gaps are visible at a glance. The validator
> is dependency-free (PyYAML optional, with a built-in YAML fallback) and fails the build on
> malformed rules or unknown technique IDs, so coverage can be gated in CI. It reframes detection
> engineering from "we wrote some rules" to a measurable, threat-informed coverage metric.

## Layout

```
rules/             *.yml  Sigma rules (committed inputs)
src/threat_informed/  utils.py (seeds) · attack.py (offline ATT&CK) · loader.py (validate+map) · coverage.py
scripts/           build_coverage.py  (validate → heatmap + metrics.json)
tests/             test_smoke.py  (fast invariants + one @slow end-to-end)
results/           figures/*.png + metrics.json  (committed)
data/ models/      git-ignored, unused (no dataset, no model)
```

## References

- MITRE ATT&CK (Enterprise) — <https://attack.mitre.org/>
- Sigma detection format — <https://sigmahq.io/> · <https://github.com/SigmaHQ/sigma>
- ATT&CK STIX data (CC-BY 4.0) — <https://github.com/mitre-attack/attack-stix-data>
