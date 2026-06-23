# module-4 · OWASP Top 10 break-and-fix lab (vs Juice Shop)

Foundations of web application security: stand up **OWASP Juice Shop** locally, then *break it*
with small dependency-free Python scripts across five OWASP Top 10 (2021) categories — and write
the **fix** for each. Every exploit also runs **offline** against a deterministic mock, so the
logic is provable in CI with no docker.

**Authorized use only.** The target is a deliberately-vulnerable app **you run yourself** on
`127.0.0.1`. The scripts refuse non-local hosts unless you explicitly opt in. Never test a system
you do not own. See [../../ETHICS.md](../../ETHICS.md).

## The idea

OWASP Juice Shop is the canonical intentionally-insecure web app. This lab treats it as a target
and walks the most instructive Top 10 categories with reproducible Python probes. Each probe sends
the exploit, asserts the vulnerable behaviour, and records a **finding + remediation**:

| OWASP (2021) | Probe | What breaks | One-line fix |
|---|---|---|---|
| **A03 Injection** | `sqli_login_bypass` | `email = ' OR 1=1--` logs you in as admin | parameterised queries |
| **A03 Injection** | `reflected_xss_search` | `q=<iframe ...>` echoed unescaped into HTML | output-encode + CSP |
| **A01 Broken Access Control** | `idor_basket` | read another user's basket via `/rest/basket/{id}` | object-level authz check |
| **A05 Security Misconfig** | `exposed_ftp_listing` | `/ftp/` lists `*.bak` / config files | disable dir listing, move secrets |
| **A07 Auth Failures** | `forged_jwt_none_alg` | mint an admin JWT via `alg=none` / weak secret | pin alg, strong key, verify claims |

### The SQLi auth bypass, concretely

Juice Shop concatenates the login email straight into SQL:

```
SELECT * FROM Users WHERE email = '<email>' AND password = '<hash>'
```

Send `email = "' OR 1=1--"` and the clause becomes `email = '' OR 1=1` with the password check
**commented out** — the query returns the first row (admin), and the app authenticates as them.

## Run it

```bash
# from this folder; uses uv if installed, else system python3

make lab                 # DEFAULT: offline mock, no docker — runs all 5 probes, writes results
make test                # fast smoke tests (the real exploit logic, vs the mock)

# Against the real container (optional, needs docker):
make up                  # docker compose up Juice Shop on 127.0.0.1:3000
make lab ARGS=--live     # run the identical probes against the live container
make down                # tear it down
```

Outputs land in [results/](results/):
- `findings.json` — one structured finding per probe (payload, evidence, severity, fix).
- `metrics.json` — dashboard-friendly summary (categories covered, confirmed counts, severity).
- `figures/findings_by_severity.png` — confirmed findings bar chart.

## What the result shows

The default offline run confirms **5/5** probes across **4** OWASP Top 10 categories — two
critical (SQLi auth bypass, forged admin JWT), two high (reflected XSS, IDOR), one medium
(exposed `/ftp/`). The point of the lab is the second half of every finding: a concrete,
named remediation, so it doubles as a *fix* reference, not just an attack collection. Running
`--live` against the container reproduces the same findings on the actual app.

## Interview story (3 sentences)

> I built a break-and-fix lab against OWASP Juice Shop that exploits five Top 10 categories —
> SQLi auth bypass, reflected XSS, IDOR, security misconfiguration, and a forged `alg=none` JWT —
> with small dependency-free Python scripts and a hard authorization guardrail that refuses
> non-local targets. Each finding pairs the working exploit with a specific remediation, and the
> whole suite runs offline against a deterministic mock so CI proves the exploit logic with no
> docker. It grounds my ML-security work in classic web appsec: the same access-control and
> input-handling failures show up in model-serving APIs and agent tools.

## Layout

```
docker-compose.yml          Juice Shop pinned to v17.1.1, bound to 127.0.0.1 only
src/juiceshop_lab/          utils.py (set_seed, require_local_target) · client.py (HttpClient + MockJuiceShop) · exploits.py (5 probes)
scripts/run_lab.py          runs probes -> results/findings.json + metrics.json + figure
tests/test_smoke.py         fast exploit-logic tests + one @slow end-to-end
results/                    findings.json + metrics.json + figures/*.png  (committed)
data/ models/               git-ignored (no dataset / no models — see their READMEs)
```

## References

- OWASP Juice Shop — https://owasp.org/www-project-juice-shop/ (project) ·
  https://pwning.owasp-juice.shop/ (companion guide).
- OWASP Top 10:2021 — https://owasp.org/Top10/.
- OWASP Cheat Sheet Series (SQLi, XSS, Authorization, JWT) — https://cheatsheetseries.owasp.org/.
