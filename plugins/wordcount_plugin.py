from __future__ import annotations

from packages.checks.base import CheckRunner
from packages.checks.common.scoring import build_result


class WordCountCheckRunner(CheckRunner):
    """Example third-party plugin runner."""

    def run(self, document, configured_check, *, domain: str, context=None):
        params = configured_check.params or {}
        preferred_sections = [s.lower() for s in params.get("preferred_sections", [])]
        min_words = int(params.get("min_words", 100))
        pass_note = params.get("pass_note", "Section length meets the minimum word-count threshold.")
        warning_note = params.get("warning_note", "Section appears shorter than the configured minimum.")

        texts = []
        if preferred_sections:
            texts = [sec.text for sec in document.sections if sec.name.lower() in preferred_sections]
        if not texts:
            texts = [sec.text for sec in document.sections]
        joined = "\n\n".join(texts).strip()
        words = [w for w in joined.split() if w.strip()]
        word_count = len(words)
        status = "pass" if word_count >= min_words else "warning"
        note = pass_note if status == "pass" else warning_note
        snippet = " ".join(words[:30])
        evidence = []
        if snippet:
            evidence = [{
                "section": preferred_sections[0] if preferred_sections else "document",
                "quote": snippet,
                "offset_start": 0,
                "offset_end": min(len(snippet), len(joined)),
            }]
        return build_result(
            check_id=f"{domain}.{configured_check.id}",
            status=status,
            confidence=0.7 if status == "pass" else 0.55,
            evidence=evidence,
            notes=f"{note} Observed word count: {word_count}.",
            details={
                "observed_word_count": word_count,
                "min_words": min_words,
                "attempt_kind": "content-profiling",
                "attempt_status": "not_attempted",
            },
        )


def register(registry):
    registry.register(
        "word_count_check",
        WordCountCheckRunner,
        runner_family="plugin-example",
        execution_mode="deterministic",
        capabilities=["plugin", "content-profiling", "section-scoped"],
        implementation="plugins.wordcount_plugin.WordCountCheckRunner",
        description="Example third-party plugin runner that profiles section length.",
    )
