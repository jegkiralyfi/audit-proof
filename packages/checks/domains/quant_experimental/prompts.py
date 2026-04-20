from __future__ import annotations

from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PROMPTS_DIR = ROOT / "prompts" / "quant_experimental"


class PromptNotFoundError(FileNotFoundError):
    pass


@lru_cache(maxsize=32)
def load_prompt_template(name: str) -> str:
    filename = name if name.endswith(".md") else f"{name}.md"
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise PromptNotFoundError(f"Quant-experimental prompt template not found: {filename}")
    return path.read_text(encoding="utf-8").strip()


def available_prompt_templates() -> list[str]:
    return sorted(path.name for path in PROMPTS_DIR.glob("*.md"))
