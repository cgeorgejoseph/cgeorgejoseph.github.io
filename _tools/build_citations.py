#!/usr/bin/env python3
"""Build /citations/index.html from /citations/data.json.

Refresh routine (monthly):
  1. Update citations/data.json with the current figures from the Google Scholar
     profile (totals, per-year counts, per-work counts, "updated" date).
  2. Run:  python3 _tools/build_citations.py
  3. Optionally re-render the LinkedIn preview image:
           python3 _tools/render_og.py --fonts <dir with Outfit/Cormorant woff2>
  4. Commit and push.

Folders starting with "_" are not published by GitHub Pages, so this script
stays private to the repository.
"""
import html
import json
import os
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "citations", "data.json")
OUT = os.path.join(ROOT, "citations", "index.html")
SITE = "https://cgeorgejoseph.github.io"
SCHOLAR_USER = "mU9Ix8IAAAAJ"


def esc(s):
    return html.escape(str(s), quote=True)


def long_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B %Y')}"


def nice_ceiling(v):
    for step in (5, 10, 20, 25, 30, 40, 50, 100, 200, 250, 500):
        top = -(-v // step) * step
        if top / step <= 6:
            return top, step
    return v, v


def chart_svg(per_year, updated_label, compact=False):
    W, H = (360, 240) if compact else (760, 300)
    left, right, top, bottom = (30, 4, 24, 34) if compact else (44, 12, 28, 40)
    pw, ph = W - left - right, H - top - bottom
    vmax = max(p["citations"] for p in per_year)
    ymax, ystep = nice_ceiling(vmax)
    n = len(per_year)
    band = pw / n
    bar = min(16 if compact else 24, band * 0.5)
    r = 4
    parts = [
        f'<svg class="chart {"sm" if compact else "lg"}" viewBox="0 0 {W} {H}" role="group" '
        f'aria-labelledby="chart-title chart-desc" preserveAspectRatio="xMidYMid meet">',
        f'<defs><pattern id="hatch{"s" if compact else ""}" width="6" height="6" patternUnits="userSpaceOnUse" '
        'patternTransform="rotate(45)"><rect width="6" height="6" fill="#d9b4bf"/>'
        '<line x1="0" y1="0" x2="0" y2="6" stroke="#8b1f3f" stroke-width="2"/></pattern></defs>',
    ]
    # gridlines and y ticks
    t = 0
    while t <= ymax:
        y = top + ph - (t / ymax) * ph
        cls = "base" if t == 0 else "grid"
        parts.append(f'<line class="{cls}" x1="{left}" x2="{W - right}" y1="{y:.1f}" y2="{y:.1f}"/>')
        parts.append(f'<text class="tick" x="{left - 8}" y="{y + 4:.1f}" text-anchor="end">{t}</text>')
        t += ystep
    # bars
    label_years = {per_year[-1]["year"], max(per_year, key=lambda p: p["citations"])["year"]}
    for i, p in enumerate(per_year):
        v = p["citations"]
        cx = left + band * i + band / 2
        x = cx - bar / 2
        h = (v / ymax) * ph
        y0 = top + ph
        y = y0 - h
        rr = min(r, h)
        path = (f"M{x:.1f},{y0:.1f} V{y + rr:.1f} Q{x:.1f},{y:.1f} {x + rr:.1f},{y:.1f} "
                f"H{x + bar - rr:.1f} Q{x + bar:.1f},{y:.1f} {x + bar:.1f},{y + rr:.1f} V{y0:.1f} Z")
        partial = p.get("partial")
        fill = f"url(#hatch{'s' if compact else ''})" if partial else "#8b1f3f"
        tip = f'{p["year"]}{" to " + updated_label if partial else ""}: {v} citations'
        parts.append(
            f'<g class="col" tabindex="0" role="img" aria-label="{esc(tip)}" data-tip="{esc(tip)}">'
            f'<rect class="hit" x="{left + band * i:.1f}" y="{top}" width="{band:.1f}" height="{ph}"/>'
            f'<path d="{path}" fill="{fill}"/>'
        )
        if p["year"] in label_years:
            parts.append(f'<text class="val" x="{cx:.1f}" y="{y - 8:.1f}" text-anchor="middle">{v}</text>')
        yl = f"\u2019{str(p['year'])[2:]}" if compact else str(p["year"])
        xl = yl + "*" if partial else yl
        parts.append(f'<text class="tick" x="{cx:.1f}" y="{H - bottom + 20}" text-anchor="middle">{xl}</text></g>')
    parts.append("</svg>")
    return "\n".join(parts)


def build():
    d = json.load(open(DATA, encoding="utf-8"))
    tot = d["totals"]
    upd = long_date(d["updated"])
    upd_short = date.fromisoformat(d["updated"]).strftime("%-d %B")
    profile = f"https://scholar.google.com/citations?user={SCHOLAR_USER}&hl=en"
    per_year = d["per_year"]
    year_sum = sum(p["citations"] for p in per_year)
    first_year = per_year[0]["year"]
    full_years = [p for p in per_year if not p.get("partial")]
    last_full = full_years[-1]
    works = sorted(d["works"], key=lambda w: (-w["citations"], -w["year"]))
    top_cites = works[0]["citations"]
    c_all = tot["citations"]["all"]

    desc = (f"George Joseph, Ph.D. (Rajagiri Business School, Kochi): {c_all} Google Scholar citations, "
            f"h-index {tot['h_index']['all']}, i10-index {tot['i10_index']['all']}. "
            f"Citations by year and most-cited works, updated {upd}.")

    rows = []
    for i, w in enumerate(works, 1):
        scholar_link = (f"https://scholar.google.com/citations?view_op=view_citation&hl=en&user={SCHOLAR_USER}"
                        f"&citation_for_view={w['scholar']}")
        href = w["page"] or scholar_link
        badge = '<span class="chip">Summary</span>' if w["page"] else ""
        ext = "" if w["page"] else ' target="_blank" rel="noopener"'
        pct = w["citations"] / top_cites * 100
        rows.append(
            f'<tr><td class="rank">{i}</td>'
            f'<td class="work"><a href="{esc(href)}"{ext}>{esc(w["title"])}</a>{badge}'
            f'<span class="meta">{esc(w["authors"])} · <em>{esc(w["venue"])}</em></span></td>'
            f'<td class="yr">{w["year"]}</td>'
            f'<td class="num"><span class="n">{w["citations"]}</span>'
            f'<span class="bar" aria-hidden="true"><i style="width:{pct:.1f}%"></i></span></td></tr>'
        )

    year_rows = "".join(
        f'<tr><td>{p["year"]}{" (to " + upd_short + ")" if p.get("partial") else ""}</td>'
        f'<td class="num">{p["citations"]}</td></tr>' for p in per_year)

    jsonld = {
        "@context": "https://schema.org",
        "@type": "ProfilePage",
        "url": f"{SITE}/citations/",
        "dateModified": d["updated"],
        "mainEntity": {
            "@type": "Person",
            "name": "George Joseph",
            "honorificSuffix": "Ph.D.",
            "jobTitle": "Assistant Professor of Operations and Systems",
            "affiliation": {"@type": "CollegeOrUniversity", "name": "Rajagiri Business School",
                            "address": "Kochi, Kerala, India"},
            "url": SITE + "/",
            "identifier": "https://orcid.org/0000-0002-8569-8297",
            "sameAs": [profile.split("&")[0], "https://orcid.org/0000-0002-8569-8297",
                       "https://www.linkedin.com/in/george-joseph-33989211"],
        },
    }

    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Research citations | George Joseph, Ph.D.</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE}/citations/">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE}/citations/">
<meta property="og:title" content="Research citations | George Joseph, Ph.D.">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{SITE}/citations/og.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="627">
<meta property="og:image:alt" content="George Joseph, Ph.D.: {c_all} Google Scholar citations, h-index {tot['h_index']['all']}, i10-index {tot['i10_index']['all']}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=Outfit:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/papers/paper.css">
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
<style>
header.top,main,footer{{max-width:60rem}}
header.top nav{{display:flex;gap:1.2rem;flex-wrap:wrap;align-items:center}}
.lead{{color:var(--mid);font-size:1.02rem}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-top:2rem}}
.stat{{background:var(--paper);border:1px solid var(--warm);padding:1.3rem 1.2rem 1.1rem}}
.stat .v{{font-family:'Cormorant Garamond',serif;font-size:3.1rem;font-weight:700;line-height:1;color:var(--ink);font-variant-numeric:lining-nums;font-feature-settings:'lnum' 1}}
.stat .l{{font-size:.72rem;font-weight:500;letter-spacing:.08em;text-transform:uppercase;color:var(--mid);margin-top:.5rem}}
.stat .s{{font-family:'Cormorant Garamond',serif;font-style:italic;font-size:.98rem;color:var(--mid);margin-top:.15rem}}
.stat.lead-stat{{border-top:3px solid var(--wine)}}
.panel{{background:var(--white);border:1px solid var(--warm);padding:1.4rem 1.4rem 1rem;margin-top:1rem;position:relative}}
.chart{{width:100%;height:auto;display:block;overflow:visible}}
.chart.sm{{display:none}}
.chart .grid{{stroke:#e8e0d0;stroke-width:1}}
.chart .base{{stroke:#a09890;stroke-width:1}}
.chart .tick{{font:400 12px Outfit,sans-serif;fill:#6b6560}}
.chart .val{{font:600 13px Outfit,sans-serif;fill:#16191f}}
.chart .hit{{fill:transparent}}
.chart .col{{outline:none}}
.chart .col:hover .hit,.chart .col:focus .hit{{fill:rgba(139,31,63,.05)}}
.tip{{position:absolute;pointer-events:none;background:var(--ink);color:var(--white);font-size:.82rem;padding:.35rem .6rem;white-space:nowrap;opacity:0;transform:translate(-50%,-100%);transition:opacity .12s}}
.note{{font-size:.88rem;color:var(--mid);margin-top:.6rem}}
details{{margin-top:.6rem;font-size:.9rem}}
summary{{cursor:pointer;color:var(--wine)}}
table{{border-collapse:collapse;width:100%}}
table.small{{max-width:20rem;margin-top:.6rem}}
table.small td{{padding:.3rem .4rem;border-bottom:1px solid var(--warm)}}
table.works{{margin-top:1rem}}
table.works th{{font-size:.7rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--mid);text-align:left;padding:.5rem .5rem;border-bottom:1px solid var(--ink)}}
table.works td{{padding:.9rem .5rem;border-bottom:1px solid var(--warm);vertical-align:top}}
td.rank{{font-family:'Cormorant Garamond',serif;font-size:1.15rem;color:var(--mid);width:2rem;font-variant-numeric:lining-nums;font-feature-settings:'lnum' 1}}
td.work a{{color:var(--ink);text-decoration:none;font-weight:400;border-bottom:1px solid var(--gold)}}
td.work a:hover{{color:var(--wine);border-color:var(--wine)}}
td.work .meta{{display:block;font-size:.83rem;color:var(--mid);margin-top:.3rem}}
.chip{{display:inline-block;margin-left:.5rem;font-size:.66rem;font-weight:500;letter-spacing:.06em;text-transform:uppercase;padding:.08rem .4rem;border:1px solid var(--wine);color:var(--wine);vertical-align:2px}}
td.yr{{color:var(--mid);width:3.5rem}}
td.num,th.num{{text-align:right}}
td.num{{width:7.5rem;white-space:nowrap}}
td.num .n{{font-weight:500;font-variant-numeric:tabular-nums}}
td.num .bar{{display:block;height:6px;background:var(--paper);margin-top:.45rem;border-radius:3px;overflow:hidden}}
td.num .bar i{{display:block;height:100%;background:var(--wine);border-radius:3px 0 0 3px;margin-left:auto}}
.profiles{{display:flex;gap:.8rem;flex-wrap:wrap;margin-top:1rem}}
@media (max-width:600px){{.chart.lg{{display:none}}.chart.sm{{display:block}}.panel{{padding:1rem .6rem .6rem}}}}
@media (max-width:760px){{.stats{{grid-template-columns:repeat(2,1fr)}}td.yr{{display:none}}th.yr{{display:none}}td.num{{width:4.5rem}}}}
</style></head>
<body><header class="top"><a class="name" href="/">George Joseph, Ph.D.</a><nav><a href="/">Home</a><a href="/papers/">Paper summaries</a><a href="{esc(profile)}" target="_blank" rel="noopener">Google Scholar</a></nav></header>
<main>
<div class="theme">Research impact</div>
<h1>Research citations</h1>
<p class="lead">Citation record of George Joseph, Assistant Professor of Operations and Systems at Rajagiri Business School, Kochi. Figures are from his <a href="{esc(profile)}" target="_blank" rel="noopener">Google Scholar profile</a>, last updated on {upd}.</p>

<div class="stats">
<div class="stat lead-stat"><div class="v">{c_all}</div><div class="l">Citations</div><div class="s">{tot['citations']['since_2021']} since 2021</div></div>
<div class="stat"><div class="v">{tot['h_index']['all']}</div><div class="l">h-index</div><div class="s">{tot['h_index']['since_2021']} since 2021</div></div>
<div class="stat"><div class="v">{tot['i10_index']['all']}</div><div class="l">i10-index</div><div class="s">{tot['i10_index']['since_2021']} since 2021</div></div>
<div class="stat"><div class="v">{tot['works_indexed']}</div><div class="l">Works indexed</div><div class="s">Articles, chapters, cases</div></div>
</div>

<section>
<h2 id="chart-title">Citations per year</h2>
<p id="chart-desc" class="note" style="margin-top:0">{last_full['citations']} citations in {last_full['year']}, and {per_year[-1]['citations']} so far in {per_year[-1]['year']}.</p>
<div class="panel"><div class="tip" id="tip" role="status"></div>
{chart_svg(per_year, upd_short)}{chart_svg(per_year, upd_short, compact=True)}</div>
<p class="note">* {per_year[-1]['year']} runs to {upd_short}. Bars cover {first_year} onward and add up to {year_sum} of the {c_all} total; the rest are older citations.</p>
<details><summary>Show the numbers as a table</summary>
<table class="small"><tbody>{year_rows}</tbody></table></details>
</section>

<section>
<h2>Most-cited works</h2>
<p class="note" style="margin-top:0">Works marked <span class="chip" style="margin-left:0">Summary</span> have a plain-language summary on this site. Other titles open the Google Scholar record.</p>
<table class="works"><thead><tr><th>#</th><th>Work</th><th class="yr">Year</th><th class="num">Citations</th></tr></thead>
<tbody>
{chr(10).join(rows)}
</tbody></table>
<p class="note">{esc(d['uncited_note'])} The full list is on <a href="{esc(profile)}" target="_blank" rel="noopener">Google Scholar</a>.</p>
</section>

<section>
<h2>About these figures</h2>
<p>Google Scholar counts citations from journal articles, books, theses, conference papers and preprints, so its totals usually run higher than Scopus or Web of Science. The h-index of {tot['h_index']['all']} means {tot['h_index']['all']} works have each been cited at least {tot['h_index']['all']} times; the i10-index counts works with at least 10 citations.</p>
<div class="profiles"><a class="btn" href="{esc(profile)}" target="_blank" rel="noopener">Full Google Scholar profile</a><a class="btn alt" href="https://orcid.org/0000-0002-8569-8297" target="_blank" rel="noopener">ORCID</a><a class="btn alt" href="/papers/">Paper summaries</a></div>
</section>
</main>
<footer>Assistant Professor, Rajagiri Business School, Kochi, India · <a href="https://orcid.org/0000-0002-8569-8297">ORCID</a> · <a href="{esc(profile)}">Google Scholar</a> · <a href="https://www.linkedin.com/in/george-joseph-33989211">LinkedIn</a></footer>
<script>
(function(){{
  var tip=document.getElementById('tip'),panel=tip.parentNode;
  function show(g,e){{
    var pr=panel.getBoundingClientRect(),br=g.querySelector('path').getBoundingClientRect();
    tip.textContent=g.getAttribute('data-tip');
    tip.style.left=(br.left+br.width/2-pr.left)+'px';
    tip.style.top=(br.top-pr.top-8)+'px';
    tip.style.opacity=1;
  }}
  function hide(){{tip.style.opacity=0;}}
  document.querySelectorAll('.chart .col').forEach(function(g){{
    g.addEventListener('mouseenter',function(e){{show(g,e)}});
    g.addEventListener('focus',function(e){{show(g,e)}});
    g.addEventListener('mouseleave',hide);g.addEventListener('blur',hide);
  }});
}})();
</script>
</body></html>
"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
