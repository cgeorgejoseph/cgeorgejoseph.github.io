#!/usr/bin/env python3
"""Render citations/og.png (1200x627), the preview image LinkedIn shows for the
citations page. Reads citations/data.json.

Usage: python3 _tools/render_og.py --fonts DIR
DIR holds the @fontsource woff2 files (outfit-latin-*-normal.woff2 and
cormorant-garamond-latin-*-normal.woff2), e.g. from
`npm i @fontsource/outfit @fontsource/cormorant-garamond`.
Needs Playwright with a Chrome or Chromium install.
"""
import argparse
import json
import os
from datetime import date

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--chrome", default="/usr/bin/google-chrome")
    a = ap.parse_args()
    d = json.load(open(os.path.join(ROOT, "citations", "data.json"), encoding="utf-8"))
    t = d["totals"]
    upd = date.fromisoformat(d["updated"]).strftime("%B %Y")
    py = d["per_year"]
    vmax = max(p["citations"] for p in py)
    bars = "".join(
        f'<div class="b{" p" if p.get("partial") else ""}" style="height:{p["citations"] / vmax * 100:.1f}%"></div>'
        for p in py)
    f = lambda name: "file://" + os.path.join(os.path.abspath(a.fonts), name)
    page = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:O;font-weight:400;src:url({f('outfit-latin-400-normal.woff2')})}}
@font-face{{font-family:O;font-weight:500;src:url({f('outfit-latin-500-normal.woff2')})}}
@font-face{{font-family:O;font-weight:600;src:url({f('outfit-latin-600-normal.woff2')})}}
@font-face{{font-family:C;font-weight:600;src:url({f('cormorant-garamond-latin-600-normal.woff2')})}}
@font-face{{font-family:C;font-weight:700;src:url({f('cormorant-garamond-latin-700-normal.woff2')})}}
@font-face{{font-family:C;font-style:italic;font-weight:600;src:url({f('cormorant-garamond-latin-600-italic.woff2')})}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1200px;height:627px;background:#fdfcfa;font-family:O;color:#16191f;position:relative;overflow:hidden}}
body:before{{content:'';position:absolute;inset:0;background:repeating-linear-gradient(to bottom,transparent 0 47px,rgba(22,25,31,.045) 47px 48px)}}
.wrap{{position:absolute;inset:0;padding:64px 72px;display:grid;grid-template-columns:1fr 360px;gap:56px}}
.tag{{font-size:19px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:#8b1f3f;display:flex;align-items:center;gap:14px}}
.tag:before{{content:'';width:40px;height:2px;background:#8b1f3f}}
h1{{font-family:C;font-weight:600;font-size:76px;line-height:1.02;margin-top:26px;letter-spacing:-.01em}}
h1 em{{color:#8b1f3f}}
.aff{{font-size:22px;color:#6b6560;margin-top:18px;border-left:3px solid #c9a84c;padding-left:16px}}
.left{{display:flex;flex-direction:column}}
.what{{font-family:C;font-weight:600;font-style:italic;font-size:44px;line-height:1.15;color:#16191f}}
.stats{{display:flex;gap:52px;margin-top:auto;margin-bottom:56px}}
.v{{font-family:C;font-weight:700;font-size:96px;line-height:.9;font-variant-numeric:lining-nums;font-feature-settings:'lnum' 1}}
.l{{font-size:16px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#6b6560;margin-top:10px}}
.right{{display:flex;flex-direction:column;justify-content:flex-end}}
.chart{{height:300px;display:flex;align-items:flex-end;gap:12px;border-bottom:2px solid #a09890;padding:0 4px}}
.b{{flex:1;background:#8b1f3f;border-radius:5px 5px 0 0}}
.b.p{{background:repeating-linear-gradient(45deg,#8b1f3f 0 3px,#d9b4bf 3px 7px)}}
.cap{{display:flex;justify-content:space-between;font-size:17px;color:#6b6560;margin-top:10px}}
.ct{{font-size:17px;font-weight:500;letter-spacing:.06em;text-transform:uppercase;color:#6b6560;margin-bottom:14px}}
.foot{{position:absolute;left:72px;right:72px;bottom:40px;display:flex;justify-content:space-between;font-size:18px;color:#6b6560}}
.foot b{{color:#8b1f3f;font-weight:500}}
</style></head><body><div class="wrap"><div class="left">
<div class="tag">Research citations</div>
<h1>George <em>Joseph</em>, Ph.D.</h1>
<div class="aff">Rajagiri Business School, Kochi</div>
<div class="stats"><div class="what">Citation metrics<br>and most-cited works</div></div></div>
<div class="right"><div class="ct">Citations per year</div><div class="chart">{bars}</div>
</div></div>
<div class="foot"><span>From Google Scholar</span><b>cgeorgejoseph.github.io/citations</b></div>
</body></html>"""
    tmp = os.path.join(ROOT, "_tools", "_og.html")
    open(tmp, "w", encoding="utf-8").write(page)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=a.chrome, args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 1200, "height": 627})
        pg.goto("file://" + tmp)
        pg.wait_for_timeout(400)
        pg.screenshot(path=os.path.join(ROOT, "citations", "og.png"))
        b.close()
    os.remove(tmp)
    print("wrote citations/og.png")


if __name__ == "__main__":
    main()
