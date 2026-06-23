# secure-ml-pipeline · pickle PoC → safetensors + scan + sign + CI gate

A flagship **ML supply-chain** project: show that loading a model file can run
arbitrary code, then build the pipeline that makes that impossible — serialize as
**safetensors**, **statically scan** for dangerous pickle opcodes, **sign +
verify** the artifact, and gate it all in **GitHub Actions that fails closed** on
an unsigned or tampered model.

> **Authorized use only — dual-use.** The "attack" here is a *benign* PoC: the
> payload only writes a marker file (`/tmp/PWNED_DEMO`), and it is only ever
> executed inside a locked-down Docker container (`--network none --read-only`).
> No weaponized pickle is ever committed. Targets are a model I trained myself on
> synthetic data. See [../../ETHICS.md](../../ETHICS.md).

## The problem

`torch.load(...)`, `joblib.load(...)`, `pickle.load(...)` — the default way the ML
world ships models — all run a **pickle**. Pickle is a tiny stack VM, and a few of
its opcodes can import and *call* arbitrary Python at load time:

```
GLOBAL / STACK_GLOBAL   push a named object (e.g. os.system) onto the stack
REDUCE / NEWOBJ / BUILD call it / construct via __reduce__ / __setstate__
```

So a model file downloaded from a hub can own your machine the instant you load
it. This is a real, exploited supply-chain class (Hugging Face nullifyAI,
PyTorch `torchtriton` dependency-confusion, etc.).

The exploit primitive is `__reduce__`: when an object is pickled it can declare
`(callable, args)`, and **unpickling calls that callable**:

```python
class MaliciousModel:
    def __reduce__(self):
        return (_run_marker, ("/tmp/PWNED_DEMO",))   # benign here; os.system in the wild
```

## The fix (defense in depth)

```
              THREAT                                   FIX
   build_poc.py  ──┐                    train TinyMLP ─► model.safetensors  (no code-exec format)
   benign pickle   │  opcode scan  ─►        │                  │
   (REDUCE/GLOBAL) │  (pickle_scan)          ▼                  ▼
   detonate ONLY   │                    pickle_scan + modelscan (optional)
   in Docker  ─────┘                         │                  │
   --network none                            ▼                  ▼
   --read-only                          cosign sign-blob (optional) / local HMAC
                                              │
                                              ▼
                              GitHub Actions gate  ─► FAIL CLOSED on
                                                       unsigned OR tampered artifact
```

1. **safetensors** — a data-only format (8-byte header length + JSON header + raw
   tensor bytes). There is no opcode for "call a function", so loading cannot
   execute code. This alone removes the attack surface.
2. **Static opcode scan** (`pickle_scan.py`) — disassembles pickle bytes with the
   stdlib `pickletools` **without unpickling them** and flags dangerous opcodes /
   known-bad globals. Pure-python, zero deps — the offline stand-in for
   protectai/`modelscan`.
3. **Sign + verify** — Sigstore **cosign** (keyless) if installed; otherwise a
   local HMAC-over-sha256 demo so the *fail-closed* gate still runs offline.
4. **CI gate** (`.github/workflows/model-supply-chain-gate.yml`) — blocks any
   pickled model with exec opcodes and refuses to ship an artifact whose
   signature is missing or invalid.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make run        # train -> safetensors -> scan -> sign/verify gate + figures & metrics.json (OFFLINE-SAFE)
make poc        # build the BENIGN pickle PoC at runtime + opcode-scan it (does NOT execute it)
make detonate   # run the PoC inside a hardened Docker sandbox (skips with a warning if no docker)
make gate       # run the CI gate locally (scan pickles + verify signature)
make test       # fast smoke tests (-m "not slow")
```

**The default `make run` path is fully offline** — it needs only torch, numpy,
scikit-learn, matplotlib (safetensors is used if present, else a pure-python
fallback writes the identical file layout). `modelscan`, `cosign`, and `docker`
are **optional**; each is wired with a graceful, logged SKIP so something always
runs.

> **No GPU needed.** Everything is CPU-only and tiny (a 20→32→2 MLP on synthetic
> data trains in ~1s). Nothing here is GPU-preferred.

Outputs land in [results/](results/):
- `figures/scanner_verdicts.png` — pickle PoC (MALICIOUS, REDUCE/GLOBAL) vs safetensors (clean).
- `figures/integrity_gate.png` — genuine PASS, tampered & unsigned BLOCKED.
- `metrics.json` — committed evidence (scan verdicts, gate correctness, tools present).

## What the result shows

The opcode scanner flags the runtime PoC as **MALICIOUS** (it resolves a `GLOBAL`
and calls it via `REDUCE`) while the safetensors artifact scans **clean** — and
the safetensors round-trip reproduces the weights exactly. The integrity gate is
**correct**: it admits the genuine signed artifact and **fails closed** on both a
byte-flipped (tampered) artifact and a missing signature. In the sandbox,
`pickle.load` on the PoC writes `/tmp/PWNED_DEMO`, proving load == code execution
— which is exactly why the rest of the pipeline ships safetensors and gates on a
signature.

## Interview story (3 sentences)

> I built an end-to-end ML supply-chain demo: a benign pickle PoC whose
> `__reduce__` runs code on load (detonated only inside a `--network none
> --read-only` container), and the fix — safetensors serialization, a stdlib
> pickle-opcode scanner, and a sign/verify CI gate that fails closed on
> unsigned/tampered artifacts. The scanner statically flags `REDUCE`/`GLOBAL`
> without ever unpickling the file, so detection itself isn't an attack surface.
> It maps directly to real incidents (malicious models on public hubs) and to
> SLSA/Sigstore artifact-integrity practice.

## Layout

```
src/secure_ml_pipeline/
    utils.py        set_seed(42) + get_device()->cpu
    model.py        TinyMLP + synthetic data (offline, scikit-learn)
    serialize.py    safetensors save/load (+ pure-python fallback) + sha256
    pickle_scan.py  stdlib pickletools opcode scanner (the offline detector)
    poc.py          builds the BENIGN pickle PoC at runtime (never committed)
    integrity.py    modelscan / cosign wrappers + offline HMAC sign/verify
scripts/
    secure_pipeline.py  the money target -> figures + metrics.json
    build_poc.py        build + opcode-scan the PoC (no execution)
    run_in_docker.sh    detonate the PoC in a hardened container
    ci_gate.py          the gate the GitHub Action calls (fails closed)
docker/                 Dockerfile + detonate.py (the ONLY place that unpickles)
.github/workflows/      model-supply-chain-gate.yml  (committed CI gate)
tests/                  test_smoke.py (fast invariants + one @slow e2e)
results/                figures/*.png + metrics.json  (committed)
data/ models/           git-ignored (synthetic data / produced artifacts)
```

## References

- Trail of Bits — *Never a dill moment: Exploiting machine learning pickle files.*
- protectai/**modelscan** — static scanner for serialized model files.
- Hugging Face — *Pickle scanning* + the **safetensors** format spec.
- **Sigstore cosign** — keyless signing & `sign-blob` / `verify-blob`.
- **SLSA** — Supply-chain Levels for Software Artifacts (provenance / integrity).
- Python docs — `pickle`, `pickletools` (the opcode disassembler we scan with).
