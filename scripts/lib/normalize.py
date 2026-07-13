"""Normalización de texto y validación de códigos ESAW/CNAE."""

from __future__ import annotations

import re
import unicodedata

CORRUPT_TEXT_RE = re.compile(r"dad de l a les", re.I)

FORMA_CODE_RE = re.compile(r"^\d{1,3}$")
DESVIACION_CODE_RE = re.compile(r"^\d{1,3}$")
ACTIVIDAD_CODE_RE = re.compile(r"^\d{1,3}$")
CNAE_CODE_RE = re.compile(r"^\d{2,4}$")
AGENTE_CODE_RE = re.compile(r"^\d{7,8}$")


def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def norm(text: str) -> str:
    text = strip_accents(text).lower()
    text = text.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip()


def slugify(text: str) -> str:
    text = norm(text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def is_corrupt_text(text: str) -> bool:
    return bool(CORRUPT_TEXT_RE.search(text))


def validate_forma_code(code: str) -> bool:
    return bool(code and FORMA_CODE_RE.match(code))


def validate_desviacion_code(code: str) -> bool:
    return bool(code and DESVIACION_CODE_RE.match(code))


def validate_actividad_code(code: str) -> bool:
    return bool(code and ACTIVIDAD_CODE_RE.match(code))


def validate_cnae_code(code: str) -> bool:
    return bool(code and CNAE_CODE_RE.match(code))


def validate_agente_code(code: str) -> bool:
    return bool(code and AGENTE_CODE_RE.match(code))


def agente_family(code: str) -> str:
    """Familia ESAW de agente material (primeros 4 dígitos + 0000)."""
    if not validate_agente_code(code):
        return ""
    padded = code.zfill(8)
    return padded[:4] + "0000"


def cnae_division(code: str) -> str:
    """División CNAE (2 primeros dígitos)."""
    if not validate_cnae_code(code):
        return ""
    padded = code.zfill(3)
    return padded[:2]
