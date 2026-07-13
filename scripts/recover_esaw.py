"""Recupera campos ESAW en fichas con maquetación antigua (datos_raw).

Solo rellena campos vacíos del frontmatter; no sobrescribe datos existentes.
Marca inferido: true cuando aplica.

Uso:
  python scripts/recover_esaw.py
  python scripts/recover_esaw.py --dry-run
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.frontmatter import dump_frontmatter, parse_frontmatter  # noqa: E402
from lib.parse_datos_raw import parse_datos_raw, parse_datos_raw_alternating  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "wiki" / "sources"

# Correcciones manuales para fichas prioritarias con datos_raw mal alineados
MANUAL_PATCHES: dict[str, dict[str, str]] = {
    "BINVAC_012": {
        "cnae": "Obrador de panadería",
        "actividad_fisica": "Vigilar la máquina",
        "desviacion": "Atrapada mano por cuchilla",
        "forma": "Amputación dedos",
        "agente_actividad": "Moldeadora de Pan (Conformadora de barras o Chapatera)",
        "agente_desviacion": "Restos de masa de pan",
        "agente_lesion": "Moldeadora de Pan (Conformadora de barras o Chapatera)",
    },
    "BINVAC_039": {
        "cnae": "Fabricación de carrocerías para vehículos",
        "actividad_fisica": "Hacer funcionar máquina",
        "desviacion": "Pérdida de control de máquina. Arranque intempestivo",
        "forma": "Amputación de dedos",
        "agente_actividad": "Cinta transportadora móviles",
        "agente_desviacion": "Cinta transportadora móviles",
        "agente_lesion": "Otros agentes constitutivos de máquinas",
    },
}

RAW_SECTION_RE = re.compile(
    r"> Codificación no estructurable.*?\n\n(.+?)(?:\n\n## |\Z)",
    re.DOTALL,
)


def extract_raw(body: str) -> str:
    m = RAW_SECTION_RE.search(body)
    return m.group(1).strip() if m else ""


def recover(dry_run: bool = False) -> int:
    changes = 0
    for path in sorted(SOURCES.glob("BINVAC_*.md")):
        text = path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        stem = path.stem

        if stem in MANUAL_PATCHES:
            inferred = MANUAL_PATCHES[stem]
        else:
            raw = extract_raw(body)
            if not raw:
                continue
            inferred = parse_datos_raw_alternating(raw)
            if not inferred:
                inferred = parse_datos_raw(raw)
            if not inferred:
                continue

        has_codes = any(fm.get(f"{k}_codigo") for k in (
            "forma", "desviacion", "actividad_fisica", "cnae", "agente_actividad"
        ))
        if has_codes and not fm.get("inferido") and stem not in MANUAL_PATCHES:
            continue

        updated = False
        for key in ("cnae", "actividad_fisica", "desviacion", "forma",
                    "agente_actividad", "agente_desviacion", "agente_lesion"):
            if inferred.get(key) and fm.get(key) != inferred[key]:
                fm[key] = inferred[key]
                updated = True

        if updated:
            fm["inferido"] = True
            changes += 1
            if not dry_run:
                new_text = dump_frontmatter(fm) + "\n\n" + body.lstrip("\n")
                path.write_text(new_text, encoding="utf-8")
                print(f"  {path.name}: campos recuperados")
    print(f"{'DRY-RUN' if dry_run else 'OK'}: {changes} fichas actualizadas.")
    return changes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    recover(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
