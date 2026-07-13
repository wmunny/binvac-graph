"""Descarga todos los PDFs de BINVAC del INSST en la carpeta raw/."""

import re
import time
import html as html_lib
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = "https://www.insst.es/stp/binvac"
RAW_DIR = Path(__file__).parent / "raw"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
TOTAL_PAGES = 21


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def extract_pdf_links(page_html: str) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    pattern = re.compile(
        r'href="([^"]*BINVAC[^"]*\.pdf[^"]*)"[^>]*>\s*(BINVAC[^<]*\.pdf)\s*</a>',
        re.IGNORECASE,
    )
    for match in pattern.finditer(page_html):
        href = html_lib.unescape(match.group(1))
        name = match.group(2).strip()
        url = urllib.parse.urljoin(BASE_URL, href)
        results.append((name, url))
    return results


def download_file(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    if len(data) < 500 or not data[:4].startswith(b"%PDF"):
        raise ValueError(f"respuesta no parece PDF ({len(data)} bytes)")
    dest.write_bytes(data)


def page_url(page: int) -> str:
    if page <= 1:
        return BASE_URL
    return f"{BASE_URL}?start={page}"


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    all_pdfs: dict[str, str] = {}

    print(f"Recorriendo {TOTAL_PAGES} páginas de BINVAC...")
    for page in range(1, TOTAL_PAGES + 1):
        url = page_url(page)
        try:
            page_html = fetch(url)
            links = extract_pdf_links(page_html)
            print(f"  Página {page:2d}: {len(links)} PDFs")
            for name, pdf_url in links:
                all_pdfs[name] = pdf_url
        except Exception as exc:
            print(f"  Página {page:2d}: ERROR - {exc}")
        time.sleep(0.3)

    print(f"\nTotal PDFs únicos: {len(all_pdfs)}")

    ok, fail, skip = 0, 0, 0
    for name in sorted(all_pdfs):
        url = all_pdfs[name]
        dest = RAW_DIR / name
        if dest.exists() and dest.stat().st_size > 1000:
            skip += 1
            continue
        try:
            print(f"Descargando {name}...")
            download_file(url, dest)
            ok += 1
            time.sleep(0.15)
        except Exception as exc:
            print(f"  ERROR {name}: {exc}")
            fail += 1

    print(f"\nCompletado: {ok} descargados, {skip} ya existían, {fail} errores")
    print(f"Carpeta: {RAW_DIR.resolve()}")


if __name__ == "__main__":
    main()
