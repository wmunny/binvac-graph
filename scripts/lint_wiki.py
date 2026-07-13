"""Lint de salud del grafo de la wiki BinvacGraph.

Uso:
  python scripts/lint_wiki.py
  python scripts/lint_wiki.py --fail-on error
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.frontmatter import parse_frontmatter  # noqa: E402
from lib.markers import extract_block  # noqa: E402
from lib.normalize import (  # noqa: E402
    validate_agente_code,
    validate_cnae_code,
    validate_desviacion_code,
    validate_forma_code,
)

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
SOURCES = WIKI / "sources"

LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


class Issue:
    def __init__(self, severity: str, message: str) -> None:
        self.severity = severity
        self.message = message


def resolve_link(target: str) -> Path | None:
    if target.endswith("/README"):
        target = target.replace("/README", "/README.md")
    candidates = [
        WIKI / "sources" / f"{target}.md",
        WIKI / f"{target}.md",
        WIKI / target,
        WIKI / target / "README.md",
        WIKI / "causas" / f"{target}.md",
        WIKI / "medidas-preventivas" / f"{target}.md",
        WIKI / "patrones" / f"{target}.md",
        WIKI / "formas" / f"{target}.md",
        WIKI / "desviaciones" / f"{target}.md",
        WIKI / "agentes-materiales" / f"{target}.md",
        WIKI / "sectores" / f"{target}.md",
    ]
    if "/" in target:
        candidates.insert(0, WIKI / f"{target}.md")
    for c in candidates:
        if c.exists():
            return c
    # Búsqueda por nombre de archivo en toda la wiki
    matches = list(WIKI.rglob(f"{target}.md"))
    if len(matches) == 1:
        return matches[0]
    return None


def lint() -> list[Issue]:
    issues: list[Issue] = []
    all_files = {p.stem: p for p in WIKI.rglob("*.md")}

    # Enlaces rotos
    for path in WIKI.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for target in LINK_RE.findall(text):
            if target.startswith("http"):
                continue
            if "plantillas" in str(path) and "NNN" in target:
                continue
            if not resolve_link(target):
                issues.append(Issue("error", f"Enlace roto en {path.relative_to(ROOT)}: [[{target}]]"))

    # Fuentes sin bloque AUTO
    for path in sorted(SOURCES.glob("BINVAC_*.md")):
        text = path.read_text(encoding="utf-8")
        if not extract_block(text, "ENTIDADES"):
            issues.append(Issue("warning", f"Fuente sin enlaces AUTO: {path.name}"))
        fm, _ = parse_frontmatter(text)
        code = fm.get("forma_codigo", "")
        if code and not validate_forma_code(code):
            issues.append(Issue("warning", f"Código forma inválido en {path.name}: {code}"))
        code = fm.get("desviacion_codigo", "")
        if code and not validate_desviacion_code(code):
            issues.append(Issue("warning", f"Código desviación inválido en {path.name}: {code}"))
        code = fm.get("agente_actividad_codigo", "")
        if code and not validate_agente_code(code):
            issues.append(Issue("warning", f"Código agente inválido en {path.name}: {code}"))
        code = fm.get("cnae_codigo", "")
        if code and not validate_cnae_code(code):
            issues.append(Issue("warning", f"Código CNAE inválido en {path.name}: {code}"))

    # Huérfanas (sin enlaces entrantes fuera de index)
    incoming: dict[str, int] = defaultdict(int)
    for path in WIKI.rglob("*.md"):
        if path.name == "index.md":
            continue
        text = path.read_text(encoding="utf-8")
        for target in LINK_RE.findall(text):
            incoming[target] += 1

    for path in WIKI.rglob("*.md"):
        rel = path.relative_to(WIKI)
        stem = path.stem
        if path.parent.name == "sources":
            if incoming.get(stem, 0) < 2:
                issues.append(Issue("info", f"Fuente con pocos enlaces entrantes: {stem}"))
        elif path.name != "index.md" and incoming.get(stem, 0) == 0:
            if "plantillas" not in str(rel):
                issues.append(Issue("info", f"Página huérfana: {rel}"))

    return issues


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-on", choices=["error", "warning", "info"], default="error")
    args = parser.parse_args()
    severity_order = {"error": 0, "warning": 1, "info": 2}
    threshold = severity_order[args.fail_on]

    issues = lint()
    for issue in issues:
        print(f"[{issue.severity.upper()}] {issue.message}")

    fail = any(severity_order[i.severity] <= threshold for i in issues)
    print(f"\nTotal: {len(issues)} incidencias.")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
