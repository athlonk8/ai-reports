#!/usr/bin/env python3
"""Remove all generated <figure class="fig"> blocks from the briefing pages.

Used together with insert-figures.py when the figure placement needs to be redone.
Only blocks produced by that script are removed; everything else is left byte-identical.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = ["state-of-markets-ii", "top-100-gen-ai-apps-7"]

for slug in PAGES:
    path = ROOT / "reports" / f"{slug}.html"
    text = path.read_text(encoding="utf-8")
    block = re.compile(r'\n?<figure class="fig">.*?</figure>\n?', re.S)
    text, n = block.subn("\n", text)
    # collapse any runs of blank lines the removal created
    text = re.sub(r"\n{3,}", "\n\n", text)
    path.write_text(text, encoding="utf-8")
    print(f"{path.name}: removed {n} figures")
