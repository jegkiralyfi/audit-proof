from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.evaluation.goldset import load_gold_manifest, evaluate_case, summarize_results


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate quant_experimental gold set.")
    parser.add_argument("--manifest", default=str(ROOT / "tests" / "fixtures" / "gold_sets" / "quant_experimental" / "manifest.json"))
    parser.add_argument("--provider", default="heuristic")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    cases = load_gold_manifest(args.manifest)
    results = [evaluate_case(case, llm_provider=args.provider) for case in cases]
    summary = summarize_results(results)
    payload = {
        "manifest": args.manifest,
        "provider": args.provider,
        "summary": summary,
        "cases": results,
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding='utf-8')
    print(text)


if __name__ == "__main__":
    main()
