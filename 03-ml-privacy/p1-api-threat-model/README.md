# p1 · Threat-modeling a model-serving API (and building the controls)

Most ML-serving demos expose a raw `/predict` with no auth, no limits, and no logging — a
gift to anyone who wants to scrape your model, DoS it, or crash it with a malformed body.
This project does the opposite: a small **model-serving endpoint hardened with four
security controls**, each tied to a row in an explicit threat model, and each proven by an
**abuse test**.

**Authorized use only.** The "target" is a model and endpoint I run myself on synthetic
data, exercised in-process. The abuse tests here are run against my own service, never a
third party. See [../../ETHICS.md](../../ETHICS.md). Threat-modeling background lives in
[../../00-foundations](../../00-foundations) (see `module-2-stride-ml`).

## The idea

Take a normal `/predict` endpoint and wrap it in a request pipeline where every stage is a
named control. The order matters — cheap, security-critical checks first:

```
request ─▶ [1 auth] ─▶ [2 rate limit] ─▶ [3 input validation] ─▶ [4 inference] ─▶ 200
              │401           │429              │422                    │
              ▼              ▼                 ▼                       ▼
            ────────────────  audit log (every outcome recorded)  ────────────
```

| # | Control | Threat (STRIDE / OWASP-API) | Implementation |
|---|---------|------------------------------|----------------|
| 1 | **API-key auth** | Spoofing · Broken auth (API2) | salted **SHA-256** of the key, **constant-time** compare; raw key never stored → `401` |
| 2 | **Token-bucket rate limit** | DoS (API4) · model extraction by scraping | per-principal bucket, `capacity` tokens, refill `r/s`; empty → `429` |
| 3 | **Input validation** | Injection / malformed-input crash (API8) · resource exhaustion | strict type / shape / finiteness / range / **batch-size** checks → `422` |
| 4 | **Audit log** | Repudiation · insufficient logging (API9) | in-memory ring buffer of every auth / rate / predict outcome |

The logic lives in [`src/api_threat_model/security.py`](src/api_threat_model/security.py)
and [`service.py`](src/api_threat_model/service.py), **independent of any web framework**, so
the *same* code (and the same tests) back two transports:

- **Default (offline) transport:** Python's stdlib `http.server` — zero extra deps.
- **Optional transport:** **FastAPI + uvicorn**, imported lazily so the package still
  imports when they are absent.

The served model itself is deliberately trivial — a scikit-learn `LogisticRegression` on
synthetic tabular data — because the subject is the *controls around* the model.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make demo            # run the abuse-test suite -> results/figures/*.png + metrics.json
make test            # fast smoke tests (-m "not slow")

make serve           # run the hardened endpoint (stdlib transport, NO fastapi needed)
make serve-fastapi   # optional FastAPI/uvicorn transport (pip install fastapi uvicorn)
```

Try it once it's serving (default port 8077):

```bash
# missing key -> 401
curl -s -X POST localhost:8077/predict -H 'content-type: application/json' \
     -d '{"instances": [[0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8]]}'
# valid -> 200 with class + probabilities
curl -s -X POST localhost:8077/predict -H 'x-api-key: demo-secret-key' \
     -H 'content-type: application/json' \
     -d '{"instances": [[0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8]]}'
```

Outputs land in [results/](results/):
- `figures/controls_coverage.png` — abuse cases **blocked / total** per control.
- `figures/rate_limit_bucket.png` — the token bucket draining to `429`, then refilling.
- `metrics.json` — controls inventory + the full abuse-test result table (committed).

## What the result shows

The abuse suite runs **12 cases** spanning all four controls and **12/12 are blocked as
expected**: missing/wrong keys are rejected (`401`), a burst of 10 requests against a
capacity-5 bucket yields exactly 5 × `200` then 5 × `429` (and recovers after the bucket
refills), six classes of malformed body are rejected (`422`) — including an oversized-batch
DoS attempt and a `NaN` that would otherwise reach the model — and every denial is written
to the audit log (non-repudiation). The point: the security posture is a property of the
*pipeline*, not the framework, so it's identical whether you serve via stdlib or FastAPI.

## Interview story (3 sentences)

> I threat-modeled a model-serving endpoint with STRIDE/OWASP-API in mind and built the
> four controls that close the top gaps — API-key auth with constant-time hashed compares,
> a per-principal token-bucket rate limiter (which also blunts model-extraction scraping),
> strict input validation, and an audit log — as framework-agnostic components. I proved
> each one with an abuse-test suite (12/12 blocked) that runs against both a dependency-free
> stdlib server and an optional FastAPI transport sharing the exact same logic. It shows I
> treat an ML endpoint as an attack surface, not just a function call.

## Layout

```
src/api_threat_model/  utils.py (seeds) · model.py (sklearn target) · security.py (controls)
                       service.py (pipeline) · stdlib_server.py (default) · app.py (FastAPI)
scripts/               run_abuse_tests.py (the money target) · serve.py
tests/                 test_smoke.py  (fast invariants + one @slow FastAPI TestClient test)
results/               figures/*.png + metrics.json  (committed)
data/ models/          synthetic / in-memory; nothing committed (git-ignored)
```

## References

- OWASP **API Security Top 10** (2023) — API2 broken auth, API4 unrestricted resource
  consumption, API8 misconfiguration/injection, API9 improper inventory/logging.
- OWASP **Machine Learning Security Top 10** — ML05 model theft / extraction.
- MITRE **ATLAS** — *Exfiltration via ML Inference API* (model extraction).
- Token-bucket algorithm — classic traffic-shaping primitive (see e.g. Tanenbaum,
  *Computer Networks*).
