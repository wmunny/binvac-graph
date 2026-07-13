"""Extracción y reemplazo de bloques AUTO delimitados por marcadores HTML."""

from __future__ import annotations

import re

MARKER_START = "<!-- AUTO:{name}:START -->"
MARKER_END = "<!-- AUTO:{name}:END -->"


def marker_start(name: str) -> str:
    return MARKER_START.format(name=name)


def marker_end(name: str) -> str:
    return MARKER_END.format(name=name)


def extract_block(text: str, name: str) -> str | None:
    pattern = re.compile(
        re.escape(marker_start(name)) + r"(.*?)" + re.escape(marker_end(name)),
        re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1) if m else None


def replace_or_insert_block(
    text: str,
    name: str,
    content: str,
    section_title: str | None = None,
) -> str:
    """Reemplaza bloque AUTO o lo inserta al final del documento."""
    block = (
        f"{marker_start(name)}\n"
        f"{content.rstrip()}\n"
        f"{marker_end(name)}"
    )
    pattern = re.compile(
        re.escape(marker_start(name)) + r".*?" + re.escape(marker_end(name)),
        re.DOTALL,
    )
    if pattern.search(text):
        return pattern.sub(block, text, count=1)

    insertion = ""
    if section_title:
        insertion = f"\n## {section_title}\n\n{block}\n"
    else:
        insertion = f"\n{block}\n"
    return text.rstrip() + insertion + "\n"
