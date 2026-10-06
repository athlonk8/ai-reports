#!/usr/bin/env python3
"""Download the original chart images from the two a16z articles and write a manifest.

Images are stored per-report under assets/img/<slug>/ and the manifest records the
intrinsic size so the generated <img> tags can carry width/height and avoid layout shift.
"""
import io
import json
import pathlib
import urllib.request
import urllib.error

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
CDN = "https://d1lamhf6l6yk6d.cloudfront.net/uploads"

# (slug, local file name, cdn path after /uploads, caption used on the page)
IMAGES = [
    # ---- State of Markets II · David George · 2026-09-30 ----
    ("state-of-markets-ii", "hero-cover.jpg",
     "2026/09/9ec4c533-a6bc-4afb-8a73-16497f12c022_2844x1600-scaled.jpg",
     "a16z 原文题图"),
    ("state-of-markets-ii", "tech-earnings-3.8x-non-tech.png",
     "2026/09/Tech-Earnings-Have-Grown-3.8x-More-Than-Non-Tech.png",
     "Tech earnings have grown 3.8× more than non-tech"),
    ("state-of-markets-ii", "tech-contributed-76pct-earnings-growth.png",
     "2026/09/Tech-Contributed-76-Of-Earnings-Growth.png",
     "Tech contributed 76% of earnings growth"),
    ("state-of-markets-ii", "hyperscaler-fcf-semiconductor-fcf.png",
     "2026/09/Hyperscaler-FCF-Has-Become-Semiconductor-FCF.png",
     "Hyperscaler FCF has become semiconductor FCF"),
    ("state-of-markets-ii", "gpus-more-valuable-over-time.png",
     "2026/09/Reports-Of-Obsolescence-Greatly-Exaggerated_-GPUs-Getting-More-Valuable-Over-Time.png",
     "Reports of obsolescence greatly exaggerated: GPUs getting more valuable over time"),
    ("state-of-markets-ii", "69pct-live-ai-deployment-2pct-tracked-metric.png",
     "2026/09/69-of-the-SP-500-Point-To-A-Live-AI-deployment.-Only-2-Disclose-A-Metric-They-Track-Over-Time.png",
     "69% of the S&P 500 point to a live AI deployment; only 2% disclose a metric they track over time"),
    ("state-of-markets-ii", "more-households-paying-for-ai-scaled.png",
     "2026/09/More-and-More-Households-are-Paying-for-AI-scaled.png",
     "More and more households are paying for AI"),
    ("state-of-markets-ii", "software-profitability-growth-scatter.png",
     "2026/09/0967b1ef-9dbd-4005-b834-d3f3c363b0de_2000x1915.png",
     "软件板块盈利与增长的散点图（原文未给出坐标）"),
    ("state-of-markets-ii", "looking-ahead.jpg",
     "2026/09/Looking-Ahead-1.jpg",
     "Looking ahead"),

    # ---- The Top 100 Gen AI Consumer Apps — 7th Edition · Olivia Moore · 2026-10-05 ----
    ("top-100-gen-ai-apps-7", "top-50-consumer-ai-apps-by-monthly-revenue.png",
     "2026/10/Top-Gen-AI-Apps-Top-50-List-1.png",
     "The top 50 consumer AI apps, by monthly revenue"),
    ("top-100-gen-ai-apps-7", "top-50-mobile-apps-by-mau.png",
     "2026/10/Top-Gen-AI-Apps-Top-50-List-3.png",
     "The top 50 gen AI mobile apps, by monthly active users"),
    ("top-100-gen-ai-apps-7", "top-50-web-products-by-monthly-visits.png",
     "2026/10/Top-Gen-AI-Web-Top-50-List-v2-2.png",
     "The top 50 gen AI web products, by unique monthly visits"),
    ("top-100-gen-ai-apps-7", "spending-and-traffic-different-rankings-scaled.jpg",
     "2026/10/Spending-and-Traffic-Produce-Different-Rankings-scaled.jpg",
     "Spending and traffic produce different rankings"),
    ("top-100-gen-ai-apps-7", "where-consumer-ai-has-room-to-grow-scaled.jpg",
     "2026/10/Where-Consumer-AI-Has-Room-to-Grow-scaled.jpg",
     "Where consumer AI has room to grow"),
    ("top-100-gen-ai-apps-7", "how-consumer-ai-companies-monetize.png",
     "2026/10/How-Consumer-AI-Companies-Monetize-1.png",
     "How consumer AI companies monetize"),
    ("top-100-gen-ai-apps-7", "consumer-spending-growth-concentrated-at-top.png",
     "2026/10/Consumer-Spending-Growth-is-Concentrated-at-the-Very-Top.png",
     "Consumer spending growth is concentrated at the very top"),
    ("top-100-gen-ai-apps-7", "what-biggest-spenders-overindex-on.png",
     "2026/10/What-AIs-Biggest-Consumer-Spenders-Overindex-On.png",
     "What AI's biggest consumer spenders overindex on"),
    ("top-100-gen-ai-apps-7", "coding-and-technical-automation-lead.png",
     "2026/10/Coding-and-Technical-Automation-Lead-Task-Discussion.png",
     "Coding and technical automation lead task discussion"),
    ("top-100-gen-ai-apps-7", "chatgpt-reclaimed-lead-net-new-subscriptions.png",
     "2026/10/ChatGPT-Has-Reclaimed-the-Lead-in-Net-New-Subscriptions.png",
     "ChatGPT has reclaimed the lead in net new subscriptions"),
    ("top-100-gen-ai-apps-7", "claude-converts-high-cost-subscriptions.png",
     "2026/10/Claude-Converts-Users-More-Aggressively-to-High-Cost-Subscriptions.png",
     "Claude converts users more aggressively to high-cost subscriptions"),
    ("top-100-gen-ai-apps-7", "three-years-in-chatgpt-holds-lead-paid.png",
     "2026/10/Three-Years-in-ChatGPT-is-Holding-The-Lead-in-Paid-Users.png",
     "Three years in, ChatGPT is holding the lead in paid users"),
    ("top-100-gen-ai-apps-7", "in-paid-us-subscribers-chatgpt-leads.png",
     "2026/10/In-Paid-U.S.-Subscribers-ChatGPT-Leads-But-Claude-Caught-Gemini.png",
     "In paid U.S. subscribers, ChatGPT leads but Claude caught Gemini"),
    ("top-100-gen-ai-apps-7", "media-built-subscription-economy.png",
     "2026/10/Media-Built-the-Subscription-Economy-ChatGPT-is-Already-Breaking-In.png",
     "Media built the subscription economy; ChatGPT is already breaking in"),
    ("top-100-gen-ai-apps-7", "openai-leads-anthropic-in-47-states.png",
     "2026/10/OpenAI-Leads-Anthropic-in-47-States.png",
     "OpenAI leads Anthropic in 47 states"),
    ("top-100-gen-ai-apps-7", "openai-spending-less-skewed-gender-income.png",
     "2026/10/OpenAI-Spending-is-Less-Skewed-by-Gender-and-Income.png",
     "OpenAI spending is less skewed by gender and income"),
    ("top-100-gen-ai-apps-7", "only-seven-products-rank-top-on-all-three.png",
     "2026/10/Only-Seven-Products-Rank-in-the-Top-Group-on-Web-Mobile-and-Revenue.png",
     "Only seven products rank in the top group on web, mobile, and revenue"),
    ("top-100-gen-ai-apps-7", "claude-for-work-gemini-consumers-chatgpt-both.png",
     "2026/10/Claude-for-work-Gemini-for-consumers-ChatGPT-for-both.png",
     "Claude for work, Gemini for consumers, ChatGPT for both"),
    ("top-100-gen-ai-apps-7", "muse-vs-threads-us-canada.png",
     "2026/10/Muse-vs.-Threads_-U.S.-and-Canada.png",
     "Muse vs. Threads: U.S. and Canada"),
    ("top-100-gen-ai-apps-7", "muse-mobile-downloads-by-day.png",
     "2026/10/Muse-Mobile-Downloads-by-Day.png",
     "Muse mobile downloads by day"),
    ("top-100-gen-ai-apps-7", "daily-visits-personal-agent-signup-pages.png",
     "2026/10/Daily-Visits-to-Personal-Agent-Signup-Pages.png",
     "Daily visits to personal agent signup pages"),
]

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/*,*/*"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read()


def main() -> None:
    manifest = []
    failures = []
    for slug, fname, cdn_path, caption in IMAGES:
        out_dir = ROOT / "assets" / "img" / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / fname
        url = f"{CDN}/{cdn_path}"
        try:
            raw = fetch(url)
            img = Image.open(io.BytesIO(raw))
            img.load()
            fmt = (img.format or "").lower()
            out.write_bytes(raw)
            manifest.append({
                "slug": slug,
                "file": fname,
                "url": url,
                "caption": caption,
                "width": img.width,
                "height": img.height,
                "format": fmt,
                "bytes": len(raw),
            })
            print(f"OK   {slug}/{fname}  {img.width}x{img.height}  {fmt}  {len(raw)/1024:.0f} KB")
        except Exception as exc:  # noqa: BLE001 - report and continue
            failures.append({"slug": slug, "file": fname, "url": url, "error": repr(exc)})
            print(f"FAIL {slug}/{fname}  {exc!r}")

    (ROOT / "tools" / "originals-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    total = sum(m["bytes"] for m in manifest)
    print(f"\n{len(manifest)} downloaded, {total/1024/1024:.2f} MB total, {len(failures)} failures")
    if failures:
        print(json.dumps(failures, ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
