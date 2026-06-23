# certpath · Security+ SY0-701 → repo modules

A study-plan artifact: map every **CompTIA Security+ SY0-701** exam domain to the concrete
**artifacts I'm building in this repo**, then sequence it into a week-by-week timeline backed by
**free** resources. The point is to learn security by *building*, with the cert as the checklist that
proves coverage.

> The source of truth for the mapping is [`syllabus.json`](syllabus.json). `make coverage` reads it
> and emits [`results/metrics.json`](results/metrics.json) + a coverage figure, so this page and the
> metrics never drift.

**Authorized use only.** Every lab here runs against models, data, and apps I own or am licensed
to test. See [../../ETHICS.md](../../ETHICS.md).

---

## Domain → module map

Official SY0-701 domains and their exam weights, each tied to repo artifacts that exercise it.

| # | Domain | Weight | Repo artifacts | ML-security tie-in |
|---|--------|:---:|---|---|
| 1.0 | General Security Concepts | 12% | `module-1-attack-atlas`, `module-5-crypto-lab` | ATT&CK/ATLAS vocabulary; crypto used for model signing (track 05 Sigstore) |
| 2.0 | Threats, Vulnerabilities & Mitigations | 22% | `module-2-stride-ml`, `module-4-web-appsec`, `01-detection-engineering` | STRIDE threat model of an ML service; OWASP Top 10 break/fix; detection-as-code is mitigation |
| 3.0 | Security Architecture | 18% | `module-2-stride-ml`, `module-3-network-labs`, `05-ml-supply-chain` | Secure ML pipeline architecture; TLS/DNS labs; training-data protection |
| 4.0 | Security Operations | 28% | `module-3-network-labs`, `01-detection-engineering`, `04-llm-security` | Detection engineering on telemetry; LLM red-team CI gate as SecOps automation |
| 5.0 | Security Program Management & Oversight | 20% | `ETHICS.md`, `module-1-attack-atlas` | Governance/authorized-use posture; threat-informed prioritization |

Weights sum to 100%. **Domain 4.0 (Security Operations) is the heaviest at 28%** — and the most
ML-adjacent, so it gets the most lab time.

---

## Week-by-week timeline (10 weeks)

Roughly 8–10 hrs/week: ~half watching Professor Messer + reading the official objectives, ~half
doing TryHackMe rooms and building the corresponding repo module. Order follows the domains but
front-loads the high-weight, high-overlap material.

| Wk | Focus (domain) | Professor Messer | TryHackMe | Repo deliverable |
|---|---|---|---|---|
| 1 | 1.0 General Concepts | 1.1–1.4 (controls, CIA, zero trust) | Pre-Security: Intro path | Start `module-1-attack-atlas` (ATT&CK + ATLAS primer) |
| 2 | 1.0 Crypto | 1.4 (PKI, hashing, signing) | Cryptography rooms | `module-5-crypto-lab` (hashing, AES/RSA, ECB-penguin demo) |
| 3 | 2.0 Threats | 2.1–2.3 (actors, attack surfaces) | SOC L1: Cyber Defense Frameworks | Finish `module-1-attack-atlas` Navigator layer |
| 4 | 2.0 Vulns & web | 2.3–2.5 (app/web vulns) | OWASP Top 10 / Juice Shop room | `module-4-web-appsec` break-and-fix |
| 5 | 2.0 Mitigations | 2.5 (hardening, segmentation) | SOC L1: Phishing | `module-2-stride-ml` data-flow diagram (pytm) |
| 6 | 3.0 Architecture | 3.1–3.3 (cloud, IaC, resilience) | SOC L1: Network Security | `module-3-network-labs` TCP/IP + TLS pcap lab |
| 7 | 3.0 Data protection | 3.3–3.4 (data states, DLP) | Networking rooms | Sketch `05-ml-supply-chain` secure-pipeline architecture |
| 8 | 4.0 SecOps (heavy) | 4.1–4.5 (monitoring, IR) | SOC L1: SIEM / Incident Response | Wire `01-detection-engineering` baseline detector |
| 9 | 4.0 SecOps + forensics | 4.6–4.9 (IR, forensics, automation) | SOC L1: Digital Forensics | `04-llm-security` red-team CI gate concept |
| 10 | 5.0 Governance + review | 5.1–5.6 (GRC, audits, awareness) | SOC L1 capstone challenge | Polish `ETHICS.md`; full practice exam; book test |

**Buffer:** weeks 11–12 for two timed practice exams (Messer's free practice + the official sample
questions) and re-watching any domain scoring < 80%.

---

## Free resources

- **Professor Messer — SY0-701 course** (free videos + study group): the spine of the theory.
  <https://www.professormesser.com/security-plus/sy0-701/sy0-701-video/sy0-701-comptia-security-plus-course/>
- **CompTIA official SY0-701 exam objectives** (free PDF) — the authoritative checklist; refreshed
  objectives go live **2026-07-01**. <https://www.comptia.org/certifications/security>
- **TryHackMe — Pre-Security** path (free): networking + web + Linux fundamentals.
  <https://tryhackme.com/path/outline/presecurity>
- **TryHackMe — SOC Level 1** path: hands-on detection, SIEM, IR — directly feeds Domain 4.0.
  <https://tryhackme.com/path/outline/soclevel1>
- **MITRE ATT&CK** <https://attack.mitre.org/> and **MITRE ATLAS** <https://atlas.mitre.org/> — the
  frameworks the whole repo references.

---

## How to run

```bash
# from this folder; uses uv if installed, else system python3
make coverage     # read syllabus.json -> write results/metrics.json + coverage figure
make test         # fast smoke tests (validates the mapping is well-formed)
make clean        # remove generated figure + metrics.json
```

## What the result shows

`make coverage` confirms **all five SY0-701 domains map to at least one concrete repo artifact**
(100% domain coverage) and visualizes how the exam's weight is distributed against where I'm
spending build effort — making the heavy Security Operations (28%) and Threats (22%) domains the
obvious priorities.

## Interview story (3 sentences)

> I treated the Security+ SY0-701 objectives as a coverage checklist and mapped every domain to a
> hands-on artifact in my ML-security portfolio instead of just memorizing terms. A tiny script
> reads the domain→module map and emits a coverage metric, so I can prove at a glance that all five
> domains are exercised by something I actually built. It turned cert prep into a build plan and
> kept the theory anchored to real attacker/defender work.

## Layout

```
certpath.md           this study plan (the primary artifact)
syllabus.json         domain -> repo-module mapping + exam weights (source of truth)
scripts/cert_coverage.py  reads syllabus.json -> results/metrics.json + figure
tests/test_smoke.py   validates the mapping (weights sum to 1, every domain mapped)
results/              figures/domain_coverage.png + metrics.json (committed as evidence)
```

## References

- CompTIA. *Security+ SY0-701 Exam Objectives.* CompTIA, 2023 (refresh 2026-07-01).
- Professor Messer. *SY0-701 CompTIA Security+ Course.* professormesser.com.
- MITRE. *ATT&CK* (attack.mitre.org) and *ATLAS* (atlas.mitre.org).
