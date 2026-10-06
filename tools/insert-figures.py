#!/usr/bin/env python3
"""Insert the downloaded original a16z charts into the two briefing pages.

Figures are placed at the end of the section whose argument they support, and they
span the full prose column rather than sitting inside one language column of a
.pair block, because an image carries no language.
"""
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = json.loads((ROOT / "tools" / "originals-manifest.json").read_text(encoding="utf-8"))
BY_FILE = {(m["slug"], m["file"]): m for m in MANIFEST}

SOURCE = {
    "state-of-markets-ii": (
        "a16z Growth",
        "https://a16z.com/state-of-markets-ii/",
    ),
    "top-100-gen-ai-apps-7": (
        "a16z Consumer",
        "https://a16z.com/100-gen-ai-apps-7/",
    ),
}

# slug -> ordered list of (section anchor after which to append, file name)
PLAN = {
    "state-of-markets-ii": [
        ("intro", "hero-cover.jpg"),
        ("cycle", "tech-earnings-3.8x-non-tech.png"),
        ("cycle", "tech-contributed-76pct-earnings-growth.png"),
        ("atoms", "hyperscaler-fcf-semiconductor-fcf.png"),
        ("gpu", "gpus-more-valuable-over-time.png"),
        ("adoption", "69pct-live-ai-deployment-2pct-tracked-metric.png"),
        ("adoption", "more-households-paying-for-ai-scaled.png"),
        ("saas", "software-profitability-growth-scatter.png"),
        ("ahead", "looking-ahead.jpg"),
    ],
    "top-100-gen-ai-apps-7": [
        ("intro", "spending-and-traffic-different-rankings-scaled.jpg"),
        # PLAN lists each section's figures bottom-up, because insertion walks the
        # plan in reverse. Result on the page matches the a16z article's own order.
        ("labs", "claude-for-work-gemini-consumers-chatgpt-both.png"),
        ("labs", "openai-leads-anthropic-in-47-states.png"),
        ("labs", "openai-spending-less-skewed-gender-income.png"),
        ("labs", "chatgpt-reclaimed-lead-net-new-subscriptions.png"),
        ("labs", "claude-converts-high-cost-subscriptions.png"),
        ("labs", "in-paid-us-subscribers-chatgpt-leads.png"),
        ("spend", "top-50-consumer-ai-apps-by-monthly-revenue.png"),
        ("spend", "top-50-mobile-apps-by-mau.png"),
        ("spend", "top-50-web-products-by-monthly-visits.png"),
        ("spend", "only-seven-products-rank-top-on-all-three.png"),
        ("spend", "what-biggest-spenders-overindex-on.png"),
        ("spend", "consumer-spending-growth-concentrated-at-top.png"),
        ("spend", "three-years-in-chatgpt-holds-lead-paid.png"),
        ("agents", "muse-vs-threads-us-canada.png"),
        ("agents", "muse-mobile-downloads-by-day.png"),
        ("agents", "coding-and-technical-automation-lead.png"),
        ("agents", "daily-visits-personal-agent-signup-pages.png"),
        ("startups", "where-consumer-ai-has-room-to-grow-scaled.jpg"),
        ("models", "media-built-subscription-economy.png"),
        ("models", "how-consumer-ai-companies-monetize.png"),
    ],
}

MIME = {"png": "image/png", "jpeg": "image/jpeg", "webp": "image/webp"}


def build_figure(slug: str, fname: str) -> str:
    m = BY_FILE[(slug, fname)]
    org, article_url = SOURCE[slug]
    assert m["format"] in MIME, f"unexpected format {m['format']} for {fname}"
    src = f"../assets/img/{slug}/{fname}"
    cap = html.escape(m["caption"], quote=True)
    return (
        '\n<figure class="fig">'
        f'<a class="fig-link" href="{src}" target="_blank" rel="noopener" '
        f'aria-label="打开原尺寸原图：{cap}">'
        f'<img src="{src}" width="{m["width"]}" height="{m["height"]}" loading="lazy" '
        f'decoding="async" alt="原图：{cap}"></a>'
        f'<figcaption><span class="fig-label">原图</span>{html.escape(m["caption"])}'
        f' · {org} · <a href="{article_url}" target="_blank" rel="noopener">原文 ↗</a>'
        f' · <a href="{src}" target="_blank" rel="noopener">原尺寸 ↗</a></figcaption>'
        "</figure>\n"
    )


def process(slug: str) -> None:
    path = ROOT / "reports" / f"{slug}.html"
    text = path.read_text(encoding="utf-8")
    if 'figure class="fig"' in text:
        raise SystemExit(f"{path.name} already contains figures; refusing to double-insert")

    plan = PLAN[slug]
    # Process in reverse: each insertion at a given cut point pushes earlier insertions
    # to the right, so reversed processing makes the page read in PLAN order.
    for anchor, fname in reversed(plan):
        block = build_figure(slug, fname)
        start = text.find(f'<h2 id="{anchor}"')
        if start == -1:
            raise SystemExit(f"{path.name}: missing anchor #{anchor}")
        after = text.find('\n<h2 id="', start)
        if after == -1:
            # Last section: stop at the end of the markdown body instead.
            after = text.rfind("      </div>\n    </article>")
            if after == -1:
                raise SystemExit(f"{path.name}: cannot find end of body")
        text = text[:after] + block + text[after:]

    path.write_text(text, encoding="utf-8")
    print(f"{path.name}: inserted {len(plan)} figures")


def main() -> None:
    for slug in PLAN:
        process(slug)


if __name__ == "__main__":
    main()
