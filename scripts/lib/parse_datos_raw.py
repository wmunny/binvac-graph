"""Parser heurístico de datos_raw en fichas de maquetación antigua."""

from __future__ import annotations

import re

from .normalize import norm

LABELS = [
    ("cnae", ["actividad economica", "cnae"]),
    ("actividad_fisica", ["actividad fisica especifica", "actividad fisica"]),
    ("desviacion", ["desviacion"]),
    ("forma", ["forma", "modalidad de la lesion"]),
    ("agente_actividad", ["agente material de la actividad fisica"]),
    ("agente_desviacion", ["agente material de la desviacion"]),
    ("agente_lesion", ["agente material causante de la lesion"]),
]


def _match_label(token: str) -> str | None:
    n = norm(token)
    for key, variants in LABELS:
        for v in variants:
            if n.startswith(v) or n == v:
                return key
    return None


def parse_datos_raw(raw: str) -> dict[str, str]:
    """Devuelve campos inferidos con confianza baja. Sin códigos."""
    if not raw or not raw.strip():
        return {}
    parts = [p.strip() for p in re.split(r"[;]", raw) if p.strip()]
    result: dict[str, str] = {}
    current_key: str | None = None
    for part in parts:
        key = _match_label(part)
        if key:
            current_key = key
            continue
        if current_key and current_key not in result:
            result[current_key] = part
            current_key = None
        elif current_key:
            result[current_key] = f"{result[current_key]} {part}".strip()
    return result


def parse_datos_raw_alternating(raw: str) -> dict[str, str]:
    """Parser para layout alterno etiqueta;valor;etiqueta;valor."""
    if not raw or not raw.strip():
        return {}
    parts = [p.strip() for p in re.split(r"[;]", raw) if p.strip()]
    result: dict[str, str] = {}
    i = 0
    while i < len(parts):
        key = _match_label(parts[i])
        if key:
            if i + 1 < len(parts) and not _match_label(parts[i + 1]):
                result[key] = parts[i + 1]
                i += 2
            else:
                i += 1
        else:
            i += 1
    return result
