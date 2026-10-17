#!/usr/bin/env python3
"""Static consistency checks for evidence-gate.dev (stdlib only).

Run: python3 tools/check_site.py
Fails on: dead/forbidden domains, inconsistent gate counts, unpinned @v1 examples,
self-referencing CTA buttons, and HTML tag imbalance.
"""
from __future__ import annotations

import pathlib
import re
import sys
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILES = [p for p in ROOT.rglob("*") if p.suffix in {".html", ".txt", ".xml"} and ".git" not in p.parts]
FORBIDDEN = [
    "allnew.co.jp",            # domain does not exist
    "docs.evidence-gate.dev",  # subdomain does not exist
    "ai-governance.html",      # 404 on allnew.work
    "support@evidence-gate.dev",  # no MX / email routing yet
    "evidence-gate-action@v1<",   # v1 tag lacks advertised features
]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr",
        "path", "rect", "line", "circle", "polygon", "polyline", "ellipse", "stop", "use"}


class Balance(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.errors.append(f"unclosed <{self.stack.pop()}> before </{tag}> at {self.getpos()}")
            self.stack.pop()
        else:
            self.errors.append(f"stray </{tag}> at {self.getpos()}")


def main() -> int:
    errors: list[str] = []
    counts: set[str] = set()
    for p in FILES:
        text = p.read_text(encoding="utf-8")
        rel = p.relative_to(ROOT)
        for bad in FORBIDDEN:
            if bad in text:
                errors.append(f"{rel}: forbidden reference '{bad}'")
        counts.update(re.findall(r"(\d+)\s*(?:種の?)?\s*(?:gate types|ゲートタイプ)", text))
        if p.suffix == ".html":
            if re.search(r'href="#pricing"\s+class="btn', text):
                errors.append(f"{rel}: CTA button links to #pricing (self-reference)")
            b = Balance()
            b.feed(text)
            errors += [f"{rel}: {e}" for e in b.errors[:5]]
    if len(counts) > 1:
        errors.append(f"inconsistent gate counts: {sorted(counts)}")
    for e in errors:
        print("ERROR:", e)
    print(f"checked {len(FILES)} files, gate counts={sorted(counts)}, errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
