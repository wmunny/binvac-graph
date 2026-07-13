"""Convierte las fichas BINVAC (PDF en raw/) en paginas de fuente normalizadas.

Cada PDF se transforma en wiki/sources/BINVAC_NNN.md con:
  - frontmatter YAML (codigo, titulo, codificacion ESAW, contadores) para Dataview.
  - las secciones del accidente en markdown: Datos, Descripcion, Causas, Recomendaciones.

El extractor es faithful: reproduce el contenido de la ficha lo mas fielmente
posible. La capa de sintesis (entidades, catalogo de medidas, patrones) la
construye y mantiene el agente segun AGENTS.md; aqui solo se generan las fuentes.

Uso:
  python scripts/extract_fichas.py            # procesa todos los PDF de raw/
  python scripts/extract_fichas.py raw/BINVAC_018.pdf ...   # solo esos
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "raw"
OUT_DIR = ROOT / "wiki" / "sources"

# Etiquetas de la tabla "DATOS DEL ACCIDENTE" (codificacion tipo ESAW).
# (prefijo_normalizado, clave_frontmatter, etiqueta_visible)
DATOS_LABELS: list[tuple[str, str, str]] = [
    ("actividad economica", "cnae", "Actividad económica (CNAE)"),
    ("actividad fisica especifica", "actividad_fisica", "Actividad física específica"),
    ("desviacion", "desviacion", "Desviación"),
    ("forma", "forma", "Forma (contacto, modalidad de la lesión)"),
    ("agente material de la actividad fisica", "agente_actividad",
     "Agente material de la actividad física"),
    ("agente material de la desviacion", "agente_desviacion",
     "Agente material de la desviación"),
    ("agente material causante de la lesion", "agente_lesion",
     "Agente material causante de la lesión"),
]
# El orden de comprobacion importa: primero los prefijos mas especificos.
DATOS_LABELS_MATCH = sorted(DATOS_LABELS, key=lambda x: len(x[0]), reverse=True)

TABLE_NOISE = {"dato", "codigo", "texto"}

BULLET_RE = re.compile(r"^\s*[\u2022\u00b7\u25aa\u25e6\u25cf\uf0b7\u2013\u2014\-\*]\s*")
CODE_RE = re.compile(r"^[\d\s]+$")
TITLE_RE = re.compile(r"^\s*(\d{2,4})\s*[\.\)]\s*(.*)$")


def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", strip_accents(text).lower()).strip()


def collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def is_bullet(line: str) -> bool:
    return bool(BULLET_RE.match(line))


def strip_bullet(line: str) -> str:
    return BULLET_RE.sub("", line, count=1).strip()


def yaml_str(value: str) -> str:
    value = collapse(value).replace("\\", " ").replace('"', "'")
    return f'"{value}"'


def find_line(lines: list[str], predicate) -> int:
    for i, line in enumerate(lines):
        if predicate(norm(line)):
            return i
    return -1


MIDWORD_CAP_RE = re.compile(r"[a-zñáéíóúü][A-ZÑÁÉÍÓÚÜ]")


def is_exploded(line: str) -> bool:
    """Texto vectorial de imagenes que PyMuPDF devuelve en caracteres sueltos
    (p. ej. 'G', 'r', 'u t', 'a n'). Se detecta por tokens muy cortos."""
    tokens = line.split()
    if len(tokens) < 2:
        return len(line.strip()) <= 2
    avg = sum(len(t) for t in tokens) / len(tokens)
    return avg <= 1.5


def is_scrambled(line: str) -> bool:
    """Pie de foto/leyenda cuyo texto vectorial explotado se ha intercalado con
    palabras al ordenar por posicion (p. ej. 'volcadaG sobre losr palesu t')."""
    tokens = line.split()
    if len(tokens) < 4:
        return False
    singles = sum(1 for t in tokens if len(t) == 1 and t.isalpha())
    midcaps = sum(1 for t in tokens if MIDWORD_CAP_RE.search(t))
    return singles + 2 * midcaps >= 5


def clean_region(lines: list[str], title_norm: str,
                 keep_blanks: bool = False) -> list[str]:
    """Elimina ruido de cabeceras/pies repetidos e imagenes explotadas.

    Con keep_blanks=True conserva UNA linea en blanco como separador de
    parrafos (util para secciones sin vinetas)."""
    cleaned: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if keep_blanks and cleaned and cleaned[-1] != "":
                cleaned.append("")
            continue
        n = norm(stripped)
        # Numero de pagina suelto.
        if re.fullmatch(r"\d{1,3}", n):
            continue
        # Fragmento del titulo repetido como cabecera.
        if len(n) > 12 and n in title_norm:
            continue
        # Cabecera de pagina repetida (a veces con pie de foto revuelto pegado):
        # cualquier linea que contenga un prefijo largo del titulo.
        needle = title_norm[:40]
        if len(needle) >= 20 and needle in n:
            continue
        # Caracteres sueltos de texto vectorial de imagenes (no vinetas).
        if not is_bullet(line) and is_exploded(stripped):
            continue
        # Pie de foto revuelto con caracteres explotados intercalados.
        if not is_bullet(line) and is_scrambled(stripped):
            continue
        cleaned.append(stripped)
    while cleaned and cleaned[-1] == "":
        cleaned.pop()
    return cleaned


def datos_label(line: str) -> tuple[str, str] | None:
    n = norm(line)
    for prefix, key, label in DATOS_LABELS_MATCH:
        if n.startswith(prefix):
            return key, label
    return None


def is_grouped_datos(region: list[str]) -> bool:
    """Layout antiguo/irregular: las etiquetas van agrupadas y separadas de sus
    codigos/textos (cabeceras 'codigo'/'texto' en bloque). Es ambiguo de alinear,
    asi que se detecta para no generar datos incorrectos."""
    label_idxs = [i for i, l in enumerate(region) if datos_label(l)]
    for a, b in zip(label_idxs, label_idxs[1:]):
        between = [region[k].strip() for k in range(a + 1, b)]
        if all(not s for s in between):
            return True
    return False


def parse_datos(region: list[str]) -> list[dict]:
    if is_grouped_datos(region):
        # No se puede alinear con fiabilidad: mejor vacio que incorrecto.
        return []
    fields: list[dict] = []
    current: dict | None = None
    for raw_line in region:
        line = raw_line.strip()
        if not line:
            continue
        n = norm(line)
        if n in TABLE_NOISE:
            continue
        matched = datos_label(line)
        if matched:
            current = {"key": matched[0], "label": matched[1], "code": "", "text": ""}
            fields.append(current)
            continue
        if current is None:
            continue
        if CODE_RE.match(line):
            current["code"] += re.sub(r"\D", "", line)
        else:
            current["text"] = (current["text"] + " " + line).strip()
    for f in fields:
        f["text"] = collapse(f["text"])
    return fields


def segment_items(lines: list[str]) -> list[str]:
    """Convierte lineas (con posibles blancos) en items. Usa vinetas si las hay;
    si no, agrupa en parrafos separados por lineas en blanco."""
    items: list[str] = []
    if any(is_bullet(l) for l in lines if l):
        for line in lines:
            if not line:
                continue
            if is_bullet(line):
                items.append(strip_bullet(line))
            elif items:
                items[-1] = collapse(items[-1] + " " + line)
    else:
        current = ""
        for line in lines:
            if not line:
                if current:
                    items.append(current)
                    current = ""
            else:
                current = collapse(current + " " + line)
        if current:
            items.append(current)
    return [collapse(i) for i in items if collapse(i)]


def parse_descripcion(region: list[str], title_norm: str) -> dict[str, list[str]]:
    lines = clean_region(region, title_norm, keep_blanks=True)
    subheaders = {"tarea", "accidente", "datos complementarios"}
    # "relato" recoge la prosa previa a cualquier subtitulo (plantilla antigua
    # cuya DESCRIPCION no usa los epigrafes Tarea/Accidente).
    buckets: dict[str, list[str]] = {"relato": [], "tarea": [], "accidente": [],
                                     "datos complementarios": []}
    current_key = "relato"
    for line in lines:
        n = norm(line)
        if n in subheaders:
            current_key = n
            continue
        buckets[current_key].append(line)
    return {k: segment_items(v) for k, v in buckets.items()}


def parse_causas(region: list[str], title_norm: str) -> list[dict]:
    lines = clean_region(region, title_norm, keep_blanks=True)
    causas: list[dict] = []
    has_categories = any(norm(l).startswith("causas relativas") for l in lines if l)
    if has_categories:
        categoria = ""
        for line in lines:
            if not line:
                continue
            n = norm(line)
            if not is_bullet(line) and n.startswith("causas relativas"):
                categoria = collapse(line)
                continue
            if is_bullet(line):
                causas.append({"categoria": categoria, "titulo": strip_bullet(line),
                               "descripcion": ""})
            elif causas:
                causas[-1]["descripcion"] = collapse(
                    causas[-1]["descripcion"] + " " + line)
    else:
        for item in segment_items(lines):
            causas.append({"categoria": "", "titulo": item, "descripcion": ""})
    return causas


def parse_lista(region: list[str], title_norm: str) -> list[str]:
    return segment_items(clean_region(region, title_norm, keep_blanks=True))


def parse_pdf(path: Path) -> dict:
    doc = fitz.open(path)
    lines: list[str] = []
    lines_raw: list[str] = []
    for page in doc:
        # sort=True ordena los bloques por posicion (y, x): corrige el orden de
        # lectura de las plantillas con etiquetas de seccion en pestana grafica
        # (necesario para causas/recomendaciones).
        lines.extend(page.get_text("text", sort=True).split("\n"))
        # El texto SIN ordenar conserva mejor la tabla de DATOS (columnas
        # dato/codigo/texto), que sort=True entrelaza.
        lines_raw.extend(page.get_text("text").split("\n"))
    doc.close()

    # Titulo y DATOS se leen del texto sin ordenar (tabla mas fiable).
    title_start = -1
    for i, line in enumerate(lines_raw):
        if TITLE_RE.match(line.strip()):
            title_start = i
            break
    idx_datos_raw = find_line(lines_raw, lambda n: n.startswith("datos del accidente"))
    idx_desc_raw = find_line(lines_raw, lambda n: n.startswith("descripcion"))

    idx_desc = find_line(lines, lambda n: n.startswith("descripcion"))
    label_causas = find_line(lines, lambda n: n == "causas")
    if label_causas == -1:
        # A veces la etiqueta aparece pegada a texto de imagen ("...ImagCAUSAS").
        # El cuerpo nunca lleva "CAUSAS" en mayusculas, asi que es fiable.
        for i, line in enumerate(lines):
            if line.strip().endswith("CAUSAS"):
                label_causas = i
                break
    label_reco = find_line(
        lines,
        lambda n: n.startswith("recomendaciones") or n.startswith("medidas preventivas"),
    )
    # Ancla de contenido de causas (categorias tipo "Causas relativas a...").
    content_causas = find_line(lines, lambda n: n.startswith("causas relativas"))

    # Plantilla nueva: get_text() reordena y agrupa las etiquetas CAUSAS/
    # RECOMENDACIONES DESPUES del contenido de causas.
    reordered = content_causas != -1 and (
        label_causas == -1 or content_causas < label_causas)

    codigo = ""
    title_parts: list[str] = []
    if title_start >= 0:
        m = TITLE_RE.match(lines_raw[title_start].strip())
        codigo = m.group(1)
        if m.group(2).strip():
            title_parts.append(m.group(2).strip())
        end = idx_datos_raw if idx_datos_raw > title_start else title_start + 1
        for line in lines_raw[title_start + 1:end]:
            if line.strip():
                title_parts.append(line.strip())
    titulo = collapse(" ".join(title_parts))
    title_norm = norm(titulo)

    n_total = len(lines)

    def sl(a: int, b: int) -> list[str]:
        if a < 0 or a >= n_total:
            return []
        b = b if (b is not None and b > a) else n_total
        return lines[a:b]

    # Determinar limites de cada seccion segun la plantilla.
    if reordered:
        # ...DESCRIPCION -> [contenido causas] -> etiquetas CAUSAS/RECO -> [reco]
        labels_cluster = min(
            [i for i in (label_causas, label_reco) if i > content_causas],
            default=n_total)
        desc_slice = sl(idx_desc + 1, content_causas) if idx_desc >= 0 else []
        causas_slice = sl(content_causas, labels_cluster)
        reco_slice = sl(label_reco + 1, n_total) if label_reco >= 0 else []
    else:
        desc_end = label_causas if label_causas >= 0 else label_reco
        desc_slice = sl(idx_desc + 1, desc_end) if idx_desc >= 0 else []
        causas_slice = (sl(label_causas + 1, label_reco if label_reco >= 0 else n_total)
                        if label_causas >= 0 else [])
        reco_slice = sl(label_reco + 1, n_total) if label_reco >= 0 else []

    datos_slice = (lines_raw[idx_datos_raw + 1:idx_desc_raw]
                   if idx_datos_raw >= 0 and idx_desc_raw > idx_datos_raw else [])
    datos = parse_datos(datos_slice) if datos_slice else []
    # Si no se pudo estructurar (layout antiguo agrupado), conservar el texto en
    # crudo para no perder la codificacion ESAW.
    datos_raw = ""
    if not datos and datos_slice:
        raw_lines = [collapse(l) for l in datos_slice
                     if l.strip() and norm(l) not in TABLE_NOISE
                     and not re.fullmatch(r"[\d\s]+", l.strip())]
        datos_raw = "; ".join(raw_lines)
    desc = parse_descripcion(desc_slice, title_norm) if desc_slice else {}
    causas = parse_causas(causas_slice, title_norm) if causas_slice else []
    reco = parse_lista(reco_slice, title_norm) if reco_slice else []

    return {
        "codigo": codigo,
        "titulo": titulo,
        "datos": datos,
        "datos_raw": datos_raw,
        "descripcion": desc,
        "causas": causas,
        "recomendaciones": reco,
    }


def build_markdown(data: dict, source_name: str) -> str:
    datos_by_key = {d["key"]: d for d in data["datos"]}

    def dval(key: str) -> str:
        return datos_by_key.get(key, {}).get("text", "")

    def dcode(key: str) -> str:
        return datos_by_key.get(key, {}).get("code", "")

    fm: list[str] = ["---"]
    fm.append(f'codigo: {yaml_str(data["codigo"])}')
    fm.append(f'titulo: {yaml_str(data["titulo"])}')
    fm.append(f"fuente: {source_name}")
    for _, key, _ in DATOS_LABELS:
        fm.append(f"{key}: {yaml_str(dval(key))}")
        code = dcode(key)
        if code:
            fm.append(f'{key}_codigo: "{code}"')
    fm.append(f'n_causas: {len(data["causas"])}')
    fm.append(f'n_recomendaciones: {len(data["recomendaciones"])}')
    fm.append("tags:")
    fm.append("  - fuente")
    fm.append("  - binvac")
    fm.append("---")

    body: list[str] = []
    titulo = data["titulo"] or source_name
    header = f'{data["codigo"]} — {titulo}' if data["codigo"] else titulo
    body.append(f"# {header}")
    body.append("")
    body.append(f"> Fuente original: `raw/{source_name}` (BINVAC, INSST). "
                "Página de fuente generada automáticamente por "
                "`scripts/extract_fichas.py`.")
    body.append("")

    body.append("## Datos del accidente")
    body.append("")
    if data["datos"]:
        body.append("| Dato | Código | Texto |")
        body.append("| --- | --- | --- |")
        for _, key, label in DATOS_LABELS:
            d = datos_by_key.get(key)
            if d:
                body.append(f"| {label} | {d['code']} | {d['text']} |")
            else:
                body.append(f"| {label} |  |  |")
    elif data.get("datos_raw"):
        body.append("> Codificación no estructurable automáticamente (ficha con "
                    "maquetación antigua). Texto original de los datos:")
        body.append("")
        body.append(data["datos_raw"])
    else:
        body.append("_No disponible._")
    body.append("")

    desc = data["descripcion"]
    if desc and any(desc.get(k) for k in
                    ("relato", "tarea", "accidente", "datos complementarios")):
        body.append("## Descripción")
        body.append("")
        relato = desc.get("relato", [])
        if relato:
            for it in relato:
                body.append(f"- {it}")
            body.append("")
        for key, label in [("tarea", "Tarea"), ("accidente", "Accidente"),
                           ("datos complementarios", "Datos complementarios")]:
            items = desc.get(key, [])
            if items:
                body.append(f"### {label}")
                body.append("")
                for it in items:
                    body.append(f"- {it}")
                body.append("")

    if data["causas"]:
        body.append("## Causas")
        body.append("")
        last_cat = None
        for c in data["causas"]:
            if c["categoria"] and c["categoria"] != last_cat:
                body.append(f"### {c['categoria']}")
                body.append("")
                last_cat = c["categoria"]
            if c["descripcion"]:
                body.append(f"- **{c['titulo']}**: {c['descripcion']}")
            else:
                body.append(f"- **{c['titulo']}**")
        body.append("")

    if data["recomendaciones"]:
        body.append("## Recomendaciones preventivas")
        body.append("")
        for r in data["recomendaciones"]:
            body.append(f"- {r}")
        body.append("")

    return "\n".join(fm) + "\n\n" + "\n".join(body).rstrip() + "\n"


def process(path: Path) -> tuple[bool, str]:
    try:
        data = parse_pdf(path)
    except Exception as exc:  # noqa: BLE001
        return False, f"ERROR al parsear: {exc}"
    md = build_markdown(data, path.name)
    out_path = OUT_DIR / (path.stem + ".md")
    out_path.write_text(md, encoding="utf-8")
    warns = []
    if not data["titulo"]:
        warns.append("sin titulo")
    if not data["datos"]:
        warns.append("sin datos")
    if not data["causas"]:
        warns.append("sin causas")
    if not data["recomendaciones"]:
        warns.append("sin recomendaciones")
    status = "OK" if not warns else "PARCIAL (" + ", ".join(warns) + ")"
    return True, status


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    args = sys.argv[1:]
    if args:
        pdfs = [Path(a) if Path(a).is_absolute() else ROOT / a for a in args]
    else:
        pdfs = sorted(RAW_DIR.glob("*.pdf"))

    if not pdfs:
        print("No hay PDFs que procesar en raw/.")
        return

    ok = 0
    parcial = 0
    fail = 0
    for pdf in pdfs:
        if not pdf.exists():
            print(f"  {pdf.name}: NO EXISTE")
            fail += 1
            continue
        success, status = process(pdf)
        print(f"  {pdf.name}: {status}")
        if not success:
            fail += 1
        elif status.startswith("OK"):
            ok += 1
        else:
            parcial += 1

    print(f"\nHecho: {ok} OK, {parcial} parciales, {fail} errores "
          f"de {len(pdfs)} fichas. Salida en {OUT_DIR}.")


if __name__ == "__main__":
    main()
