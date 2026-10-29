#!/usr/bin/env python3
"""Rebuild the homepage's Security TL;DR block from a small JSON file.

    python3 scripts/update_tldr.py tldr/latest.json          # check, then write index.html
    python3 scripts/update_tldr.py tldr/latest.json --check  # check only

The daily task writes tldr/latest.json; this script is the only thing that touches the
HTML, and only between the TLDR:START and TLDR:END markers in index.html. It refuses
anything that doesn't pass the checks below, leaving the live page unchanged.

JSON shape:
{
  "date": "2026-10-29",
  "items": [
    {"title": "...", "why": "...", "action": "...",
     "source_name": "CISA", "source_url": "https://..."}
  ]
}
"""
import html
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "index.html"
START, END = "<!-- TLDR:START -->", "<!-- TLDR:END -->"
LIMITS = {"title": 90, "why": 240, "action": 170, "source_name": 40}
BANNED = re.compile(r"<|>|javascript:|\bclick here\b", re.I)


class Invalid(Exception):
    pass


def check(data: dict) -> dict:
    try:
        d = date.fromisoformat(str(data.get("date", "")))
    except ValueError:
        raise Invalid("date must be YYYY-MM-DD")
    if not (date.today() - timedelta(days=2) <= d <= date.today() + timedelta(days=1)):
        raise Invalid(f"date {d} is not current")
    items = data.get("items")
    if not isinstance(items, list) or not 1 <= len(items) <= 3:
        raise Invalid("need 1 to 3 items")
    seen = set()
    for i, it in enumerate(items, 1):
        for k, limit in LIMITS.items():
            v = it.get(k)
            if not isinstance(v, str) or not v.strip():
                raise Invalid(f"item {i}: '{k}' is missing")
            if len(v) > limit:
                raise Invalid(f"item {i}: '{k}' is {len(v)} characters (limit {limit})")
            if BANNED.search(v):
                raise Invalid(f"item {i}: '{k}' contains markup or a banned phrase")
        u = urlparse(it.get("source_url", ""))
        if u.scheme != "https" or not u.netloc or "phortex" in u.netloc:
            raise Invalid(f"item {i}: source_url must be an outside https link")
        if it["source_url"] in seen:
            raise Invalid(f"item {i}: duplicate source")
        seen.add(it["source_url"])
    return {"date": d, "items": items}


def render(data: dict) -> str:
    d = data["date"]
    label = f"{d:%B} {d.day}, {d.year}"
    cards = []
    for it in data["items"]:
        e = {k: html.escape(it[k].strip(), quote=True) for k in (*LIMITS, "source_url")}
        cards.append(f"""      <article class="threat-card" style="display:flex; flex-direction:column; gap:0.6rem;">
        <h3 class="threat-label" style="font-size:1rem; line-height:1.35;">{e['title']}</h3>
        <p class="text-muted" style="font-size:0.9rem; line-height:1.55; margin:0;">{e['why']}</p>
        <p style="font-size:0.9rem; line-height:1.55; margin:0;"><strong class="text-accent-cyan">Do this:</strong> {e['action']}</p>
        <a class="threat-source" href="{e['source_url']}" target="_blank" rel="noopener noreferrer" style="margin-top:auto;">Source: {e['source_name']} &rarr;</a>
      </article>""")
    return f"""{START}
<section class="compact" id="tldr" aria-labelledby="tldr-heading">
  <div class="container">
    <div class="eyebrow">Security TL;DR &middot; <time datetime="{d.isoformat()}">{label}</time></div>
    <h2 class="heading-md" id="tldr-heading">What small businesses should know <span class="text-accent-cyan">today</span></h2>
    <div class="threat-grid" style="grid-template-columns:repeat(auto-fit, minmax(260px, 1fr));">
{chr(10).join(cards)}
    </div>
    <p class="threat-source" style="margin-top:1rem;">Updated daily. Summaries link to the original source; not legal or incident-response advice. <a href="/ai-security/">More in the AI Security TL;DR &rarr;</a></p>
  </div>
</section>
{END}"""


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    try:
        data = check(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    except (Invalid, ValueError, OSError) as e:
        sys.exit(f"TLDR not updated: {e}")
    page = PAGE.read_text(encoding="utf-8")
    if page.count(START) != 1 or page.count(END) != 1:
        sys.exit("TLDR not updated: markers missing or duplicated in index.html")
    if "--check" in sys.argv:
        print("TLDR data is valid.")
        return
    before, rest = page.split(START)
    _, after = rest.split(END)
    PAGE.write_text(before + render(data) + after, encoding="utf-8")
    print(f"TLDR updated for {data['date']} with {len(data['items'])} items.")


if __name__ == "__main__":
    main()
