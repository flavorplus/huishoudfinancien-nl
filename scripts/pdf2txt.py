#!/usr/bin/env python3
"""Zet alle PDF's in <werkmap>/data/ om naar tekst in <werkmap>/work/pdf/ (loonstroken, jaaropgaven, aangifte,
hypotheekoverzicht, kinderopvangfactuur). Gebruikt pdfplumber, anders pypdf/PyPDF2, anders PyMuPDF (fitz).
Gescande PDF's (alleen plaatjes) geven geen tekst: vraag dan om een foto/screenshot en lees die zelf.

Gebruik: python pdf2txt.py <werkmap>
"""
import sys
from pathlib import Path


def extract(p: Path) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(p) as pdf:
            return "\n\n=== PAGINA ===\n".join((pg.extract_text() or "") for pg in pdf.pages)
    except ImportError:
        pass
    for mod in ("pypdf", "PyPDF2"):
        try:
            lib = __import__(mod)
            return "\n\n=== PAGINA ===\n".join((pg.extract_text() or "") for pg in lib.PdfReader(str(p)).pages)
        except ImportError:
            continue
    try:
        import fitz
        return "\n\n=== PAGINA ===\n".join(pg.get_text() for pg in fitz.open(str(p)))
    except ImportError:
        raise SystemExit("Geen PDF-bibliotheek gevonden: pip install pdfplumber (of pypdf)")


def main(workdir: Path):
    data, out = workdir / "data", workdir / "work" / "pdf"
    out.mkdir(parents=True, exist_ok=True)
    for p in sorted(data.rglob("*.pdf")):
        txt = extract(p)
        dest = out / (p.relative_to(data).as_posix().replace("/", "__") + ".txt")
        dest.write_text(txt)
        flag = "  (weinig tekst: gescand? lees de pagina's als afbeelding)" if len(txt.strip()) < 200 else ""
        print(f"{p.relative_to(data)} -> {dest.name} ({len(txt)} tekens){flag}")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve())
