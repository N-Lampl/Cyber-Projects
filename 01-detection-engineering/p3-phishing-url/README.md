# p3 · Phishing-URL detection (lexical features + sklearn)

Detect phishing URLs from the **string alone** — no DNS, WHOIS, or page fetch. A handful of
cheap, explainable *lexical* features feed a scikit-learn classifier that scores each URL at wire
speed. Runs fully offline on a deterministic synthetic corpus; an optional real-data path
(PhiUSIIL) and an optional char-CNN are one flag away.

**Authorized use only.** Targets are a self-trained model on synthetic / public-research data.
This is a *defensive* detector — do not use it to probe systems you don't own. See
[../../ETHICS.md](../../ETHICS.md).

## The idea

Phishing URLs leave **lexical fingerprints** before you ever resolve them: raw-IP hosts, the `@`
redirect trick, punycode/homograph hosts, brand keywords stuffed into junk domains, suspicious TLDs
(`.tk`, `.zip`, `.xyz`), long hyphenated subdomains, deep paths, and long random query tokens. We
turn each URL into a fixed feature vector and let a linear model learn the boundary:

```
url ──► extract_features() ──► [url_len, n_dots, has_ip_host, has_at,
                                has_punycode, n_subdomains, host_entropy,
                                n_suspicious_words, is_https, ...]  (20 features)
                           ──► StandardScaler ──► LogisticRegression ──► P(phishing)
```

The 20 features live in [src/phishing_url/features.py](src/phishing_url/features.py); the model is a
StandardScaler + LogisticRegression pipeline ([src/phishing_url/model.py](src/phishing_url/model.py))
so its coefficients are directly readable as "which signals push toward phishing."

Because no labeled corpus ships in the repo, [src/phishing_url/data.py](src/phishing_url/data.py)
**generates** benign-looking and phishing-looking URLs from controllable distributions (with class
overlap, so the task isn't trivial). Same `--seed` ⇒ identical data and metrics.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make detect                          # SYNTHETIC URLs -> lexical features -> logreg; writes figures + metrics.json
make detect ARGS="--model rf"         # RandomForest instead of logistic regression
make test                            # fast smoke tests

# OPTIONAL enhanced paths (extra installs):
pip install ucimlrepo
make detect ARGS="--data phiusiil"    # train/eval on the real PhiUSIIL dataset (UCI id 967)
pip install torch
make detect ARGS="--model cnn"        # char-level CNN over raw URL strings (torch)
```

Outputs land in [results/](results/):
- `figures/roc_curve.png` — the **money plot**: TPR vs FPR with the AUC.
- `figures/feature_importance.png` — signed logreg weights (red = pushes phishing, blue = benign).
- `metrics.json` — accuracy / precision / recall / F1 / ROC-AUC + top features (committed as evidence).

## What the result shows

On the held-out synthetic set the lexical detector reaches **ROC-AUC ≈ 0.994** (accuracy ≈ 97%) — a
tiny, transparent model with no network calls cleanly separates phishing-looking from benign-looking
URLs even though ~10–12% of each class is deliberately built to overlap, and the
feature-importance plot shows the model leaning on exactly the human "tells" (`@`, IP hosts,
suspicious TLDs, brand-stuffed subdomains). Synthetic AUC is optimistic by construction; the
PhiUSIIL flag exists to show the same pipeline on messier real URLs.

## Interview story (3 sentences)

> I built a phishing-URL detector that scores URLs from the string alone using ~20 explainable
> lexical features and a logistic-regression model, so it needs no DNS/WHOIS lookups and runs at
> wire speed. To keep it reproducible and offline I wrote a synthetic URL generator that encodes the
> known phishing "tells," and the model recovers them as its top weights — detection plus built-in
> explainability. The same feature pipeline drops straight onto the real PhiUSIIL dataset or a
> char-CNN with a single flag, which is how I'd harden it for production traffic.

## Layout

```
src/phishing_url/  utils.py (seeds) · data.py (synthetic + PhiUSIIL) · features.py (lexical)
                   model.py (sklearn pipeline) · char_cnn.py (optional torch)
scripts/           detect.py  (train + ROC/feature figures + metrics.json)
tests/             test_smoke.py  (fast invariants + one @slow end-to-end)
results/           figures/*.png + metrics.json  (committed)
data/ models/      git-ignored (synthetic in-memory by default)
```

## References

- Ma, Saul, Savage, Voelker. *Beyond Blacklists: Learning to Detect Malicious Web Sites from
  Suspicious URLs.* KDD 2009.
- Sahingoz, Buber, Demir, Diri. *Machine learning based phishing detection from URLs.* Expert
  Systems with Applications, 2019.
- Prasad & Chandra. *PhiUSIIL: A diverse security profile empowered phishing URL detection
  framework.* Computers & Security, 2024. UCI ML Repository id 967 (CC BY 4.0).
