#!/usr/bin/env python3
"""Security TL;DR: merge today's stories into the running feed and rebuild the pages.

    python3 scripts/update_tldr.py tldr/latest.json          # check, merge, write pages
    python3 scripts/update_tldr.py tldr/latest.json --check  # check only
    python3 scripts/update_tldr.py --rebuild                  # rebuild pages from tldr/feed.json

The daily task writes tldr/latest.json (today's stories only). This script checks it,
replaces that day's entries in tldr/feed.json (so a rerun the same day doesn't duplicate),
keeps the last KEEP_DAYS days, and regenerates:
  * the homepage block between TLDR:START and TLDR:END in index.html (today's top 3)
  * security-tldr/index.html (the full ranked archive, newest day first)
If any check fails, nothing is written and the live pages stay as they were.

latest.json:
{
  "date": "2026-10-30",
  "items": [
    {"title": "...", "why": "...", "action": "...",
     "heat": 1-5,            # how big the story is today; 5 = everyone is talking about it
     "cat": "vpn",           # one of CATS below; picks the illustration
     "source_name": "BleepingComputer", "source_url": "https://..."}
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
FEED = ROOT / "tldr" / "feed.json"
ARCHIVE = ROOT / "security-tldr" / "index.html"
START, END = "<!-- TLDR:START -->", "<!-- TLDR:END -->"
LIMITS = {"title": 90, "why": 260, "action": 180, "source_name": 40}
MAX_PER_DAY = 6
KEEP_DAYS = 60
ASSET_V = "20261030"
BANNED = re.compile(r"<|>|javascript:|\bclick here\b", re.I)

# key: (label, accent color, svg path data drawn on a 48x48 grid, white strokes)
CATS = {
    "vpn":        ("Firewall & VPN", "#00D4F0",
                   '<path d="M24 6l14 5v11c0 9-6 16-14 20-8-4-14-11-14-20V11z"/><path d="M17 24h14M17 18h14M17 30h14M24 18v6M20 24v6M28 24v6"/>'),
    "phishing":   ("Phishing", "#F5A524",
                   '<rect x="7" y="12" width="34" height="24" rx="3"/><path d="M7 15l17 12 17-12"/><path d="M33 30v6a4 4 0 0 1-8 0"/>'),
    "ransomware": ("Ransomware", "#FF5C7A",
                   '<rect x="12" y="21" width="24" height="19" rx="3"/><path d="M17 21v-5a7 7 0 0 1 14 0v5"/><path d="M24 28v5"/>'),
    "patch":      ("Patch now", "#10D98A",
                   '<path d="M14 34L34 14"/><rect x="9" y="19" width="30" height="10" rx="5" transform="rotate(-45 24 24)"/><path d="M21 24h.01M24 21h.01M27 24h.01M24 27h.01"/>'),
    "breach":     ("Data breach", "#8B5CF6",
                   '<ellipse cx="24" cy="12" rx="13" ry="5"/><path d="M11 12v12c0 3 6 5 13 5s13-2 13-5V12"/><path d="M11 24v10c0 3 6 5 13 5"/><path d="M33 31l6 6M39 31l-6 6"/>'),
    "crypto":     ("Crypto theft", "#F7C948",
                   '<circle cx="24" cy="24" r="16"/><path d="M20 16v16M20 16h6a4 4 0 0 1 0 8h-6M20 24h7a4 4 0 0 1 0 8h-7M23 13v3M23 32v3"/>'),
    "browser":    ("Browser & apps", "#4FA3FF",
                   '<rect x="6" y="9" width="36" height="30" rx="3"/><path d="M6 17h36M11 13h.01M15 13h.01"/><circle cx="22" cy="28" r="5"/><path d="M26 32l5 5"/>'),
    "malware":    ("Malware", "#FF8A3D",
                   '<ellipse cx="24" cy="27" rx="8" ry="11"/><path d="M24 16v22M18 12l3 4M30 12l-3 4M8 22h8M32 22h8M8 32h8M32 32h8"/>'),
    "cloud":      ("Cloud & accounts", "#38E1C6",
                   '<path d="M14 34a8 8 0 0 1 0-16 11 11 0 0 1 21-2 8 8 0 0 1-1 18z"/><circle cx="24" cy="25" r="3"/><path d="M24 28v4"/>'),
    "ai":         ("AI", "#C084FC",
                   '<rect x="13" y="13" width="22" height="22" rx="4"/><path d="M19 8v5M29 8v5M19 35v5M29 35v5M8 19h5M8 29h5M35 19h5M35 29h5"/><path d="M20 28l4-9 4 9M21.5 25h5"/>'),
    "policy":     ("Policy & law", "#9AA8C7",
                   '<path d="M24 8v32M14 40h20M10 14h28"/><path d="M10 14l-5 12a5 5 0 0 0 10 0zM38 14l-5 12a5 5 0 0 0 10 0z"/>'),
}


class Invalid(Exception):
    pass


def e(s) -> str:
    return html.escape(str(s).strip(), quote=True)


def fmt(d: date, long=False) -> str:
    return f"{d:%A}, {d:%B} {d.day}" if long else f"{d:%B} {d.day}, {d.year}"


def check_item(it: dict, where: str) -> dict:
    for k, limit in LIMITS.items():
        v = it.get(k)
        if not isinstance(v, str) or not v.strip():
            raise Invalid(f"{where}: '{k}' is missing")
        if len(v) > limit:
            raise Invalid(f"{where}: '{k}' is {len(v)} characters (limit {limit})")
        if BANNED.search(v):
            raise Invalid(f"{where}: '{k}' contains markup or a banned phrase")
    u = urlparse(it.get("source_url", ""))
    if u.scheme != "https" or not u.netloc or "phortex" in u.netloc:
        raise Invalid(f"{where}: source_url must be an outside https link")
    heat = it.get("heat", 3)
    if not isinstance(heat, int) or not 1 <= heat <= 5:
        raise Invalid(f"{where}: 'heat' must be a whole number from 1 to 5")
    cat = it.get("cat", "patch")
    if cat not in CATS:
        raise Invalid(f"{where}: 'cat' must be one of {', '.join(CATS)}")
    return {**{k: it[k].strip() for k in LIMITS}, "source_url": it["source_url"].strip(),
            "heat": heat, "cat": cat}


def check_latest(data: dict) -> tuple:
    try:
        d = date.fromisoformat(str(data.get("date", "")))
    except ValueError:
        raise Invalid("date must be YYYY-MM-DD")
    if not (date.today() - timedelta(days=2) <= d <= date.today() + timedelta(days=1)):
        raise Invalid(f"date {d} is not current")
    items = data.get("items")
    if not isinstance(items, list) or not 1 <= len(items) <= MAX_PER_DAY:
        raise Invalid(f"need 1 to {MAX_PER_DAY} items")
    out, seen = [], set()
    for i, it in enumerate(items, 1):
        c = check_item(it, f"item {i}")
        if c["source_url"] in seen:
            raise Invalid(f"item {i}: duplicate source")
        seen.add(c["source_url"])
        out.append({"date": d.isoformat(), **c})
    return d, out


def load_feed() -> list:
    if not FEED.exists():
        return []
    items = json.loads(FEED.read_text(encoding="utf-8")).get("items", [])
    for i, it in enumerate(items, 1):
        date.fromisoformat(it["date"])
        check_item(it, f"feed item {i}")
    return items


def merge(feed: list, day: date, today_items: list) -> list:
    today_urls = {x["source_url"] for x in today_items}
    keep = [x for x in feed if x["date"] != day.isoformat() and x["source_url"] not in today_urls]
    cutoff = (day - timedelta(days=KEEP_DAYS)).isoformat()
    merged = [x for x in keep + today_items if x["date"] >= cutoff]
    return sorted(merged, key=lambda x: (x["date"], x["heat"]), reverse=True)


# ── rendering ────────────────────────────────────────────────────────────

def art(cat: str, size="md") -> str:
    """Small illustration tile for a category: gradient square, glow, line icon."""
    label, color, paths = CATS[cat]
    return (f'<div class="tl-art tl-art-{size}" style="--c:{color}" aria-hidden="true">'
            f'<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.4" '
            f'stroke-linecap="round" stroke-linejoin="round">{paths}</svg></div>')


def heat(n: int) -> str:
    dots = "".join(f'<i class="{"on" if k < n else ""}"></i>' for k in range(5))
    word = {5: "Top story", 4: "Hot", 3: "Notable", 2: "Worth knowing", 1: "FYI"}[n]
    return f'<span class="tl-heat" title="Heat {n} of 5"><span class="tl-dots">{dots}</span>{word}</span>'


def chip(cat: str) -> str:
    label, color, _ = CATS[cat]
    return f'<span class="tl-cat" style="--c:{color}">{e(label)}</span>'


def card(it: dict, cls="tl-card", show_date=False, rank=None) -> str:
    d = date.fromisoformat(it["date"])
    when = f' &middot; <time datetime="{d.isoformat()}">{d:%b} {d.day}</time>' if show_date else ""
    r = f'<span class="tl-rank">#{rank}</span>' if rank else ""
    return f"""<article class="{cls}" data-cat="{it['cat']}">
  {art(it['cat'])}
  <div class="tl-body">
    <div class="tl-meta">{r}{chip(it['cat'])}{heat(it['heat'])}</div>
    <h3 class="tl-title">{e(it['title'])}</h3>
    <p class="tl-why">{e(it['why'])}</p>
    <p class="tl-do"><strong>Do this:</strong> {e(it['action'])}</p>
    <a class="tl-src" href="{e(it['source_url'])}" target="_blank" rel="noopener noreferrer">{e(it['source_name'])}{when} &rarr;</a>
  </div>
</article>"""


def render_home(feed: list) -> str:
    latest = feed[0]["date"]
    d = date.fromisoformat(latest)
    top = [x for x in feed if x["date"] == latest][:3]
    more = sum(1 for x in feed if x["date"] == latest) - len(top)
    cards = "\n".join(card(x, "tl-card tl-feature", rank=i) for i, x in enumerate(top, 1))
    more_txt = f"See all {more + len(top)} of today&rsquo;s stories and past days" if more > 0 else "See past days&rsquo; stories"
    return f"""{START}
<section class="compact" id="tldr" aria-labelledby="tldr-heading">
  <div class="container">
    <div class="eyebrow">Security TL;DR &middot; <time datetime="{d.isoformat()}">{fmt(d)}</time></div>
    <h2 class="heading-md" id="tldr-heading">Today&rsquo;s top security stories, <span class="text-accent-cyan">ranked</span></h2>
    <div class="tl-grid">
{cards}
    </div>
    <div class="tl-foot">
      <a class="btn btn-ghost btn-arrow" href="/security-tldr/">{more_txt}</a>
      <p>Updated daily. Summaries link to the original source; not legal or incident-response advice. <a href="/ai-security/">AI Security TL;DR &rarr;</a></p>
    </div>
  </div>
</section>
{END}"""


def render_archive(feed: list) -> str:
    latest = date.fromisoformat(feed[0]["date"])
    week = [x for x in feed if date.fromisoformat(x["date"]) > latest - timedelta(days=7)]
    hottest = sorted(week, key=lambda x: (x["heat"], x["date"]), reverse=True)[:3]
    hot_html = "\n".join(card(x, "tl-card tl-feature", show_date=True, rank=i) for i, x in enumerate(hottest, 1))
    days, order = {}, []
    for x in feed:
        if x["date"] not in days:
            days[x["date"]] = []
            order.append(x["date"])
        days[x["date"]].append(x)
    blocks = []
    for ds in order:
        d = date.fromisoformat(ds)
        items = sorted(days[ds], key=lambda x: -x["heat"])
        body = "\n".join(card(x, rank=i) for i, x in enumerate(items, 1))
        blocks.append(f"""    <section class="tl-day" aria-labelledby="d-{ds}">
      <h2 class="tl-day-h" id="d-{ds}"><time datetime="{ds}">{fmt(d, long=True)}</time><span>{len(items)} {'story' if len(items) == 1 else 'stories'}</span></h2>
      <div class="tl-list">
{body}
      </div>
    </section>""")
    counts = {}
    for x in feed:
        counts[x["cat"]] = counts.get(x["cat"], 0) + 1
    chips = [f'<button type="button" class="tl-filter" aria-pressed="true" data-filter="all">All <span>{len(feed)}</span></button>']
    chips += [f'<button type="button" class="tl-filter" aria-pressed="false" data-filter="{k}">{e(CATS[k][0])} <span>{counts[k]}</span></button>'
              for k in CATS if counts.get(k)]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Security TL;DR — Phortex</title>
  <meta name="description" content="The day's biggest cybersecurity stories, ranked and explained in plain English, each with one thing a small or mid-size business should do. Updated daily by Phortex." />
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml" />
  <link rel="canonical" href="https://phortex.com/security-tldr/" />
  <link rel="stylesheet" href="/css/style.css?v={ASSET_V}" />
  <!-- Generated by scripts/update_tldr.py from tldr/feed.json. Edit the JSON, not this file. -->
</head>
<body class="grid-bg">
<script src="/js/components.js?v={ASSET_V}"></script>

<div class="page-hero">
  <div class="page-hero-bg"><div class="page-hero-glow"></div></div>
  <div class="container" style="position:relative;">
    <div class="eyebrow">Security TL;DR &middot; Updated {fmt(latest)}</div>
    <h1 class="heading-xl" style="max-width:820px; margin-bottom:1.25rem;">The security news that matters, <span class="text-accent-cyan">ranked daily</span></h1>
    <p class="lead" style="max-width:660px;">Every morning we rank the biggest cybersecurity stories, explain each in two sentences, and tell you the one thing a small or mid-size business should do about it. Every item links to its original source.</p>
  </div>
</div>

<section class="compact">
  <div class="container">
    <div class="eyebrow">Hottest this week</div>
    <div class="tl-grid tl-grid-feature">
{hot_html}
    </div>
  </div>
</section>

<section id="archive" style="background:var(--navy-1);">
  <div class="container">
    <div class="eyebrow">Daily briefings</div>
    <h2 class="heading-lg">Newest first</h2>
    <div class="tl-filters" role="group" aria-label="Filter by topic">
      {''.join(chips)}
    </div>
{chr(10).join(blocks)}
    <p class="tl-note">Stories are kept for {KEEP_DAYS} days. Summaries are written by Phortex and link to the original reporting; not legal or incident-response advice.</p>
  </div>
</section>

<div class="cta-band">
  <div class="cta-band-glow"></div>
  <div class="container" style="position:relative;">
    <h2 class="heading-lg" style="margin-bottom:1rem;">Not sure if a story affects <span class="text-accent-cyan">your business?</span></h2>
    <p class="lead" style="margin:0 auto; text-align:center;">Phortex helps small and mid-size teams turn security news into a short, practical plan.</p>
    <div class="cta-band-actions">
      <a href="/#contact" class="btn btn-primary btn-lg btn-arrow">Talk to Phortex</a>
      <a href="/security/" class="btn btn-ghost btn-lg">Security services</a>
    </div>
  </div>
</div>

<script>
document.querySelectorAll('.tl-filter').forEach(function (b) {{
  b.addEventListener('click', function () {{
    var f = b.getAttribute('data-filter');
    document.querySelectorAll('.tl-filter').forEach(function (c) {{ c.setAttribute('aria-pressed', c === b ? 'true' : 'false'); }});
    document.querySelectorAll('.tl-day').forEach(function (day) {{
      var shown = 0;
      day.querySelectorAll('.tl-card').forEach(function (it) {{
        it.hidden = f !== 'all' && it.getAttribute('data-cat') !== f;
        if (!it.hidden) shown++;
      }});
      day.hidden = shown === 0;
    }});
  }});
}});
</script>
<script src="/js/main.js?v={ASSET_V}"></script>
</body>
</html>
"""


def write_pages(feed: list):
    page = PAGE.read_text(encoding="utf-8")
    if page.count(START) != 1 or page.count(END) != 1:
        raise Invalid("markers missing or duplicated in index.html")
    before, rest = page.split(START)
    _, after = rest.split(END)
    PAGE.write_text(before + render_home(feed) + after, encoding="utf-8")
    ARCHIVE.parent.mkdir(exist_ok=True)
    ARCHIVE.write_text(render_archive(feed), encoding="utf-8")
    FEED.write_text(json.dumps({"updated": feed[0]["date"], "items": feed}, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    try:
        feed = load_feed()
        if "--rebuild" in sys.argv:
            if not feed:
                raise Invalid("tldr/feed.json is empty")
            write_pages(feed)
            print(f"Rebuilt pages from {len(feed)} stored stories.")
            return
        if not args:
            sys.exit(__doc__)
        day, items = check_latest(json.loads(Path(args[0]).read_text(encoding="utf-8")))
        merged = merge(feed, day, items)
        if "--check" in sys.argv:
            print(f"TLDR data is valid ({len(items)} stories for {day}; feed would hold {len(merged)}).")
            return
        write_pages(merged)
    except (Invalid, ValueError, KeyError, OSError) as err:
        sys.exit(f"TLDR not updated: {err}")
    print(f"TLDR updated for {day} with {len(items)} stories; feed holds {len(merged)}.")


if __name__ == "__main__":
    main()
