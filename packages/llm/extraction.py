from __future__ import annotations

from packages.core.models import ParsedDocument


def select_excerpt(
    document: ParsedDocument,
    preferred_sections: list[str],
    *,
    match_scope: str = "preferred",
    max_chars: int = 4000,
) -> tuple[str, str]:
    preferred = {name.strip().lower() for name in preferred_sections if name}
    if match_scope == "full_text" or not preferred:
        text = document.raw_text[:max_chars]
        return "full_text", text

    chunks: list[str] = []
    chosen_names: list[str] = []
    for section in document.sections:
        if section.name.strip().lower() in preferred:
            chosen_names.append(section.name)
            chunks.append(section.text)
    if not chunks:
        return "full_text", document.raw_text[:max_chars]
    text = "\n\n".join(chunks)[:max_chars]
    label = ", ".join(chosen_names[:3]) if chosen_names else "preferred_sections"
    return label, text
