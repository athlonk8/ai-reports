#!/usr/bin/env python3
"""Force-load every image on the briefing pages through real Chrome and report
naturalWidth/naturalHeight, so a lazy placeholder can never be mistaken for a render."""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PAGES = ["index.html", "reports/state-of-markets-ii.html", "reports/top-100-gen-ai-apps-7.html"]


def audit_page(rel: str) -> dict:
    url = (ROOT / rel).as_uri()
    html_doc = f"""<!doctype html><meta charset="utf-8"><title>audit</title><body>
<pre id="out">pending</pre>
<script>
(async () => {{
  const res = await fetch({json.dumps(url)});
  const text = await res.text();
  const doc = new DOMParser().parseFromString(text, "text/html");
  const imgs = [...doc.querySelectorAll("img")];
  const results = [];
  await Promise.all(imgs.map(img => new Promise(done => {{
    const probe = new Image();
    probe.onload = () => done(results.push({{src: img.getAttribute("src"),
      nat: [probe.naturalWidth, probe.naturalHeight], declared: [img.getAttribute("width"), img.getAttribute("height")], ok: true}}));
    probe.onerror = () => done(results.push({{src: img.getAttribute("src"), ok: false}}));
    probe.src = new URL(img.getAttribute("src"), {json.dumps(url)}).href;
  }})));
  document.getElementById("out").textContent = "AUDITJSON" + JSON.stringify(results) + "AUDITEND";
}})();
</script></body>"""
    tmp = pathlib.Path.home() / "AppData/Local/Temp/audit-page.html"
    tmp.write_text(html_doc, encoding="utf-8")
    out = subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
         "--allow-file-access-from-files", "--virtual-time-budget=20000",
         "--dump-dom", tmp.as_uri()],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180,
    )
    m = re.search(r"AUDITJSON(\[.*?\])AUDITEND", out.stdout, re.S)
    if not m:
        print(f"  !! could not read audit JSON for {rel}")
        print("  stderr:", (out.stderr or "")[-400:])
        return {"parse_error": True}
    return {"results": json.loads(m.group(1).replace("&quot;", '"'))}


bad = []
for rel in PAGES:
    data = audit_page(rel)
    res = data.get("results", [])
    print(f"\n=== {rel} === ({len(res)} images)")
    for r in res:
        if not r.get("ok"):
            bad.append(f"{rel}: FAILED TO LOAD {r['src']}")
            print("  FAIL", r["src"])
            continue
        declared = r.get("declared") or [None, None]
        nat = r["nat"]
        mismatch = ""
        if all(declared) and [str(x) for x in nat] != [str(x) for x in declared]:
            mismatch = f"  <-- declared {declared} != natural {nat}"
            bad.append(f"{rel}: {r['src']} declared {declared} but is {nat}")
        print(f"  OK {nat[0]}x{nat[1]}  {pathlib.PurePosixPath(r['src']).name}{mismatch}")

if bad:
    print("\nPROBLEMS:")
    for b in bad:
        print("  -", b)
    sys.exit(1)
print("\nEvery image loaded, and every declared size matches the real file.")
