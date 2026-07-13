"""Tests de marcadores AUTO."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.markers import extract_block, replace_or_insert_block  # noqa: E402


def test_replace_block_idempotente():
    text = "Contenido\n\n## Sección\n\n"
    block = "- enlace 1\n- enlace 2"
    once = replace_or_insert_block(text, "ENTIDADES", block, "Clasificación")
    twice = replace_or_insert_block(once, "ENTIDADES", block, "Clasificación")
    assert once == twice
    assert extract_block(twice, "ENTIDADES").strip() == block


def test_insert_block_nuevo():
    text = "# Título\n\nPárrafo.\n"
    result = replace_or_insert_block(text, "FICHAS", "- [[BINVAC_001]]", "Fichas")
    assert "AUTO:FICHAS:START" in result
    assert "[[BINVAC_001]]" in result
