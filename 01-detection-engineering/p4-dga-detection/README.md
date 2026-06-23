# p4 · DGA domain detection (char-level features)

Botnets that use a **Domain Generation Algorithm** spin up thousands of throwaway
domains (`x7k9q2zhf3mn.com`) so their command-and-control survives takedowns. This
project builds a lightweight detector that separates such domains from benign,
human-readable ones using **character-level features** — and shows why the obvious
"high entropy = bad" heuristic is not enough.

**Authorized use only.** Everything here is synthetic data generated in-process
and a model I trained myself. No real domains, feeds, or DNS traffic are touched.
See [../../ETHICS.md](../../ETHICS.md).

## The idea

A domain label carries a surprising amount of signal in its characters alone:

- **Length & Shannon entropy.** Random/hex DGA labels are long and high-entropy:
  `H(s) = -Σ p(c) log₂ p(c)` over the characters `c`.
- **Vowel / digit / consonant ratios.** Pronounceable benign labels have a
  healthy vowel ratio; random DGAs barely any.
- **Character n-grams (2–3).** A TF-IDF over character n-grams captures *transition*
  structure. This is the part that catches the hardest family below.

Three synthetic DGA families (in [src/dga_detection/data.py](src/dga_detection/data.py))
mirror real malware:

| family   | example label            | mirrors        | what gives it away |
|----------|--------------------------|----------------|--------------------|
| `random` | `x7k9q2zhf3mnab`         | Cryptolocker   | high entropy       |
| `hexish` | `a3f9c0d1e4b7...`        | Necurs         | high entropy, hex  |
| `dict`   | `quartzsphinx` (rare words) | Matsnu/Suppobox | **n-grams only** — its entropy looks benign |

The `dict` family is the interesting one: it is built from a *disjoint, rarer*
word pool, so it has the **same length and entropy profile as benign** domains.
Only the character-transition features can tell it apart — which is exactly where
the naive entropy detector fails.

The default detector ([src/dga_detection/model.py](src/dga_detection/model.py)) is a
scikit-learn `LogisticRegression` on `[char n-gram TF-IDF | standardized stats]`.
An `EntropyBaseline` (single threshold on entropy) is included as the strawman.

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make detect            # generate synthetic domains, train, write figures + metrics.json
make test              # fast smoke tests
make lstm              # ALSO train the optional torch char-LSTM and add it to the ROC plot
```

Outputs land in [results/](results/):
- `figures/roc_curve.png` — the **money plot**: the model's ROC vs the entropy baseline.
- `figures/pr_curve.png` — precision-recall for both detectors.
- `figures/entropy_distribution.png` — benign vs DGA entropy histograms with the
  baseline threshold drawn in, making the overlap (dict family) visible.
- `metrics.json` — ROC/PR-AUC, precision/recall, FPR, and **per-family recall**
  (committed as evidence).

**CPU-only.** Everything trains in a few seconds on a laptop. The optional
char-LSTM (`make lstm`) is also CPU-friendly (small embedding + one LSTM layer,
a few epochs) — no GPU required.

## What the result shows

The LogisticRegression reaches **ROC-AUC ≈ 1.00** with ~0% false-positive rate and
catches all three families, including **99.7% of the dict-DGA family**. The naive
entropy baseline only manages **ROC-AUC ≈ 0.96** with an **11% FPR**, and crucially
catches just **~72% of the dict family** — it cannot see past entropy. That gap is
the whole point: good DGA detection is a *features* problem, and character n-grams
are what make the hard, dictionary-based families detectable.

## Interview story (3 sentences)

> I built a DGA-domain detector on character-level features (length, entropy,
> vowel/digit ratios, and char n-grams) and benchmarked it against the common
> "high entropy = malicious" heuristic. To make the comparison honest I generated
> a dictionary-DGA family whose entropy matches benign domains, which the entropy
> baseline misses ~28% of while my n-gram model catches 99.7%. It is a concrete
> demonstration that detection quality lives in feature engineering, not in picking
> a fancier threshold.

## Layout

```
src/dga_detection/  utils.py (seeds) · data.py (synthetic domains) · features.py
                    (entropy + n-grams) · model.py (LogReg + baseline) · lstm.py (optional)
scripts/            run_detection.py  (trains, evaluates, writes figures + metrics.json)
tests/              test_smoke.py  (fast invariants + one @slow end-to-end)
results/            figures/*.png + metrics.json  (committed)
data/ models/       git-ignored (data is synthetic; models are reproduced at runtime)
```

## References

- Yadav et al. *Detecting Algorithmically Generated Malicious Domain Names.* IMC 2010.
- Antonakakis et al. *From Throw-Away Traffic to Bots: Detecting the Rise of DGA-Based Malware.* USENIX Security 2012.
- Woodbridge et al. *Predicting Domain Generation Algorithms with Long Short-Term Memory Networks.* 2016. [arXiv:1611.00791](https://arxiv.org/abs/1611.00791).
- Reference DGA/benign data (optional, not used by default): [Bambenek OSINT feeds](https://osint.bambenek.com/feeds/), [Tranco list](https://tranco-list.eu/).
