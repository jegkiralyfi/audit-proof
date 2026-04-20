# Real-paper evaluation

This repository does **not** bundle copyrighted real papers.

Use this folder to place locally available, open-access, or user-supplied PDF/TXT papers for evaluation.
Then create a manifest (see `manifest.template.json`) and run:

```bash
python scripts/evaluate_real_papers.py --manifest examples/real_papers/manifest.local.json --provider heuristic
```

If you provide `expected` labels for a subset of checks, the evaluator will compute labeled-case FP/FN metrics.
If you do not provide labels, the evaluator will still emit a prediction report, but it will not claim validated accuracy.


A small local text sample is included only to verify the harness end-to-end. Do not count it as a real-paper benchmark.
