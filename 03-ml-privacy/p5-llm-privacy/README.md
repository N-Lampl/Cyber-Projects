# p5 · LLM training-data memorization (canary exposure)

Language models don't just *learn* their training data — they sometimes **memorize** it
verbatim, including secrets. This project plants known "canary" secrets in a corpus, trains
a tiny char-level LM on it, and then **measures the leak** with the *Secret Sharer* canary
**exposure** metric — a perplexity-based membership test. No training data is needed beyond a
synthetic corpus we generate ourselves, so the whole thing runs offline on CPU in ~70s.

**Authorized use only.** The target is a model I train myself on synthetic data; the
optional GPT-2 path uses public weights / your own fine-tune. See [../../ETHICS.md](../../ETHICS.md).

## The idea

A **canary** is a phrase with a high-entropy secret slot:

```
user alice secret code is 8401739265
                          ^^^^^^^^^^ secret: 10 random digits  ->  |R| = 10^10 candidates
```

If the model *memorized* the canary, the **real** secret should be far more likely (lower
perplexity) than random alternatives drawn from the same space. We quantify this with
**exposure** (Carlini et al., 2019):

```
exposure(s) = log2(|R|) - log2( rank of s among all |R| candidates, by perplexity )
```

- rank 1 (most likely of all 10^10) ⇒ exposure = log2(|R|) ≈ **33.2 bits** (max leak).
- rank ≈ |R|/2 (model has no preference) ⇒ exposure ≈ **1 bit** (no memorization).

We can't perplexity-rank 10^10 strings, so we use the paper's distributional estimate: sample
N random secrets, fit a normal to their perplexities, and read off where the real secret falls
(`rank = |R| · P(perp < perp_real)`). The whole detector is in
[src/llm_privacy/exposure.py](src/llm_privacy/exposure.py); the per-string membership signal is just
teacher-forced log-perplexity:

```python
log_probs = torch.log_softmax(model(x)[0], dim=-1)
token_ll  = log_probs.gather(-1, y[..., None]).squeeze(-1)
log_perplexity = -token_ll.mean()      # lower = the model finds this string more likely
```

## Run it

```bash
# from this folder; uses uv if installed, else system python3
make detect            # build corpus + train tiny char-LM + measure exposure + write figures & metrics.json
make test              # fast smoke tests

# tune the experiment:
make detect ARGS=...   # or: python scripts/detect_memorization.py --canary-repeats 32 --epochs 12
```

`--canary-repeats` is the dial that matters: the more times a secret appears in training, the
more it gets memorized, and the higher its exposure.

Outputs land in [results/](results/):
- `figures/exposure_by_canary.png` — exposure (bits) per inserted secret vs. the 33-bit max and
  the ~1-bit baseline.
- `figures/perplexity_distribution.png` — the **money plot**: the real secret sitting far in the
  left tail vs. the bell of 2,000 random alternatives.
- `metrics.json` — exposure per canary, the control, ranks, perplexities (committed as evidence).

### Optional enhanced path (GPT-2, opt-in)

`scripts/gpt2_exposure.py` runs the same exposure idea against a real **GPT-2**
(`pip install "transformers>=4.40"`; downloads ~500MB). `transformers` is imported lazily, so the
default path works without it. Stock GPT-2 shows ~baseline exposure for a fresh secret;
fine-tune it on a corpus containing the secret to watch exposure climb.

## What the result shows

On the committed run (4 canaries inserted 16× each, 10 epochs):

| canary | exposure (bits) | est. rank in 10^10 |
|--------|-----------------|--------------------|
| grace  | **22.3** | ~1,970 |
| judy   | **21.8** | ~2,721 |
| dave   | 18.2 | ~33,090 |
| frank  | 17.3 | ~63,933 |
| *control (never inserted)* | **1.1** | ~baseline |

Inserted secrets reach **~18–22 of a possible 33 bits** of exposure — out of 10 *billion*
candidate secrets, the model ranks the true one in the **top few thousand**. A never-inserted
control secret sits at ~1 bit (baseline), confirming the signal is memorization, not an artifact.
This is exactly how real LLMs leak PII, API keys, and copyrighted text from their training sets.

## Interview story (3 sentences)

> I planted high-entropy "canary" secrets in a training corpus, trained a small LM on it, then
> implemented the Secret Sharer **exposure** metric to prove the model memorized them — ranking the
> true 10-digit secret in the top few thousand out of 10 billion candidates (~22 of 33 bits),
> versus ~1 bit for a never-inserted control. The detector is just a perplexity-based membership
> test, the same primitive behind membership-inference and training-data-extraction attacks on real
> LLMs. It makes concrete *why* memorization is a privacy risk and sets up defenses like
> deduplication and DP-SGD (track 03).

## Layout

```
src/llm_privacy/  utils.py (seeds) · corpus.py (synthetic + canaries) · model.py (CharLM GRU)
                  train.py · exposure.py (the perplexity membership test + exposure metric)
scripts/          detect_memorization.py (default) · gpt2_exposure.py (optional GPT-2)
tests/            test_smoke.py  (fast invariants + one @slow end-to-end)
results/          figures/*.png + metrics.json  (committed)
data/ models/     git-ignored (corpus is synthetic; weights produced at runtime)
```

## References

- Carlini, Liu, Erlingsson, Kos, Song. *The Secret Sharer: Evaluating and Testing Unintended
  Memorization in Neural Networks.* USENIX Security 2019.
  [arXiv:1802.08232](https://arxiv.org/abs/1802.08232).
- Carlini et al. *Extracting Training Data from Large Language Models.* USENIX Security 2021.
  [arXiv:2012.07805](https://arxiv.org/abs/2012.07805).
- Shokri et al. *Membership Inference Attacks Against Machine Learning Models.* IEEE S&P 2017.
  [arXiv:1610.05820](https://arxiv.org/abs/1610.05820).
