# Real-paper evaluation

The bundled gold-set is **synthetic** and exists to provide a pinned, reproducible baseline for automated regression testing.

To demonstrate real-paper behavior, use the `scripts/evaluate_real_papers.py` harness with **local, open-access, or user-supplied PDFs/TXT files** listed in a manifest.

Important constraints:
- This repository does not ship copyrighted real papers.
- Unlabeled real-paper runs are **demonstrations**, not validated accuracy claims.
- FP/FN metrics should only be reported on cases that have explicit human labels.

Recommended workflow:
1. Assemble 5–10 local open-access papers for the target certification type.
2. Create a manifest using `examples/real_papers/manifest.template.json`.
3. Add labels for a subset of checks where a human reviewer can adjudicate the expected outcome.
4. Run `scripts/evaluate_real_papers.py`.
5. Report labeled-case metrics separately from unlabeled exploratory runs.


The bundled `sample_local_paper.txt` exists only so the harness can be exercised in CI/development. It must not be presented as evidence that the system has been evaluated on a meaningful corpus of real papers.
