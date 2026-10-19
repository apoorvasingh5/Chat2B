#!/usr/bin/env python3
"""
Artifact Ingestion Agent helper: HTML / Confluence export parser.

Extracts title, headings (with anchors), tables, links, code blocks, and
images (candidate diagrams) from an HTML file -- typically a Confluence
"Export to HTML" page. Uses BeautifulSoup4 if it is installed for more
robust parsing, and otherwise falls back to a small stdlib
html.parser-based extractor so the script has no hard dependency.

Usage:
    python parse_html.py <file.html> [--artifact-id SRC-002] [--out out.json]
"""

from __future__ import annotations

import argparse
import re
from html.parser import HTMLParser
from pathlib import Path

from common import read_text_file, sha256_of_file, slugify, save_json, eprint

HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
SKIP_TEXT_TAGS = {"script", "style", "noscript"}
CODE_TAGS = {"pre", "code"}

try:
    from bs4 import BeautifulSoup  # type: ignore
    HAVE_BS4 = True
except ImportError:
    HAVE_BS4 = False


def github_slug(text: str, seen: dict) -> str:
    slug = slugify(text)
    if slug not in seen:
        seen[slug] = 0
        return slug
    seen[slug] += 1
    return f"{slug}-{seen[slug]}"


def _clean_text(text: str) -> str:
    return re.sub(r"[ \t]+", " ", re.sub(r"\r\n?", "\n", text)).strip()


def parse_with_bs4(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    for tag in soup(list(SKIP_TEXT_TAGS)):
        tag.decompose()

    slug_seen: dict = {}
    sections = []
    stack: list[dict] = []
    for tag in soup.find_all(list(HEADING_TAGS) + ["p", "li", "table"]):
        if tag.name in HEADING_TAGS:
            level = int(tag.name[1])
            heading_text = _clean_text(tag.get_text(" "))
            anchor = tag.get("id") or github_slug(heading_text, slug_seen)
            while stack and stack[-1]["level"] >= level:
                stack.pop()
            path = " > ".join([s["heading"] for s in stack] + [heading_text])
            section = {"heading": heading_text, "level": level, "anchor": anchor, "path": path, "text": ""}
            sections.append(section)
            stack.append(section)
        else:
            if stack:
                piece = _clean_text(tag.get_text(" "))
                if piece:
                    stack[-1]["text"] += (piece + "\n")

    tables = []
    for t_idx, table in enumerate(soup.find_all("table")):
        header = [_clean_text(th.get_text(" ")) for th in table.find_all("th")]
        rows = []
        for tr in table.find_all("tr"):
            cells = tr.find_all("td")
            if cells:
                rows.append([_clean_text(td.get_text(" ")) for td in cells])
        tables.append({"index": t_idx, "header": header, "rows": rows})

    links = []
    for a in soup.find_all("a", href=True):
        links.append({"text": _clean_text(a.get_text(" ")), "url": a["href"]})

    code_blocks = []
    for pre in soup.find_all("pre"):
        code_blocks.append({"content": pre.get_text("\n")})

    images = []
    for img in soup.find_all("img"):
        images.append({
            "src": img.get("src", ""),
            "alt": img.get("alt", ""),
            "title": img.get("title", ""),
        })

    for s in sections:
        s["text"] = s["text"].strip()

    return {
        "title": title,
        "sections": sections,
        "tables": tables,
        "links": links,
        "code_blocks": code_blocks,
        "images": images,
    }


class _FallbackHTMLExtractor(HTMLParser):
    """Minimal stdlib fallback used when bs4 is unavailable. Handles the
    common well-formed export case; malformed HTML may parse partially."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.sections: list[dict] = []
        self.tables: list[dict] = []
        self.links: list[dict] = []
        self.code_blocks: list[dict] = []
        self.images: list[dict] = []

        self._stack: list[dict] = []
        self._tag_stack: list[str] = []
        self._in_title = False
        self._in_skip = 0
        self._slug_seen: dict = {}

        self._cur_heading_level = None
        self._cur_heading_text = []

        self._in_table = 0
        self._cur_table = None
        self._cur_row = None
        self._cur_cell = None
        self._in_th = False

        self._in_pre = 0
        self._pre_buffer = []

        self._in_link = False
        self._link_href = ""
        self._link_text = []

    def handle_starttag(self, tag, attrs):
        attrs_d = dict(attrs)
        self._tag_stack.append(tag)

        if tag in SKIP_TEXT_TAGS:
            self._in_skip += 1
            return
        if tag == "title":
            self._in_title = True
            return
        if tag in HEADING_TAGS:
            self._cur_heading_level = int(tag[1])
            self._cur_heading_text = []
            self._cur_heading_anchor = attrs_d.get("id", "")
            return
        if tag == "table":
            self._in_table += 1
            self._cur_table = {"index": len(self.tables), "header": [], "rows": []}
            return
        if tag == "tr" and self._in_table:
            self._cur_row = []
            return
        if tag in ("td", "th") and self._in_table:
            self._cur_cell = []
            self._in_th = tag == "th"
            return
        if tag in CODE_TAGS:
            self._in_pre += 1
            return
        if tag == "a":
            self._in_link = True
            self._link_href = attrs_d.get("href", "")
            self._link_text = []
            return
        if tag == "img":
            self.images.append({
                "src": attrs_d.get("src", ""),
                "alt": attrs_d.get("alt", ""),
                "title": attrs_d.get("title", ""),
            })
            return

    def handle_endtag(self, tag):
        if self._tag_stack and self._tag_stack[-1] == tag:
            self._tag_stack.pop()

        if tag in SKIP_TEXT_TAGS:
            self._in_skip = max(0, self._in_skip - 1)
            return
        if tag == "title":
            self._in_title = False
            return
        if tag in HEADING_TAGS and self._cur_heading_level is not None:
            heading_text = _clean_text("".join(self._cur_heading_text))
            level = self._cur_heading_level
            anchor = self._cur_heading_anchor or github_slug(heading_text, self._slug_seen)
            while self._stack and self._stack[-1]["level"] >= level:
                self._stack.pop()
            path = " > ".join([s["heading"] for s in self._stack] + [heading_text])
            section = {"heading": heading_text, "level": level, "anchor": anchor, "path": path, "text": ""}
            self.sections.append(section)
            self._stack.append(section)
            self._cur_heading_level = None
            return
        if tag == "table" and self._in_table:
            self._in_table -= 1
            if self._cur_table is not None:
                self.tables.append(self._cur_table)
            self._cur_table = None
            return
        if tag == "tr" and self._cur_row is not None:
            if self._cur_row:
                self._cur_table["rows"].append(self._cur_row)
            self._cur_row = None
            return
        if tag in ("td", "th") and self._cur_cell is not None:
            text = _clean_text("".join(self._cur_cell))
            if self._in_th:
                self._cur_table["header"].append(text)
            elif self._cur_row is not None:
                self._cur_row.append(text)
            self._cur_cell = None
            return
        if tag in CODE_TAGS and self._in_pre:
            self._in_pre -= 1
            if self._in_pre == 0 and self._pre_buffer:
                self.code_blocks.append({"content": "".join(self._pre_buffer)})
                self._pre_buffer = []
            return
        if tag == "a" and self._in_link:
            self.links.append({"text": _clean_text("".join(self._link_text)), "url": self._link_href})
            self._in_link = False
            return

    def handle_data(self, data):
        if self._in_skip:
            return
        if self._in_title:
            self.title += data
            return
        if self._cur_heading_level is not None:
            self._cur_heading_text.append(data)
        if self._in_pre:
            self._pre_buffer.append(data)
        if self._in_link:
            self._link_text.append(data)
        if self._cur_cell is not None:
            self._cur_cell.append(data)
        elif self._stack:
            piece = _clean_text(data)
            if piece:
                self._stack[-1]["text"] += (piece + "\n")

    def finalize(self):
        self.title = self.title.strip()
        for s in self.sections:
            s["text"] = s["text"].strip()


def parse_with_fallback(html: str) -> dict:
    extractor = _FallbackHTMLExtractor()
    extractor.feed(html)
    extractor.finalize()
    return {
        "title": extractor.title,
        "sections": extractor.sections,
        "tables": extractor.tables,
        "links": extractor.links,
        "code_blocks": extractor.code_blocks,
        "images": extractor.images,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="Path to the HTML file to parse")
    parser.add_argument("--artifact-id", default="SRC-001", help="Source artifact ID (e.g. SRC-002)")
    parser.add_argument("--out", default="-", help="Output JSON path, or '-' for stdout")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        eprint(f"error: file not found: {path}")
        return 1

    html = read_text_file(path)
    parsed = parse_with_bs4(html) if HAVE_BS4 else parse_with_fallback(html)
    if not HAVE_BS4:
        eprint("note: bs4 not installed, used stdlib html.parser fallback (pip install beautifulsoup4 for more robust parsing)")

    result = {
        "artifact": {
            "id": args.artifact_id,
            "file_name": path.name,
            "type": "html",
            "location": str(path),
            "hash": sha256_of_file(path),
        },
        "title": parsed["title"],
        "sections": parsed["sections"],
        "diagrams_detected": len(parsed["images"]) > 0,
        "images": parsed["images"],
        "tables": parsed["tables"],
        "code_blocks": parsed["code_blocks"],
        "links": parsed["links"],
        "parser": "bs4" if HAVE_BS4 else "stdlib-fallback",
        "stats": {
            "section_count": len(parsed["sections"]),
            "table_count": len(parsed["tables"]),
            "image_count": len(parsed["images"]),
            "link_count": len(parsed["links"]),
            "code_block_count": len(parsed["code_blocks"]),
        },
    }

    save_json(result, args.out)
    if args.out != "-":
        eprint(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
