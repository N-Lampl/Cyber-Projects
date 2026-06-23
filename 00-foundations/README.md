# 00 · Security Foundations

The security half of the pivot, built as **artifacts** (not just reading). Every other track links
back here instead of re-teaching threat modeling or the frameworks. Substantial but modular.

Authorized use only — see [../ETHICS.md](../ETHICS.md).

## Modules

| Module | Build | Status |
|---|---|---|
| `module-1-attack-atlas/` | MITRE ATT&CK + **ATLAS** primer; the **canonical ATT&CK/ATLAS Navigator layer** reused by every track | |
| `module-2-stride-ml/` | STRIDE threat model of an ML inference service (data-flow diagram via Threat Dragon + `pytm`) | |
| `module-3-network-labs/` | TCP/IP, HTTP, DNS, TLS mini-labs with pcap analysis (Wireshark / `scapy`) | |
| `module-4-web-appsec/` | OWASP Top 10 break-and-fix against **OWASP Juice Shop** in Docker | |
| `module-5-crypto-lab/` | Hashing, AES/RSA, signatures, and misuse demos (ECB penguin, unsalted hashes) | |
| `certpath.md` | **Security+ SY0-701** domains mapped to modules + TryHackMe/HTB rooms + a timeline | |

## Why this is first

The gap between "data scientist" and "security professional" is security vocabulary and the attacker
mindset — not ML. Build the shared Navigator layer + the reusable `AUTHORIZATION.md` template here in
Phase 0 so the rest of the repo references one source of truth.

**Cert anchor:** Security+ SY0-701 (Professor Messer free course + official objectives; refreshed
objectives go live 2026-07-01). TryHackMe Pre-Security → SOC Level 1 for hands-on.
