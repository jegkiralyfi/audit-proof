from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.evaluation.goldset import load_gold_manifest
from packages.evaluation.matrix import evaluate_provider_matrix, matrix_markdown_report


def main() -> None:
    parser = argparse.ArgumentParser(description='Evaluate a provider matrix on the quant_experimental gold set.')
    parser.add_argument('--manifest', default=str(ROOT / 'tests' / 'fixtures' / 'gold_sets' / 'quant_experimental' / 'manifest.json'))
    parser.add_argument('--providers', default='heuristic,openai-compatible,anthropic,gemini')
    parser.add_argument('--lane', default='quant_experimental')
    parser.add_argument('--output', default='')
    parser.add_argument('--markdown-output', default='')
    args = parser.parse_args()

    providers = [item.strip() for item in args.providers.split(',') if item.strip()]
    cases = load_gold_manifest(args.manifest)
    payload = evaluate_provider_matrix(providers, cases, lane=args.lane)
    payload['manifest'] = args.manifest
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding='utf-8')
    md = matrix_markdown_report(payload)
    if args.markdown_output:
        md_out = Path(args.markdown_output)
        md_out.parent.mkdir(parents=True, exist_ok=True)
        md_out.write_text(md, encoding='utf-8')
    print(text)
    print('\n---MARKDOWN_REPORT---\n')
    print(md)


if __name__ == '__main__':
    main()
