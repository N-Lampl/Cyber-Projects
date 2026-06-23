# module-1 · Attack Atlas (MITRE ATT&CK × MITRE ATLAS)

The foundations module: a primer + a **reusable, machine-readable artifact** that maps every
project in this repo to the adversarial-ML techniques it demonstrates. It answers the question a
hiring manager (or a threat-modeling review) will actually ask: *"which real attacks does this
work cover, and how do they relate to the classic kill chain?"*

**Authorized use only.** This module is documentation/threat-modeling over **self-trained models
and synthetic data only** — no live targets. See [../../ETHICS.md](../../ETHICS.md).

## The two frameworks

- **MITRE ATT&CK** — the industry-standard matrix of adversary *tactics* (the "why": Initial Access,
  Execution, Exfiltration, Impact…) and *techniques* (the "how": `T1195` Supply Chain Compromise,
  `T1041` Exfiltration over C2…). It models attacks on conventional IT systems.
- **MITRE ATLAS** — the ATT&CK-style matrix for **AI/ML systems** (Adversarial Threat Landscape for
  Artificial-Intelligence Systems). Same shape, ML-specific techniques with `AML.Txxxx` IDs:
  `AML.T0043` Craft Adversarial Data (evasion), `AML.T0024` Exfiltration via ML Inference API,
  `AML.T0010` ML Supply Chain Compromise, `AML.T0051` LLM Prompt Injection, …

ATLAS techniques frequently *bridge back* to ATT&CK (a poisoned model artifact is still
`T1195` Supply Chain Compromise). This module makes that bridge explicit.

```
 repo track/project ──maps to──▶ ATLAS technique (AML.Txxxx) ──bridges to──▶ ATT&CK technique (Txxxx)
   p1-fgsm-mnist               AML.T0043 Craft Adversarial Data            T1565 Data Manipulation
   03-ml-privacy               AML.T0024 Exfil via Inference API           T1041 Exfil over C2
   05-ml-supply-chain          AML.T0010 ML Supply Chain Compromise        T1195 Supply Chain Compromise
   04-llm-security             AML.T0051 LLM Prompt Injection              T1059 Command/Scripting
```

The catalog + portfolio map live in [src/attack_atlas/atlas.py](src/attack_atlas/atlas.py) so the
whole build is **stdlib-only and offline** (no MITRE downloads, no network).

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make run         # build results/atlas_map.json + metrics.json + ASCII coverage figure
make navigator   # (re)build navigator/portfolio_layer.json — a valid ATT&CK Navigator layer
make test        # fast smoke tests (validate IDs, schema, navigator layer)
```

Outputs:
- [results/atlas_map.json](results/atlas_map.json) — each track/project → ATLAS technique IDs
  (with names, tactics, and the bridged ATT&CK refs).
- [results/metrics.json](results/metrics.json) — counts (entries, techniques, tactics covered,
  ATT&CK techniques bridged) for a future dashboard to auto-discover.
- [results/figures/coverage_by_tactic.txt](results/figures/coverage_by_tactic.txt) — an ASCII bar
  chart of ATLAS-tactic coverage (no matplotlib needed — this project is stdlib-only).
- [navigator/portfolio_layer.json](navigator/portfolio_layer.json) — open it at
  <https://mitre-attack.github.io/attack-navigator/> via **File → Open Existing Layer** to see the
  exercised ATT&CK techniques highlighted, scored by how many projects touch each.

## What the result shows

The portfolio spans the ML kill chain end to end: **ML Model Access → Attack Staging (craft
adversarial data) → Defense Evasion → Exfiltration → Impact**, plus the **Initial Access /
Persistence** supply-chain path and the **Execution** LLM-injection path. The coverage figure makes
the gaps and the concentration visible at a glance, and the Navigator layer turns "I did some ML
security projects" into a concrete, reviewable ATT&CK overlay.

## Interview story (3 sentences)

> I built a machine-readable map from every project in my ML-security portfolio to the MITRE ATLAS
> technique it demonstrates, then bridged each ATLAS technique back to classic MITRE ATT&CK so the
> work plugs straight into a conventional threat model. It emits a valid ATT&CK Navigator layer and a
> coverage metrics file, so the portfolio is reviewable as a threat model rather than a pile of
> scripts. The exercise is also how I reason about new ML systems: enumerate model access, staging,
> evasion, exfiltration, and supply-chain risk before writing any attack code.

## Optional enhanced path

The default build uses a curated, self-contained subset of the ATLAS/ATT&CK catalogs (offline). To
validate technique IDs against the **live** ATT&CK catalog, install `mitreattack-python` (listed,
commented, in `requirements.txt`) and cross-check `attack_refs` against the fetched STIX bundle —
imported lazily so the default build never needs it.

## Layout

```
src/attack_atlas/  utils.py (set_seed/get_device) · atlas.py (catalog + portfolio map)
                   builder.py (map/metrics/chart) · navigator.py (ATT&CK layer)
scripts/           build_atlas_map.py · build_navigator_layer.py
navigator/         portfolio_layer.json  (valid ATT&CK Navigator layer, committed)
tests/             test_smoke.py  (fast invariants + one @slow end-to-end)
results/           atlas_map.json · metrics.json · figures/coverage_by_tactic.txt  (committed)
data/ models/      git-ignored; this project has no dataset and trains no models
```

## References

- MITRE ATLAS — *Adversarial Threat Landscape for AI Systems.* <https://atlas.mitre.org/>
- MITRE ATT&CK — Enterprise matrix. <https://attack.mitre.org/>
- ATT&CK Navigator layer format (v4.5).
  <https://github.com/mitre-attack/attack-navigator/blob/master/layers/LAYERFORMAT.md>
- ATT&CK Navigator (web). <https://mitre-attack.github.io/attack-navigator/>
