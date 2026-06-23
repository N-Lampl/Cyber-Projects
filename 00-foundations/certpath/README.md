# certpath · Security+ SY0-701 study plan

A **study-plan artifact** (mostly markdown): map the **CompTIA Security+ SY0-701** exam domains to
the concrete artifacts I'm building across this repo, sequence them into a week-by-week timeline, and
back it with **free** resources (Professor Messer, TryHackMe Pre-Security / SOC Level 1). A tiny
script turns the mapping into a domain-coverage metric.

The plan itself lives in **[certpath.md](certpath.md)**; this README is the run/convention wrapper.

**Authorized use only.** Every lab referenced here runs against models, data, and apps I own or am
licensed to test. See [../../ETHICS.md](../../ETHICS.md).

## The idea

Cert prep usually means rote memorization. Instead, I keep the SY0-701 objectives as a *coverage
checklist* and tie each of the five exam domains to a real build artifact in the repo
([`syllabus.json`](syllabus.json) is the source of truth). A small script reads that mapping and
emits a coverage metric — the fraction of exam domains exercised by at least one artifact — weighted
by each domain's official exam percentage:

```
domain_coverage = (# domains with >=1 repo artifact) / (# domains)
weighted_coverage = sum( weight_d  for each covered domain d )
```

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make coverage     # read syllabus.json -> write results/figures/*.png + results/metrics.json
make test         # fast smoke tests (-m "not slow")
make clean        # remove generated figure + metrics.json
```

Outputs land in [results/](results/):
- `figures/domain_coverage.png` — exam weight per domain, colored by whether it's covered by a repo
  artifact (the "money plot": every domain is green).
- `metrics.json` — domain count, coverage fraction, weighted coverage, and the per-domain map
  (committed as evidence).

## What the result shows

All five SY0-701 domains map to at least one concrete artifact in this repo (**100% coverage**), and
the figure makes the exam's weight distribution obvious — Security Operations (28%) and Threats,
Vulnerabilities & Mitigations (22%) dominate, so the timeline front-loads them. The artifact proves
cert prep and portfolio work are the same effort, not two.

## Interview story (3 sentences)

> I treated the Security+ SY0-701 objectives as a coverage checklist and mapped every exam domain to
> a hands-on artifact in my ML-security portfolio rather than just memorizing terms. A tiny,
> deterministic script reads the domain→module map and emits a coverage metric plus a figure, so I
> can show at a glance that all five domains are exercised by something I actually built. It turned
> cert prep into a build plan and kept the theory anchored to real attacker/defender work.

## Layout

```
README.md            this wrapper
certpath.md          the study plan (primary artifact): map + 10-week timeline + free resources
syllabus.json        domain -> repo-module mapping + official exam weights (source of truth)
scripts/cert_coverage.py  reads syllabus.json -> results/figures/*.png + results/metrics.json
tests/test_smoke.py  fast invariants + one @slow end-to-end run of the script
results/             figures/domain_coverage.png + metrics.json (committed)
```

This project is intentionally light: **no `src/` package and no datasets** — the only code is the
coverage script, which depends solely on the Python standard library + matplotlib (always installed
in this repo), so the default run path works fully offline.

## References

- CompTIA. *Security+ SY0-701 Exam Objectives* (refresh live 2026-07-01).
  <https://www.comptia.org/certifications/security>
- Professor Messer. *SY0-701 CompTIA Security+ Course.* <https://www.professormesser.com/security-plus/sy0-701/>
- TryHackMe. *Pre-Security* and *SOC Level 1* paths. <https://tryhackme.com/>
- MITRE *ATT&CK* (attack.mitre.org) · MITRE *ATLAS* (atlas.mitre.org).
