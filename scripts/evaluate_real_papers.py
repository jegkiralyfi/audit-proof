from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.evaluation.real_papers import (
    evaluate_real_paper_case,
    load_real_paper_manifest,
    summarize_real_paper_results,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate real papers from a local manifest.")
    parser.add_argument(
        "--manifest",
        default=str(ROOT / "examples" / "real_papers" / "manifest.template.json"),
        help="Path to a manifest listing local PDF/text files and optional expected labels.",
    )
    parser.add_argument("--provider", default="heuristic")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    cases = load_real_paper_manifest(args.manifest)
    results = [evaluate_real_paper_case(case, llm_provider=args.provider) for case in cases]
    payload = {
        "manifest": args.manifest,
        "provider": args.provider,
        "summary": summarize_real_paper_results(results),
        "cases": results,
        "note": "REAL-PAPER EVALUATION MAY INCLUDE UNLABELED CASES; FP/FN METRICS ARE COMPUTED ONLY FOR LABELED CASES.",
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
