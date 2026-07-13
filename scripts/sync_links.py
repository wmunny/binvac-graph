"""Sincroniza enlaces bidireccionales fuente ↔ entidad en la wiki.

Solo escribe bloques delimitados por marcadores AUTO. No modifica síntesis manual.

Uso:
  python scripts/sync_links.py
  python scripts/sync_links.py --dry-run
  python scripts/sync_links.py --check
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
SOURCES = WIKI / "sources"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.frontmatter import dump_frontmatter, parse_frontmatter  # noqa: E402
from lib.markers import extract_block, replace_or_insert_block  # noqa: E402
from lib.normalize import is_corrupt_text  # noqa: E402
from lib.parse_datos_raw import parse_datos_raw  # noqa: E402
from lib.registry import Registry  # noqa: E402

SOURCE_FIELDS = [
    ("forma", "forma_codigo", "forma"),
    ("desviacion", "desviacion_codigo", "desviacion"),
    ("agente_actividad", "agente_actividad_codigo", "agente_material"),
    ("cnae", "cnae_codigo", "sector"),
]

ENTITY_CATEGORIES = {
    "formas": "forma",
    "desviaciones": "desviacion",
    "agentes-materiales": "agente-material",
    "sectores": "sector",
}


def read_source(path: Path) -> tuple[dict, str]:
    return parse_frontmatter(path.read_text(encoding="utf-8"))


def extract_datos_raw(body: str) -> str:
    m = re.search(
        r"> Codificación no estructurable.*?\n\n(.+?)(?:\n\n## |\Z)",
        body,
        re.DOTALL,
    )
    return m.group(1).strip() if m else ""


def enrich_from_raw(fm: dict, body: str) -> dict:
    enriched = dict(fm)
    raw = extract_datos_raw(body)
    if not raw:
        return enriched
    inferred = parse_datos_raw(raw)
    for key, value in inferred.items():
        if not enriched.get(key) and value:
            enriched[key] = value
    return enriched


def link_label(ref_slug: str, code: str, text: str) -> str:
    display = text[:80] if text else ref_slug.split("/")[-1]
    if code:
        return f"[[{ref_slug}|{code} — {display}]]"
    return f"[[{ref_slug}|{display}]]"


def build_source_links(fm: dict, registry: Registry) -> list[str]:
    lines: list[str] = []
    for text_key, code_key, dimension in SOURCE_FIELDS:
        text = fm.get(text_key, "") or ""
        code = fm.get(code_key, "") or ""
        if is_corrupt_text(text):
            text = ""
        if not text and not code:
            continue
        ref = registry.resolve(dimension, code, text)
        if not ref:
            continue
        label = {
            "forma": "Forma",
            "desviacion": "Desviación",
            "agente_material": "Agente material",
            "sector": "Sector",
        }[dimension]
        lines.append(f"- **{label}**: {link_label(ref.slug, code, text or ref.titulo)}")
    lines.append("- **Índice**: [[index]]")
    return lines


def preserve_frontmatter(text: str, new_body: str) -> str:
    if not text.startswith("---"):
        return new_body
    end = text.find("\n---", 3)
    if end == -1:
        return new_body
    return text[: end + 4] + "\n\n" + new_body.lstrip("\n")


def ficha_line(stem: str, fm: dict) -> str:
    codigo = fm.get("codigo", stem.replace("BINVAC_", ""))
    titulo = (fm.get("titulo", "") or "")[:100]
    return f"- [[{stem}|{codigo}]] — (auto) {titulo}"


def ensure_auto_entity_page(
    slug: str,
    titulo: str,
    fichas: list[tuple[str, dict]],
    dry_run: bool,
) -> Path | None:
    """Crea o actualiza página de entidad auto_generada."""
    if slug.startswith("formas/"):
        folder, cat = "formas", "forma"
    elif slug.startswith("desviaciones/"):
        folder, cat = "desviaciones", "desviacion"
    elif slug.startswith("agentes-materiales/"):
        folder, cat = "agentes-materiales", "agente-material"
    elif slug.startswith("sectores/"):
        folder, cat = "sectores", "sector"
    else:
        return None

    rel = slug.split("/", 1)[1]
    path = WIKI / folder / f"{rel}.md"
    if path.exists():
        fm_existing, body_existing = parse_frontmatter(path.read_text(encoding="utf-8"))
        if fm_existing.get("sintesis") == "manual":
            return path
        if not fm_existing.get("auto_generada"):
            return path
    else:
        fm_existing, body_existing = {}, ""

    fichas_sorted = sorted(fichas, key=lambda x: x[0])
    fichas_codes = [f[1].get("codigo", f[0].replace("BINVAC_", "")) for f in fichas_sorted]
    auto_lines = [ficha_line(stem, fm) for stem, fm in fichas_sorted]
    auto_content = "\n".join(auto_lines)

    fm: dict = {
        "tipo": "entidad",
        "titulo": titulo,
        "categoria": cat,
        "auto_generada": True,
        "fichas_auto": fichas_codes,
        "tags": ["entidad", folder, "auto"],
    }
    if fm_existing.get("fichas"):
        fm["fichas"] = fm_existing["fichas"]

    body_parts = [
        f"# {titulo}",
        "",
        "> Página generada automáticamente por `scripts/sync_links.py`. "
        "Promover a entidad canónica cuando se complete la síntesis.",
        "",
    ]
    if body_existing and not fm_existing.get("auto_generada"):
        body_parts = [body_existing.rstrip(), ""]
    else:
        body_parts.extend([
            "## Fichas relacionadas",
            "",
        ])

    new_body = "\n".join(body_parts)
    new_body = replace_or_insert_block(new_body, "FICHAS", auto_content, None)
    content = dump_frontmatter(fm) + "\n\n" + new_body.rstrip() + "\n"

    if path.exists():
        old_content = path.read_text(encoding="utf-8")
        if old_content == content:
            return path

    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return path


def patch_entity_manual(path: Path, auto_lines: list[str], dry_run: bool) -> bool:
    """Añade bloque AUTO:FICHAS en entidades manuales sin sobrescribir contenido."""
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    if fm.get("auto_generada"):
        return False
    auto_content = "\n".join(auto_lines)
    new_body = replace_or_insert_block(body, "FICHAS", auto_content, "Fichas relacionadas (auto)")
    if extract_block(new_body, "FICHAS") == extract_block(body, "FICHAS"):
        return False
    new_text = preserve_frontmatter(text, new_body)
    if new_text == text:
        return False
    if not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return True


def sync(dry_run: bool = False, check: bool = False) -> int:
    registry = Registry.load()
    source_data: dict[str, tuple[dict, str]] = {}
    entity_fichas: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    changes = 0

    for path in sorted(SOURCES.glob("BINVAC_*.md")):
        fm, body = read_source(path)
        fm = enrich_from_raw(fm, body)
        source_data[path.stem] = (fm, body)

        for text_key, code_key, dimension in SOURCE_FIELDS:
            text = fm.get(text_key, "") or ""
            code = fm.get(code_key, "") or ""
            if is_corrupt_text(text):
                text = ""
            ref = registry.resolve(dimension, code, text)
            if ref:
                entity_fichas[ref.slug].append((path.stem, fm))

    # Actualizar fuentes
    for stem, (fm, body) in source_data.items():
        path = SOURCES / f"{stem}.md"
        original = path.read_text(encoding="utf-8")
        auto_lines = build_source_links(fm, registry)
        auto_content = "\n".join(auto_lines)
        new_body = replace_or_insert_block(
            body, "ENTIDADES", auto_content, "Clasificación y enlaces"
        )
        similar = find_similar(stem, fm, source_data)
        if similar:
            sim_content = "\n".join(f"- [[{s}]]" for s in similar)
            new_body = replace_or_insert_block(new_body, "SIMILARES", sim_content, "Fichas similares")

        ent_changed = extract_block(new_body, "ENTIDADES") != extract_block(body, "ENTIDADES")
        sim_changed = extract_block(new_body, "SIMILARES") != extract_block(body, "SIMILARES")
        if ent_changed or sim_changed:
            changes += 1
            if not dry_run and not check:
                path.write_text(preserve_frontmatter(original, new_body), encoding="utf-8")

    # Actualizar entidades
    for slug, fichas in entity_fichas.items():
        fichas_unique: dict[str, dict] = {}
        for stem, fm in fichas:
            fichas_unique[stem] = fm
        fichas_list = list(fichas_unique.items())
        auto_lines = [ficha_line(stem, fm) for stem, fm in sorted(fichas_list)]

        rel_parts = slug.split("/", 1)
        if len(rel_parts) != 2:
            continue
        folder, name = rel_parts
        entity_path = WIKI / folder / f"{name}.md"

        if entity_path.exists():
            fm_e, _ = parse_frontmatter(entity_path.read_text(encoding="utf-8"))
            if fm_e.get("sintesis") == "manual" or not fm_e.get("auto_generada", False):
                if patch_entity_manual(entity_path, auto_lines, dry_run or check):
                    changes += 1
                continue

        titulo_final = name.replace("-", " ").title()
        if fichas_list:
            ref = registry.resolve(
                {"formas": "forma", "desviaciones": "desviacion",
                 "agentes-materiales": "agente_material", "sectores": "sector"}[folder],
                fichas_list[0][1].get(
                    {"formas": "forma_codigo", "desviaciones": "desviacion_codigo",
                     "agentes-materiales": "agente_actividad_codigo",
                     "sectores": "cnae_codigo"}[folder], ""
                ),
                fichas_list[0][1].get(
                    {"formas": "forma", "desviaciones": "desviacion",
                     "agentes-materiales": "agente_actividad",
                     "sectores": "cnae"}[folder], ""
                ),
            )
            if ref:
                titulo_final = ref.titulo
        old_exists = entity_path.exists()
        old_content = entity_path.read_text(encoding="utf-8") if old_exists else ""
        ensure_auto_entity_page(slug, titulo_final, fichas_list, dry_run or check)
        if entity_path.exists():
            new_content = entity_path.read_text(encoding="utf-8")
            if new_content != old_content:
                changes += 1

    action = "CHECK" if check else ("DRY-RUN" if dry_run else "SYNC")
    print(f"{action}: {changes} cambios detectados/aplicados.")
    return 1 if check and changes else 0


def find_similar(
    stem: str,
    fm: dict,
    all_data: dict[str, tuple[dict, str]],
) -> list[str]:
    keys = ("forma_codigo", "desviacion_codigo", "agente_actividad_codigo")
    sig = tuple(fm.get(k, "") for k in keys)
    if not any(sig):
        return []
    similar = []
    for other_stem, (other_fm, _) in all_data.items():
        if other_stem == stem:
            continue
        other_sig = tuple(other_fm.get(k, "") for k in keys)
        if sig == other_sig and all(sig):
            similar.append(other_stem)
    return sorted(similar)[:8]


def main() -> None:
    parser = argparse.ArgumentParser(description="Sincroniza enlaces wiki")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    code = sync(dry_run=args.dry_run, check=args.check)
    sys.exit(code)


if __name__ == "__main__":
    main()
