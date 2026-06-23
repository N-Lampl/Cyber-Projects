# 05 · ML Supply-Chain Security

Securing the model supply chain — disproportionately hireable for **MLSecOps / AI-security-engineer**
titles, and a project almost no candidates have built.

Authorized use only — see [../ETHICS.md](../ETHICS.md).

## Project

| Project | Build | Status |
|---|---|---|
| `secure-ml-pipeline/` | pickle-RCE PoC → safetensors → ModelScan → Sigstore signing → CI gate | |

## What it demonstrates

1. **The threat:** a pickle-deserialization RCE. The malicious artifact is **built at runtime** by
   `build_poc.py` (never committed) with a deliberately **benign** payload (e.g. `touch /tmp/PWNED`),
   and only ever loaded inside a throwaway container: `docker run --network none --read-only`.
2. **The fix (hardened pipeline):** train → serialize as **safetensors** → scan with `protectai/modelscan`
   → sign & verify with **Sigstore Cosign** → a GitHub Actions gate that **fails closed** on an
   unsigned/tampered artifact.

Hits every 2026 AI-security req (safetensors / ModelScan / Sigstore / SLSA), and the
runtime-PoC + isolated-blast-radius design is itself a strong "I reason about risk" interview story.
