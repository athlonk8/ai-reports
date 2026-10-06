#!/usr/bin/env python3
"""Verify the briefing pages: every figure image resolves, no figure sits inside a .pair,
source links are all attribution, and no stale rehosting language survives."""
import html
import pathlib
import re
import sys
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = ["index.html", "materials.html",
         "reports/state-of-markets-ii.html", "reports/top-100-gen-ai-apps-7.html"]

problems = []


class FigureAudit(HTMLParser):
    """Track whether an <img> appears inside a .pair block and collect img sources."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []          # (tag, in_pair)
        self.pair_depth = 0
        self.imgs = []           # (src, inside_pair)
        self.figures = 0
        self.captions = 0
        self.figcaptions = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "")
        is_pair = tag == "div" and "pair" in cls.split()
        if tag == "figure" and "fig" in cls.split():
            self.figures += 1
        if tag == "p" and "caption" in cls.split():
            self.captions += 1
        if tag == "figcaption":
            self.figcaptions += 1
        if tag == "img":
            self.imgs.append((a.get("src", ""), self.pair_depth > 0, a.get("width"), a.get("height")))
        if is_pair:
            self.pair_depth += 1
        if tag not in ("img", "br", "meta", "link", "input", "hr"):
            self.stack.append((tag, is_pair))

    def handle_startendtag(self, tag, attrs):
        if tag == "img":
            a = dict(attrs)
            self.imgs.append((a.get("src", ""), self.pair_depth > 0, a.get("width"), a.get("height")))

    def handle_endtag(self, tag):
        while self.stack:
            t, was_pair = self.stack.pop()
            if was_pair:
                self.pair_depth -= 1
            if t == tag:
                break


for rel in PAGES:
    path = ROOT / rel
    if not path.exists():
        problems.append(f"{rel}: file missing")
        continue
    text = path.read_text(encoding="utf-8")

    audit = FigureAudit()
    audit.feed(text)

    for src, in_pair, w, h in audit.imgs:
        if not src:
            problems.append(f"{rel}: <img> with empty src")
            continue
        if in_pair:
            problems.append(f"{rel}: {src} sits inside a .pair block")
        target = (path.parent / html.unescape(src)).resolve()
        if not target.exists():
            problems.append(f"{rel}: broken image path {src}")
        if not w or not h:
            problems.append(f"{rel}: {src} missing width/height (layout shift risk)")
        if target.exists() and target.suffix.lower() in (".png", ".jpg", ".jpeg"):
            head = target.read_bytes()[:12]
            if target.suffix.lower() == ".png" and head[:8] != b"\x89PNG\r\n\x1a\n":
                problems.append(f"{rel}: {src} is not really a PNG")
            if target.suffix.lower() in (".jpg", ".jpeg") and head[:2] != b"\xff\xd8":
                problems.append(f"{rel}: {src} is not really a JPEG")

    # every figure must carry a caption and an attribution link
    if audit.figures != audit.figcaptions:
        problems.append(f"{rel}: {audit.figures} figures but {audit.figcaptions} figcaptions")
    for m in re.finditer(r"<figure class=\"fig\">(.*?)</figure>", text, re.S):
        block = m.group(1)
        if "a16z.com" not in block:
            problems.append(f"{rel}: a figure has no a16z attribution link")

    # stale rehosting language
    for bad in ("不转存", "原图留在 a16z", "原图留在出处"):
        if bad in text:
            problems.append(f"{rel}: stale wording {bad!r}")
    if audit.captions:
        problems.append(f"{rel}: {audit.captions} leftover <p class=\"caption\"> block(s)")

    # raw cloudfront links left in the body are fine only for non-chart resources
    for link in re.findall(r'href="(https://d1lamhf6l6yk6d\.cloudfront\.net/[^"]+)"', text):
        if re.search(r"\.(png|jpe?g|webp)$", link):
            problems.append(f"{rel}: leftover cloudfront chart link {link}")

    print(f"{rel}: {audit.figures} figures, {len(audit.imgs)} inline images")

if problems:
    print("\nPROBLEMS:")
    for p in problems:
        print("  -", p)
    sys.exit(1)
print("\nAll checks passed.")
