#!/usr/bin/env python3
"""Build /ai-security/ (the AI Security TL;DR page) from intel/feed.json.

    python3 scripts/build_intel.py            # check, then write ai-security/index.html
    python3 scripts/build_intel.py --check    # check only

The daily task edits intel/feed.json only; this script checks it and regenerates the page.
If a check fails, the live page is left as it was.

feed.json:
  updated            YYYY-MM-DD
  threat_of_the_week one item (below), shown at the top
  items              newest first or any order; sorted by date here; up to 60 kept
  voices             [{name, outlet, focus, url}]
Item: {cat: news|talk|voices, source, date: YYYY-MM-DD, title, tldr, smb, url, link_label}
"""
import html
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
FEED = ROOT / "intel" / "feed.json"
PAGE = ROOT / "ai-security" / "index.html"
CATS = {"news": "News", "talk": "Talks", "voices": "Voices"}
LIMITS = {"source": 60, "title": 110, "tldr": 320, "smb": 180, "link_label": 40}
MAX_ITEMS = 60
BANNED = re.compile(r"<|>|javascript:", re.I)


class Invalid(Exception):
    pass


def _url(u: str, where: str) -> str:
    p = urlparse(u or "")
    if p.scheme != "https" or not p.netloc:
        raise Invalid(f"{where}: url must be an https link")
    return u


def _text(obj: dict, key: str, limit: int, where: str) -> str:
    v = obj.get(key)
    if not isinstance(v, str) or not v.strip():
        raise Invalid(f"{where}: '{key}' is missing")
    if len(v) > limit:
        raise Invalid(f"{where}: '{key}' is {len(v)} characters (limit {limit})")
    if BANNED.search(v):
        raise Invalid(f"{where}: '{key}' contains markup")
    return v.strip()


def _date(v: str, where: str) -> date:
    try:
        d = date.fromisoformat(str(v))
    except ValueError:
        raise Invalid(f"{where}: date must be YYYY-MM-DD")
    if d > date.today() + timedelta(days=1):
        raise Invalid(f"{where}: date {d} is in the future")
    return d


def _item(it: dict, where: str, cat_required=True) -> dict:
    out = {k: _text(it, k, n, where) for k, n in LIMITS.items()}
    out["date"] = _date(it.get("date"), where)
    out["url"] = _url(it.get("url"), where)
    if cat_required:
        if it.get("cat") not in CATS:
            raise Invalid(f"{where}: cat must be one of {', '.join(CATS)}")
        out["cat"] = it["cat"]
    return out


def check(data: dict) -> dict:
    updated = _date(data.get("updated"), "updated")
    if updated < date.today() - timedelta(days=3):
        raise Invalid(f"updated date {updated} is stale")
    threat = _item(data.get("threat_of_the_week") or {}, "threat_of_the_week", cat_required=False)
    raw = data.get("items")
    if not isinstance(raw, list) or not 3 <= len(raw):
        raise Invalid("need at least 3 items")
    items, seen = [], set()
    for i, it in enumerate(raw, 1):
        x = _item(it, f"item {i}")
        if x["url"] in seen:
            raise Invalid(f"item {i}: duplicate url")
        seen.add(x["url"])
        items.append(x)
    items.sort(key=lambda x: x["date"], reverse=True)
    voices = []
    for i, v in enumerate(data.get("voices") or [], 1):
        voices.append({"name": _text(v, "name", 60, f"voice {i}"), "outlet": _text(v, "outlet", 60, f"voice {i}"),
                       "focus": _text(v, "focus", 140, f"voice {i}"), "url": _url(v.get("url"), f"voice {i}")})
    return {"updated": updated, "threat": threat, "items": items[:MAX_ITEMS], "voices": voices}


def e(s) -> str:
    return html.escape(str(s), quote=True)


def fmt(d: date) -> str:
    return f"{d:%b} {d.day}, {d.year}"


def card(x: dict) -> str:
    return f"""      <article class="card intel-item" data-cat="{x['cat']}">
        <div class="intel-meta"><span class="tag">{CATS[x['cat']]}</span><span>{e(x['source'])} &middot; <time datetime="{x['date'].isoformat()}">{fmt(x['date'])}</time></span></div>
        <h3 class="heading-sm intel-title">{e(x['title'])}</h3>
        <p class="intel-tldr">{e(x['tldr'])}</p>
        <div class="intel-smb"><span>SMB takeaway</span>{e(x['smb'])}</div>
        <a class="intel-link" href="{e(x['url'])}" target="_blank" rel="noopener noreferrer">{e(x['link_label'])} &rarr;</a>
      </article>"""


def render(d: dict) -> str:
    t = d["threat"]
    counts = {k: sum(1 for x in d["items"] if x["cat"] == k) for k in CATS}
    chips = [f'<button type="button" class="intel-chip" aria-pressed="true" data-filter="all">All <span>{len(d["items"])}</span></button>']
    chips += [f'<button type="button" class="intel-chip" aria-pressed="false" data-filter="{k}">{v} <span>{counts[k]}</span></button>'
              for k, v in CATS.items() if counts[k]]
    voices = "\n".join(f"""      <a class="card intel-voice" href="{e(v['url'])}" target="_blank" rel="noopener noreferrer">
        <div class="intel-voice-name">{e(v['name'])}</div>
        <div class="intel-voice-outlet">{e(v['outlet'])}</div>
        <p>{e(v['focus'])}</p>
      </a>""" for v in d["voices"])
    upd = fmt(d["updated"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AI Security TL;DR — Phortex</title>
  <meta name="description" content="The AI security news, talks and expert voices that matter, summarized in plain English with one takeaway for small and mid-size businesses. Updated daily by Phortex." />
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml" />
  <link rel="canonical" href="https://phortex.com/ai-security/" />
  <link rel="stylesheet" href="/css/style.css" />
  <!-- Generated by scripts/build_intel.py from intel/feed.json. Edit the JSON, not this file. -->
  <style>
    .intel-threat {{ border-left: 3px solid var(--cyan); }}
    .intel-meta {{ display:flex; flex-wrap:wrap; align-items:center; gap:.6rem; font-family:var(--font-mono); font-size:.7rem; color:var(--gray-300); }}
    .intel-title {{ margin:.75rem 0 .5rem; }}
    .intel-tldr {{ color:var(--gray-100); font-size:.95rem; line-height:1.6; margin:0 0 1rem; }}
    .intel-smb {{ font-size:.92rem; line-height:1.55; padding:.8rem 1rem; border-radius:var(--r); background:var(--cyan-subtle); margin-bottom:1rem; }}
    .intel-smb span {{ display:block; font-family:var(--font-mono); font-size:.65rem; letter-spacing:.1em; text-transform:uppercase; color:var(--cyan); margin-bottom:.3rem; }}
    .intel-link {{ font-family:var(--font-mono); font-size:.75rem; }}
    .intel-grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(320px, 1fr)); gap:1.25rem; margin-top:1.5rem; }}
    .intel-item {{ display:flex; flex-direction:column; }}
    .intel-item .intel-link {{ margin-top:auto; }}
    .intel-item[hidden] {{ display:none; }}
    .intel-chips {{ display:flex; flex-wrap:wrap; gap:.5rem; margin-top:1.5rem; }}
    .intel-chip {{ font:500 .85rem var(--font-body); color:var(--gray-100); background:transparent; border:1px solid var(--gray-700); border-radius:999px; padding:.55rem 1rem; min-height:44px; cursor:pointer; }}
    .intel-chip span {{ font-family:var(--font-mono); font-size:.7rem; opacity:.7; margin-left:.25rem; }}
    .intel-chip[aria-pressed="true"] {{ color:var(--navy-1); background:var(--cyan); border-color:var(--cyan); }}
    .intel-voices {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(240px, 1fr)); gap:1.25rem; margin-top:1.5rem; }}
    .intel-voice {{ color:inherit; text-decoration:none; }}
    .intel-voice-name {{ font-weight:700; font-size:1.05rem; }}
    .intel-voice-outlet {{ font-family:var(--font-mono); font-size:.7rem; color:var(--cyan); margin:.25rem 0 .75rem; }}
    .intel-voice p {{ margin:0; font-size:.9rem; line-height:1.55; color:var(--gray-100); }}
    @media (max-width: 420px) {{ .intel-grid {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body class="grid-bg">
<script src="/js/components.js?v=20261029"></script>

<div class="page-hero">
  <div class="page-hero-bg"><div class="page-hero-glow"></div></div>
  <div class="container" style="position:relative;">
    <div class="eyebrow">AI Security TL;DR &middot; Updated {upd}</div>
    <h1 class="heading-xl" style="max-width:820px; margin-bottom:1.25rem;">AI security, <span class="text-accent-cyan">decoded</span></h1>
    <p class="lead" style="max-width:640px;">The AI security news, conference talks and expert voices that matter, each summarized in plain English with one takeaway for small and mid-size businesses. Every item links to its original source.</p>
  </div>
</div>

<section class="compact">
  <div class="container">
    <div class="eyebrow">Threat of the week</div>
    <article class="card intel-threat" style="margin-top:1.25rem; max-width:860px;">
      <div class="intel-meta"><span>{e(t['source'])} &middot; <time datetime="{t['date'].isoformat()}">{fmt(t['date'])}</time></span></div>
      <h2 class="heading-md intel-title">{e(t['title'])}</h2>
      <p class="intel-tldr">{e(t['tldr'])}</p>
      <div class="intel-smb"><span>SMB takeaway</span>{e(t['smb'])}</div>
      <a class="intel-link" href="{e(t['url'])}" target="_blank" rel="noopener noreferrer">{e(t['link_label'])} &rarr;</a>
    </article>
  </div>
</section>

<section id="feed" style="background:var(--navy-1);">
  <div class="container">
    <div class="eyebrow">The feed</div>
    <h2 class="heading-lg">Latest in <span class="text-accent-cyan">AI security</span></h2>
    <div class="intel-chips" role="group" aria-label="Filter the feed">
      {"".join(chips)}
    </div>
    <div class="intel-grid">
{chr(10).join(card(x) for x in d['items'])}
    </div>
    <p class="threat-source" style="margin-top:1.5rem;">Summaries are written by Phortex and link to the original source. Not legal or incident-response advice.</p>
  </div>
</section>

<section id="voices">
  <div class="container">
    <div class="eyebrow">Voices we track</div>
    <h2 class="heading-lg">The people worth <span class="text-accent-cyan">reading first</span></h2>
    <div class="intel-voices">
{voices}
    </div>
  </div>
</section>

<div class="cta-band">
  <div class="cta-band-glow"></div>
  <div class="container" style="position:relative;">
    <h2 class="heading-lg" style="margin-bottom:1rem;">Did this raise a question about <span class="text-accent-cyan">your business?</span></h2>
    <p class="lead" style="margin:0 auto; text-align:center;">Phortex helps small and mid-size teams turn AI security news into a plan.</p>
    <div class="cta-band-actions">
      <a href="/#contact" class="btn btn-primary btn-lg btn-arrow">Talk to Phortex</a>
      <a href="/security/" class="btn btn-ghost btn-lg">Security services</a>
    </div>
  </div>
</div>

<script>
document.querySelectorAll('.intel-chip').forEach(function (chip) {{
  chip.addEventListener('click', function () {{
    var f = chip.getAttribute('data-filter');
    document.querySelectorAll('.intel-chip').forEach(function (c) {{ c.setAttribute('aria-pressed', c === chip ? 'true' : 'false'); }});
    document.querySelectorAll('.intel-item').forEach(function (it) {{ it.hidden = f !== 'all' && it.getAttribute('data-cat') !== f; }});
  }});
}});
</script>
<script src="/js/main.js?v=20261029"></script>
</body>
</html>
"""


def main():
    try:
        data = check(json.loads(FEED.read_text(encoding="utf-8")))
    except (Invalid, ValueError, OSError) as err:
        sys.exit(f"AI Security page not updated: {err}")
    if "--check" in sys.argv:
        print(f"Feed is valid: {len(data['items'])} items, {len(data['voices'])} voices.")
        return
    PAGE.parent.mkdir(exist_ok=True)
    PAGE.write_text(render(data), encoding="utf-8")
    print(f"Built ai-security/index.html: {len(data['items'])} items, updated {data['updated']}.")


if __name__ == "__main__":
    main()
