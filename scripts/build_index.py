"""Genera wiki/index.md agrupando por códigos canónicos ESAW/CNAE.

Produce un catálogo de todas las fichas y vistas agrupadas por forma,
desviación, agente material y sector. Reejecutar tras cada ingesta.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.frontmatter import parse_frontmatter  # noqa: E402
from lib.normalize import is_corrupt_text  # noqa: E402
from lib.registry import Registry  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "wiki" / "sources"
INDEX = ROOT / "wiki" / "index.md"

FIELDS = [
    ("forma", "forma_codigo", "forma"),
    ("desviacion", "desviacion_codigo", "desviacion"),
    ("agente_actividad", "agente_actividad_codigo", "agente_material"),
    ("cnae", "cnae_codigo", "sector"),
]


def link(stem: str, label: str) -> str:
    return f"[[{stem}|{label}]]"


def entity_link(slug: str, label: str) -> str:
    return f"[[{slug}|{label}]]"


def main() -> None:
    registry = Registry.load()
    rows: list[dict] = []
    for path in sorted(SOURCES.glob("BINVAC_*.md")):
        fm, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        fm["stem"] = path.stem
        rows.append(fm)

    groups: dict[str, dict[str, list]] = {f[0]: defaultdict(list) for f in FIELDS}

    for r in rows:
        for text_key, code_key, dimension in FIELDS:
            text = r.get(text_key, "") or ""
            code = r.get(code_key, "") or ""
            if is_corrupt_text(text):
                text = ""
            ref = registry.resolve(dimension, code, text)
            if ref:
                key = ref.slug
                label = ref.titulo
            elif text:
                key = f"TEXT:{text}"
                label = text
            else:
                continue
            groups[text_key][key].append((r, label))

    out: list[str] = []
    out.append("---")
    out.append("tipo: index")
    out.append("tags:")
    out.append("  - index")
    out.append("---")
    out.append("")
    out.append("# Índice del cerebro de investigación de accidentes")
    out.append("")
    out.append("> Página generada por `scripts/build_index.py`. No editar a mano; "
               "reejecutar tras cada ingesta.")
    out.append("")
    out.append(f"- **Fichas fuente**: {len(rows)}")
    out.append(f"- **Grupos por forma (canónico)**: {len(groups['forma'])}")
    out.append(f"- **Grupos por sector (canónico)**: {len(groups['cnae'])}")
    out.append("")
    out.append("Páginas clave: [[overview]] · [[log]] · [[causas/README|Causas]] · "
               "[[medidas-preventivas/README|Catálogo de medidas]] · "
               "[[patrones/README|Patrones]]")
    out.append("")

    section_titles = {
        "forma": "forma / modalidad de la lesión",
        "desviacion": "desviación",
        "agente_actividad": "agente material",
        "cnae": "sector (CNAE)",
    }

    for text_key, title in section_titles.items():
        out.append(f"## Por {title}")
        out.append("")
        grp = groups[text_key]
        for key in sorted(grp, key=lambda k: (-len(grp[k]), k.lower())):
            items = grp[key]
            label = items[0][1]
            fichas = [r for r, _ in items]
            links = ", ".join(
                link(r["stem"], r.get("codigo", ""))
                for r in sorted(fichas, key=lambda x: x.get("codigo", ""))
            )
            if key.startswith("TEXT:"):
                header = f"**{label}**"
            else:
                header = f"**{entity_link(key, label)}**"
            out.append(f"- {header} ({len(fichas)}): {links}")
        out.append("")

    out.append("## Catálogo de fichas")
    out.append("")
    out.append("| Código | Título | Forma | Sector |")
    out.append("| --- | --- | --- | --- |")
    for r in rows:
        titulo = (r.get("titulo", "") or "").replace("|", "\\|")
        forma = (r.get("forma", "") or "").replace("|", "\\|")
        sector = (r.get("cnae", "") or "").replace("|", "\\|")
        out.append(
            f"| {link(r['stem'], r.get('codigo', ''))} | {titulo} "
            f"| {forma} | {sector} |"
        )
    out.append("")

    INDEX.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"index.md generado con {len(rows)} fichas, "
          f"{len(groups['forma'])} grupos de forma.")


if __name__ == "__main__":
    main()
