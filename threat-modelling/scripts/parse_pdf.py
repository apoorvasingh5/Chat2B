#!/usr/bin/env python3
"""
Artifact Ingestion Agent helper: PDF parser.

Extracts per-page text (and tables, where a table-aware backend is
available) from a PDF architecture document, with page-level references so
downstream agents can cite evidence as "SRC-00X, page N". PDF parsing has
no pure-stdlib option, so this script tries progressively lighter-weight
optional dependencies and degrades gracefully:

    1. pdfplumber   (best: text + tables + image/diagram counts per page)
    2. PyMuPDF (fitz) (text + image counts per page)
    3. pypdf / PyPDF2 (text only)
    4. none installed -> emits a clear, actionable error artifact instead
       of crashing, per the skill's "stop and clarify on missing
       information" principle.

Usage:
    python parse_pdf.py <file.pdf> [--artifact-id SRC-003] [--out out.json]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from common import sha256_of_file, save_json, eprint

BACKEND = None
try:
    import pdfplumber  # type: ignore
    BACKEND = "pdfplumber"
except ImportError:
    try:
        import fitz  # type: ignore  # PyMuPDF
        BACKEND = "pymupdf"
    except ImportError:
        try:
            from pypdf import PdfReader  # type: ignore
            BACKEND = "pypdf"
        except ImportError:
            try:
                from PyPDF2 import PdfReader  # type: ignore
                BACKEND = "pypdf2"
            except ImportError:
                BACKEND = None


def _low_text_density(text: str, page_area: float) -> bool:
    """Heuristic: pages that are mostly a diagram tend to have very little
    extractable text relative to a typical text page."""
    return page_area > 0 and (len(text or "") / page_area) < 0.02


def extract_with_pdfplumber(path: Path) -> dict:
    pages = []
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            tables = []
            for t in page.extract_tables():
                if t:
                    tables.append({"header": t[0], "rows": t[1:]})
            area = float(page.width or 0) * float(page.height or 0)
            image_count = len(page.images)
            pages.append({
                "page": i + 1,
                "text": text.strip(),
                "tables": tables,
                "image_count": image_count,
                "likely_diagram_page": image_count > 0 and _low_text_density(text, area),
            })
    return {"pages": pages, "page_count": len(pages)}


def extract_with_pymupdf(path: Path) -> dict:
    pages = []
    doc = fitz.open(str(path))
    for i, page in enumerate(doc):
        text = page.get_text("text") or ""
        images = page.get_images(full=True)
        rect = page.rect
        area = float(rect.width) * float(rect.height)
        pages.append({
            "page": i + 1,
            "text": text.strip(),
            "tables": [],
            "image_count": len(images),
            "likely_diagram_page": len(images) > 0 and _low_text_density(text, area),
        })
    doc.close()
    return {"pages": pages, "page_count": len(pages)}


def extract_with_pypdf(path: Path) -> dict:
    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        pages.append({
            "page": i + 1,
            "text": text,
            "tables": [],
            "image_count": None,
            "likely_diagram_page": None,
        })
    return {"pages": pages, "page_count": len(pages)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="Path to the PDF file to parse")
    parser.add_argument("--artifact-id", default="SRC-001", help="Source artifact ID (e.g. SRC-003)")
    parser.add_argument("--out", default="-", help="Output JSON path, or '-' for stdout")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        eprint(f"error: file not found: {path}")
        return 1

    artifact = {
        "id": args.artifact_id,
        "file_name": path.name,
        "type": "pdf",
        "location": str(path),
        "hash": sha256_of_file(path),
    }

    if BACKEND is None:
        result = {
            "artifact": artifact,
            "error": "no_pdf_backend_available",
            "message": (
                "No PDF text-extraction library is installed. Install one of: "
                "'pip install pdfplumber' (recommended, also extracts tables), "
                "'pip install pymupdf', or 'pip install pypdf'. "
                "Per the skill's missing-information rule, treat this artifact "
                "as unparsed and ask the user for a text/Markdown/HTML export, "
                "or for the missing dependency to be installed, before proceeding."
            ),
            "pages": [],
            "page_count": 0,
        }
        save_json(result, args.out)
        eprint("warning: no PDF backend available; emitted an unparsed-artifact placeholder")
        return 2

    try:
        if BACKEND == "pdfplumber":
            extracted = extract_with_pdfplumber(path)
        elif BACKEND == "pymupdf":
            extracted = extract_with_pymupdf(path)
        else:
            extracted = extract_with_pypdf(path)
    except Exception as exc:  # noqa: BLE001 - surface any backend failure as data, not a crash
        result = {
            "artifact": artifact,
            "error": "pdf_extraction_failed",
            "message": f"{BACKEND} raised: {exc}",
            "pages": [],
            "page_count": 0,
        }
        save_json(result, args.out)
        eprint(f"error: extraction failed with backend {BACKEND}: {exc}")
        return 1

    diagram_pages = [p["page"] for p in extracted["pages"] if p.get("likely_diagram_page")]
    table_count = sum(len(p.get("tables") or []) for p in extracted["pages"])

    result = {
        "artifact": artifact,
        "backend": BACKEND,
        "page_count": extracted["page_count"],
        "diagrams_detected": len(diagram_pages) > 0,
        "likely_diagram_pages": diagram_pages,
        "pages": extracted["pages"],
        "stats": {
            "page_count": extracted["page_count"],
            "table_count": table_count,
            "likely_diagram_page_count": len(diagram_pages),
        },
    }

    save_json(result, args.out)
    if args.out != "-":
        eprint(f"wrote {args.out} (backend: {BACKEND})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
