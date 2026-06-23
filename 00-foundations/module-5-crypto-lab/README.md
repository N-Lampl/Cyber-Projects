# module 5 · crypto lab — basics & misuse demos

Hands-on cryptography for the foundations track: the primitives you *should*
reach for, side by side with the classic ways they get misused. Four mini-demos
in one runnable lab — **salted vs unsalted hashing**, **AES-GCM (good) vs
AES-ECB (the penguin, bad)**, **RSA**, and **digital signatures**.

The default path uses **only the standard library + numpy/matplotlib** — it
ships a compact pure-Python AES-128 and a textbook-RSA so nothing third-party is
needed. If the `cryptography` library happens to be installed, the lab
*additionally* exercises the real authenticated/padded primitives (AES-GCM,
RSA-OAEP, RSA-PSS).

**Authorized use only.** Every key, hash, and ciphertext here is generated
locally over synthetic data; there are no real secrets, accounts, or networks.
The toy AES/RSA are for *learning only* — never use them for anything real. See
[../../ETHICS.md](../../ETHICS.md).

## The ideas

**1. Salted hashing.** Unsalted `H(password)` is deterministic, so reused
passwords collide and one precomputed *rainbow table* `digest -> password`
cracks every matching account at once. A per-user random salt makes
`H(salt ‖ password)` unique, so the attacker's table is worthless. (Even
salted SHA-256 is too *fast* for real password storage — use a slow KDF; we
include a `pbkdf2_hash` helper to show the right primitive.)

**2. AES-ECB vs AES-GCM — the penguin.** ECB encrypts each 16-byte block
independently:

```
C_i = E_k(P_i)      => identical plaintext blocks give identical ciphertext blocks
```

Encrypt an image with flat regions and the silhouette survives the encryption.
GCM adds a random 96-bit nonce and chains state, so equal plaintext blocks
produce unrelated ciphertext — and it *authenticates*, so tampering is detected.

**3. RSA + signatures.** `n = p·q`, `e = 65537`, `d = e⁻¹ mod φ(n)`.
Encrypt `c = mᵉ mod n`, decrypt `m = cᵈ mod n`. Signing flips the keys:
`s = H(msg)ᵈ mod n`, and anyone verifies with `sᵉ mod n == H(msg)`. A modified
message no longer matches the signature.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make run     # all four demos -> results/figures/*.png + results/metrics.json
make test    # fast smoke tests (-m "not slow")
make run     # re-run anytime; deterministic image, fresh random keys
```

Default run needs only numpy + matplotlib. For the enhanced (real-crypto) path:

```bash
pip install -r requirements.txt   # adds `cryptography` + Pillow
make run                          # now also runs AES-GCM / RSA-OAEP / RSA-PSS
```

Outputs land in [results/](results/):
- `figures/ecb_penguin.png` — the **money plot**: plaintext, ECB (outline leaks),
  and GCM (noise) side by side.
- `figures/hash_salt_demo.png` — accounts cracked by one rainbow table, unsalted
  vs salted.
- `metrics.json` — block-uniqueness, crack counts, signature/forgery results.

## What the result shows

One rainbow table cracked **15/15** unsalted accounts and **0** salted ones. The
ECB ciphertext kept the *exact* block-uniqueness of the plaintext (0.076) — the
penguin is plainly visible — while GCM ciphertext hit uniqueness 1.0 (pure
noise) and detected a single flipped byte. RSA round-tripped and its signature
rejected a tampered message. Same data, same key — the *mode* and the *salt* are
the whole ballgame.

## Interview story (3 sentences)

> I built a small crypto lab that puts good primitives next to their classic
> misuses: salted vs unsalted password hashing, and AES-GCM vs the AES-ECB
> "penguin" where the image outline survives encryption. I implemented AES-128
> and textbook RSA from scratch for a zero-dependency default path, then wired an
> optional path to the real `cryptography` library (GCM/OAEP/PSS) behind lazy
> imports. It made concrete *why* mode of operation, salting, and padding are
> security-critical rather than implementation trivia.

## Layout

```
src/crypto_lab/  utils.py (seeds) · hashing.py · aes.py (pure-Py AES + GCM) ·
                 asymmetric.py (textbook RSA + OAEP/PSS) · image.py (penguin)
scripts/         run_crypto_lab.py   (produces figures + metrics.json)
tests/           test_smoke.py       (fast invariants + one @slow end-to-end)
results/         figures/*.png + metrics.json  (committed)
data/ models/    no datasets/keys persisted (synthetic, runtime-generated)
```

## References

- Goldberg & co., *ECB Penguin* — Wikipedia, "Block cipher mode of operation"
  (the canonical Tux/ECB demonstration).
- NIST SP 800-38A (modes incl. ECB/CBC) and SP 800-38D (GCM).
- NIST SP 800-132 (PBKDF2) · OWASP Password Storage Cheat Sheet.
- Rivest, Shamir, Adleman. *A Method for Obtaining Digital Signatures and
  Public-Key Cryptosystems.* CACM 1978. · PKCS#1 v2.2 (RSA-OAEP / RSA-PSS).
- Python `cryptography` library docs (hazmat: AESGCM, RSA OAEP/PSS).
```
