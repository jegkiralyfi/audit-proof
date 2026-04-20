# Evaluation manual

Use the same gold-set fixtures across providers.
Track at least:
- pass / warning / fail distribution
- false positive rate
- false negative rate
- unresolved / error cases
- runtime and timeout behavior

Provider comparisons are only meaningful when prompts, fixtures, and policy versions are pinned.

## Included quant_experimental gold set

This repository now includes a first gold-set fixture pack at:

- `tests/fixtures/gold_sets/quant_experimental/manifest.json`

Run the automated evaluation with:

```bash
python scripts/evaluate_quant_experimental.py --provider heuristic
```

Optional output file:

```bash
python scripts/evaluate_quant_experimental.py --provider heuristic --output .artifacts/evaluations/quant_experimental_heuristic.json
```

## Current scope

The bundled gold set is intentionally small and demonstrative. It is suitable for:
- smoke-testing the evaluation loop
- comparing provider behavior on pinned fixtures
- generating first-pass false positive / false negative metrics

It is **not** yet a publication-grade benchmark.


## Provider-matrix protocol

For certification types with LLM-assisted checks, we run the same pinned gold set against a matrix of providers.
Minimum outputs:
- exact accuracy
- micro false-positive rate
- micro false-negative rate
- per-check breakdown

The current reference command is:

```bash
python scripts/evaluate_provider_matrix.py --providers heuristic,openai-compatible,anthropic,gemini
```

Interpretation rule: a provider may be fast or convenient, but it is not considered deployable for a lane unless it is measured on the pinned gold set.


## Provider profiles and recommendations

The provider-matrix report now includes:
- exported provider profiles
- a current lane recommendation
- profile-level caveats (self-hostability, schema support, auth mode)

Export provider profiles with:

```bash
python scripts/export_provider_profiles.py
```


## Real-paper evaluation

Use `scripts/evaluate_real_papers.py` with a local manifest when you want to move beyond the synthetic pinned gold-set. Separate labeled-case metrics from unlabeled exploratory runs.
