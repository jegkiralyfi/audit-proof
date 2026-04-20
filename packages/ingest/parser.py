from __future__ import annotations

import re
from pathlib import Path

from packages.core.hashing import sha256_bytes, sha256_text
from packages.core.models import ParsedDocument, ParsedSection


SECTION_NAMES = [
    "abstract",
    "introduction",
    "background",
    "methods",
    "materials and methods",
    "results",
    "discussion",
    "conclusion",
    "limitations",
    "references",
]



def _extract_text_from_pdf(path: Path) -> str:
    try:
        from PyPDF2 import PdfReader  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("PyPDF2 is required for PDF parsing in the PoC") from exc

    reader = PdfReader(str(path))
    texts = []
    for page in reader.pages:
        texts.append(page.extract_text() or "")
    return "\n\n".join(texts)



def read_text_from_path(path: str | Path) -> tuple[str, str]:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        text = _extract_text_from_pdf(p)
    else:
        text = p.read_text(encoding="utf-8")
    return text, sha256_bytes(p.read_bytes())



def split_sections(text: str) -> list[ParsedSection]:
    pattern = re.compile(
        r"(?im)^\s*(abstract|introduction|background|methods|materials and methods|results|discussion|conclusion|limitations|references)\s*$"
    )
    matches = list(pattern.finditer(text))
    if not matches:
        return [ParsedSection(name="full_text", text=text.strip())]

    sections: list[ParsedSection] = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        name = match.group(1).strip().lower()
        body = text[start:end].strip()
        sections.append(ParsedSection(name=name, text=body))
    return sections



def parse_text_to_document(text: str, source_name: str = "inline-text", metadata: dict | None = None) -> ParsedDocument:
    metadata = metadata or {}
    sections = split_sections(text)
    title = metadata.get("title")
    abstract = None
    for section in sections:
        if section.name == "abstract":
            abstract = section.text
            break
    if title is None:
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), None)
        title = first_line

    return ParsedDocument(
        doc_hash=sha256_text(text),
        title=title,
        abstract=abstract,
        sections=sections,
        metadata=metadata,
        source_name=source_name,
        raw_text=text,
    )



def parse_path_to_document(path: str | Path, metadata: dict | None = None) -> ParsedDocument:
    text, doc_hash = read_text_from_path(path)
    metadata = metadata or {}
    doc = parse_text_to_document(text=text, source_name=Path(path).name, metadata=metadata)
    doc.doc_hash = doc_hash
    return doc
