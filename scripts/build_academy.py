#!/usr/bin/env python3
"""Build /academy/ (Phortex Learning Academy catalog) from academy/catalog.json.

    python3 scripts/build_academy.py            # check, then write academy/index.html + course pages
    python3 scripts/build_academy.py --check    # check only
    python3 scripts/build_academy.py --preview  # also build unrecorded lessons into _preview/ (git-ignored)

Course pages come from the private phortex-academy repo (../phortex-academy, or set PHORTEX_ACADEMY).
A course gets a page once its outline.md exists; a lesson gets a page once it has a script and a
YouTube video ID. Without the course source, only the catalog page is rebuilt.

To launch a course, set its "status" to "live" (its url defaults to /academy/<slug>/).
Statuses: "live", "production" (being made), "soon" (planned).
"""
import html
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import academy_course  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "academy" / "catalog.json"
PAGE = ROOT / "academy" / "index.html"
SITEMAP = ROOT / "sitemap.xml"
CONTENT = Path(os.environ.get("PHORTEX_ACADEMY", ROOT.parent / "phortex-academy"))
ASSET_V = academy_course.ASSET_V
FORM = "https://formspree.io/f/mreoodbz"
BANNED = re.compile(r"<|>|javascript:", re.I)
LEVELS = ("Beginner", "Intermediate", "Advanced")
STATUS = {"live": "Available now", "production": "In production", "soon": "Coming soon"}

# 48x48 line icons, drawn white on a colored tile
ICONS = {
    "ai": '<rect x="13" y="13" width="22" height="22" rx="4"/><path d="M19 8v5M29 8v5M19 35v5M29 35v5M8 19h5M8 29h5M35 19h5M35 29h5"/><path d="M20 28l4-9 4 9M21.5 25h5"/>',
    "chat": '<path d="M8 10h32v22H22l-9 7v-7H8z"/><path d="M15 18h18M15 24h12"/>',
    "agent": '<rect x="10" y="16" width="28" height="22" rx="6"/><path d="M24 8v8M18 25v2M30 25v2M19 32h10"/>',
    "code": '<path d="M16 14L6 24l10 10M32 14l10 10-10 10M27 10l-6 28"/>',
    "workflow": '<rect x="6" y="7" width="13" height="10" rx="2"/><rect x="29" y="7" width="13" height="10" rx="2"/><rect x="17.5" y="31" width="13" height="10" rx="2"/><path d="M19 12h10M12.5 17v7H24v7M35.5 17v7H24"/>',
    "policy": '<path d="M24 8v32M14 40h20M10 14h28"/><path d="M10 14l-5 12a5 5 0 0 0 10 0zM38 14l-5 12a5 5 0 0 0 10 0z"/>',
    "key": '<circle cx="15" cy="24" r="8"/><path d="M23 24h19M36 24v6M41 24v4"/>',
    "atom": '<circle cx="24" cy="24" r="2.5"/><ellipse cx="24" cy="24" rx="18" ry="7"/><ellipse cx="24" cy="24" rx="18" ry="7" transform="rotate(60 24 24)"/><ellipse cx="24" cy="24" rx="18" ry="7" transform="rotate(120 24 24)"/>',
    "lattice": '<path d="M9 9v.01M24 9v.01M39 9v.01M9 24v.01M24 24v.01M39 24v.01M9 39v.01M24 39v.01M39 39v.01" stroke-width="5"/><path d="M9 39L39 9M9 24l15-15"/>',
    "shield": '<path d="M24 6l14 5v11c0 9-6 16-14 20-8-4-14-11-14-20V11z"/><path d="M17 24l5 5 9-10"/>',
    "aishield": '<path d="M24 6l14 5v11c0 9-6 16-14 20-8-4-14-11-14-20V11z"/><path d="M19 29l5-12 5 12M20.8 25h6.4"/>',
    "inject": '<path d="M8 10h32v22H22l-9 7v-7H8z"/><path d="M26 13l-6 9h7l-6 9"/>',
    "mask": '<circle cx="24" cy="20" r="11"/><path d="M19 18v.01M29 18v.01M19 25c3 2 7 2 10 0" stroke-width="3"/><path d="M8 41c3-6 9-8 16-8s13 2 16 8"/>',
    "chain": '<path d="M20 28l8-8"/><path d="M22 15l3-3a7 7 0 0 1 10 10l-3 3M26 33l-3 3a7 7 0 0 1-10-10l3-3"/>',
    "vpn": '<path d="M24 6l14 5v11c0 9-6 16-14 20-8-4-14-11-14-20V11z"/><path d="M17 24h14M17 18h14M17 30h14M24 18v6M20 24v6M28 24v6"/>',
    "crypto": '<circle cx="24" cy="24" r="16"/><path d="M20 16v16M20 16h6a4 4 0 0 1 0 8h-6M20 24h7a4 4 0 0 1 0 8h-7M23 13v3M23 32v3"/>',
    "passkey": '<rect x="12" y="22" width="24" height="18" rx="3"/><path d="M17 22v-5a7 7 0 0 1 14 0"/><circle cx="24" cy="30" r="2.5"/><path d="M24 32.5V35"/>',
    "browser": '<rect x="6" y="9" width="36" height="30" rx="3"/><path d="M6 17h36M11 13h.01M15 13h.01"/><circle cx="22" cy="28" r="5"/><path d="M26 32l5 5"/>',
    "ransomware": '<rect x="12" y="21" width="24" height="19" rx="3"/><path d="M17 21v-5a7 7 0 0 1 14 0v5"/><path d="M24 28v5"/>',
    "fold": '<rect x="7" y="9" width="34" height="30" rx="4"/><path d="M24 9v30" stroke-dasharray="3 3"/><path d="M28 14h.01" stroke-width="4"/><path d="M15 33h4M29 33h4"/>',
    "blocks": '<rect x="5" y="18" width="12" height="12" rx="2"/><rect x="31" y="18" width="12" height="12" rx="2"/><rect x="18" y="5" width="12" height="12" rx="2"/><rect x="18" y="31" width="12" height="12" rx="2"/><path d="M17 24h14M24 17v14"/>',
    "printer": '<rect x="6" y="6" width="36" height="36" rx="3"/><path d="M6 14h36M20 14v5l4 4 4-4v-5M13 37h22M16 33h16M19 29h10"/>',
    "battery": '<rect x="5" y="14" width="34" height="20" rx="3"/><path d="M43 20v8M12 21v6M18 21v6M24 21v6"/>',
    "server": '<rect x="10" y="6" width="28" height="10" rx="2"/><rect x="10" y="19" width="28" height="10" rx="2"/><rect x="10" y="32" width="28" height="10" rx="2"/><path d="M15 11h.01M15 24h.01M15 37h.01M22 11h10M22 24h10M22 37h10"/>',
    "nuclear": '<circle cx="24" cy="24" r="4"/><path d="M24 20V6a18 18 0 0 0-15.6 9L20.5 22M27.5 22l12.1-7A18 18 0 0 0 24 6M20.5 26L8.4 33A18 18 0 0 0 24 42V28M27.5 26l12.1 7A18 18 0 0 1 24 42"/>',
}


class Invalid(Exception):
    pass


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower().replace("&", "and")).strip("-")


def e(s) -> str:
    return html.escape(str(s).strip(), quote=True)


def check(data: dict) -> dict:
    tracks = data.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        raise Invalid("need at least one track")
    ids = set()
    for t in tracks:
        for k in ("id", "group", "name", "color", "icon", "blurb"):
            if not isinstance(t.get(k), str) or not t[k].strip() or BANNED.search(t[k]):
                raise Invalid(f"track {t.get('id')}: bad '{k}'")
        if t["id"] in ids or not re.fullmatch(r"[a-z0-9-]+", t["id"]):
            raise Invalid(f"track id '{t['id']}' is invalid or repeated")
        ids.add(t["id"])
        if t["icon"] not in ICONS or not re.fullmatch(r"#[0-9A-Fa-f]{6}", t["color"]):
            raise Invalid(f"track {t['id']}: unknown icon or bad color")
        for c in t.get("courses", []):
            where = f"{t['id']}: {c.get('title')}"
            for k, lim in (("title", 80), ("desc", 240)):
                if not isinstance(c.get(k), str) or not c[k].strip() or len(c[k]) > lim or BANNED.search(c[k]):
                    raise Invalid(f"{where}: '{k}' missing, too long (limit {lim}) or has markup")
            if c.get("level") not in LEVELS or c.get("status") not in STATUS or c.get("icon") not in ICONS:
                raise Invalid(f"{where}: bad level, status or icon")
            if not all(isinstance(c.get(k), int) and c[k] > 0 for k in ("lessons", "minutes")):
                raise Invalid(f"{where}: lessons and minutes must be positive whole numbers")
            c["slug"] = c.get("slug") or slugify(c["title"])
            if not re.fullmatch(r"[a-z0-9-]+", c["slug"]):
                raise Invalid(f"{where}: bad slug '{c['slug']}'")
            c.setdefault("url", f"/academy/{c['slug']}/")
            if c["status"] == "live" and not re.match(r"^(https://|/)", c["url"]):
                raise Invalid(f"{where}: a live course needs a url")
            for tp in c.get("topics", []):
                if BANNED.search(tp) or len(tp) > 30:
                    raise Invalid(f"{where}: topic '{tp}' too long or has markup")
    slugs = [c["slug"] for t in tracks for c in t["courses"]]
    if len(slugs) != len(set(slugs)):
        raise Invalid("two courses share a slug")
    for t in tracks:
        for c in t["courses"]:
            for r in c.get("related", []):
                if r not in slugs:
                    raise Invalid(f"{c['title']}: related course '{r}' is not in the catalog")
    return data


def art(icon: str, color: str, size="") -> str:
    return (f'<div class="tl-art {size}" style="--c:{color}" aria-hidden="true">'
            f'<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.4" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICONS[icon]}</svg></div>')


def mins(n: int) -> str:
    return f"{n} min" if n < 60 else f"{n // 60} hr" + (f" {n % 60} min" if n % 60 else "")


def course(c: dict, color: str) -> str:
    st = c["status"]
    topics = "".join(f"<li>{e(x)}</li>" for x in c.get("topics", []))
    if st == "live":
        cta = f'<a class="ac-cta" href="{e(c["url"])}">Start the course &rarr;</a>'
    elif (ROOT / "academy" / c["slug"] / "index.html").exists():
        cta = f'<a class="ac-cta" href="/academy/{c["slug"]}/">See the course outline &rarr;</a>'
    else:
        cta = '<a class="ac-cta" href="#waitlist">Get notified &rarr;</a>'
    return f"""<article class="ac-course" style="--c:{color}">
          <div class="ac-course-top">{art(c['icon'], color)}<span class="ac-status ac-{st}">{STATUS[st]}</span></div>
          <h4 class="ac-title">{e(c['title'])}</h4>
          <div class="ac-facts"><span>{e(c['level'])}</span><span>{c['lessons']} lessons</span><span>{mins(c['minutes'])}</span></div>
          <p class="ac-desc">{e(c['desc'])}</p>
          <ul class="ac-topics">{topics}</ul>
          {cta}
        </article>"""


def render(data: dict) -> str:
    tracks = data["tracks"]
    total = sum(len(t["courses"]) for t in tracks)
    nprod = sum(1 for t in tracks for c in t["courses"] if c["status"] in ("production", "live"))
    jump = "".join(f'<a class="ac-jump" href="#{t["id"]}" style="--c:{t["color"]}">{e(t["name"])}</a>' for t in tracks)
    first = [(c, t["color"]) for t in tracks for c in t["courses"] if c["status"] in ("live", "production")]
    first_html = "\n".join(course(c, col) for c, col in first)
    sections, last_group = [], None
    for t in tracks:
        if t["group"] != last_group:
            sections.append(f'    <div class="ac-group"><span>{e(t["group"])}</span></div>')
            last_group = t["group"]
        body = "\n".join(course(c, t["color"]) for c in t["courses"])
        sections.append(f"""    <section class="ac-track" id="{t['id']}" aria-labelledby="h-{t['id']}">
      <header class="ac-track-head">
        {art(t['icon'], t['color'], 'tl-art-lg')}
        <div>
          <h3 class="heading-md" id="h-{t['id']}">{e(t['name'])}</h3>
          <p>{e(t['blurb'])}</p>
        </div>
        <span class="ac-count">{len(t['courses'])} courses</span>
      </header>
      <div class="ac-grid">
{body}
      </div>
    </section>""")
    boxes = "".join(f'<label class="ac-check"><input type="checkbox" name="tracks" value="{e(t["name"])}" /> {e(t["name"])}</label>' for t in tracks)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Learning Academy — Phortex</title>
  <meta name="description" content="Short, expert-led courses on AI, cybersecurity, post-quantum cryptography and the science behind emerging technology. From Phortex." />
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml" />
  <link rel="canonical" href="https://phortex.com/academy/" />
  <link rel="stylesheet" href="/css/style.css?v={ASSET_V}" />
  <!-- Generated by scripts/build_academy.py from academy/catalog.json. Edit the JSON, not this file. -->
</head>
<body class="grid-bg">
<script src="/js/components.js?v={ASSET_V}"></script>

<div class="page-hero">
  <div class="page-hero-bg"><div class="page-hero-glow" style="background:radial-gradient(ellipse, rgba(16,217,138,0.10) 0%, transparent 65%)"></div></div>
  <div class="container" style="position:relative;">
    <div class="eyebrow emerald">Phortex Learning Academy</div>
    <h1 class="heading-xl" style="max-width:860px; margin-bottom:1.25rem;">Learn AI, security and the science of <span class="text-accent-emerald">what&rsquo;s next</span></h1>
    <p class="lead" style="max-width:660px; margin-bottom:2rem;">Short, expert-led courses taught by a 25-year security architect. Bite-size lessons you can finish over a coffee, with a practical takeaway at the end of every one.</p>
    <div style="display:flex; gap:1rem; flex-wrap:wrap;">
      <a href="#waitlist" class="btn btn-emerald btn-lg btn-arrow">Get notified at launch</a>
      <a href="#catalog" class="btn btn-ghost btn-lg">Browse {total} courses</a>
    </div>
  </div>
</div>

<section class="compact">
  <div class="container">
    <div class="ac-format">
      <div><strong>Short video lessons</strong><span>5 to 12 minutes each</span></div>
      <div><strong>Hands-on exercises</strong><span>Try it on real tools</span></div>
      <div><strong>Quick knowledge checks</strong><span>Know what stuck</span></div>
      <div><strong>A checklist to keep</strong><span>Put it to work Monday</span></div>
      <div><strong>Certificate of completion</strong><span>Self-issued when you finish</span></div>
    </div>
    <p class="ac-note">Planned format. Lesson counts and times are estimates until each course is published.</p>
  </div>
</section>

<section style="background:var(--navy-1);">
  <div class="container">
    <div class="eyebrow emerald">First wave</div>
    <h2 class="heading-lg">Now in <span class="text-accent-emerald">production</span></h2>
    <p class="lead" style="max-width:640px;">We&rsquo;re building these {nprod} courses first, one from each track.</p>
    <div class="ac-grid ac-grid-first" style="margin-top:1.75rem;">
{first_html}
    </div>
  </div>
</section>

<section id="catalog">
  <div class="container">
    <div class="eyebrow emerald">Course catalog</div>
    <h2 class="heading-lg">Five tracks, <span class="text-accent-emerald">{total} courses</span></h2>
    <nav class="ac-jumps" aria-label="Jump to a track">{jump}</nav>
{chr(10).join(sections)}
  </div>
</section>

<section id="waitlist" style="background:var(--navy-1);">
  <div class="container ac-wait">
    <div>
      <div class="eyebrow emerald">Get notified</div>
      <h2 class="heading-lg">Be first in <span class="text-accent-emerald">class</span></h2>
      <p class="lead">Tell us what you want to learn. We&rsquo;ll email you when those courses open, and use your picks to decide what we record next.</p>
      <p class="ac-note">Training a team? <a href="/#contact">Ask about group access</a>.</p>
    </div>
    <form class="contact-form" id="academy-form" action="{FORM}" method="POST">
      <input type="hidden" name="_subject" value="Learning Academy waitlist" />
      <input type="hidden" name="service" value="Learning Academy waitlist" />
      <div class="form-group">
        <label class="form-label" for="ac-name">First name</label>
        <input class="form-input" type="text" id="ac-name" name="first_name" autocomplete="given-name" placeholder="Jane" />
      </div>
      <div class="form-group">
        <label class="form-label" for="ac-email">Email</label>
        <input class="form-input" type="email" id="ac-email" name="email" required autocomplete="email" placeholder="you@company.com" />
      </div>
      <fieldset class="form-group ac-checks">
        <legend class="form-label">I&rsquo;m interested in</legend>
        {boxes}
      </fieldset>
      <button type="submit" class="btn btn-emerald btn-lg" style="width:100%; justify-content:center;">Notify me</button>
      <p class="ac-msg" role="status" aria-live="polite"></p>
    </form>
  </div>
</section>

<script>
(function () {{
  var f = document.getElementById('academy-form');
  if (!f) return;
  f.addEventListener('submit', function (ev) {{
    ev.preventDefault();
    var msg = f.querySelector('.ac-msg'), btn = f.querySelector('button');
    if (!f.email.value || !f.email.checkValidity()) {{ msg.textContent = 'Please enter a valid email.'; return; }}
    btn.disabled = true; btn.textContent = 'Sending…';
    fetch(f.action, {{ method: 'POST', body: new FormData(f), headers: {{ Accept: 'application/json' }} }})
      .then(function (r) {{ if (!r.ok) throw new Error(); f.reset(); btn.textContent = 'You’re on the list'; msg.textContent = 'Thanks. We’ll email you when your courses open.'; }})
      .catch(function () {{ btn.disabled = false; btn.textContent = 'Notify me'; msg.textContent = 'That didn’t go through. Please try again, or email contact@phortex.com.'; }});
  }});
}})();
</script>
<script src="/js/main.js?v={ASSET_V}"></script>
</body>
</html>
"""


def main():
    try:
        data = check(json.loads(DATA.read_text(encoding="utf-8")))
    except (Invalid, ValueError, OSError) as err:
        sys.exit(f"Academy not updated: {err}")
    if "--check" in sys.argv:
        print("Academy catalog is valid.")
        return
    preview = "--preview" in sys.argv
    note = ""
    if (CONTENT / "courses").is_dir():
        try:
            if preview:
                out = ROOT / "_preview" / "academy"
                shutil.rmtree(ROOT / "_preview", ignore_errors=True)
                urls = academy_course.build(CONTENT, data, out, "/_preview", True)
                (out / "index.html").write_text(render(data), encoding="utf-8")
                note = f" Preview: {len(urls)} pages in _preview/academy/ (open /_preview/academy/<slug>/)."
            else:
                urls = academy_course.build(CONTENT, data, ROOT / "academy", "", False)
                update_sitemap(urls)
                note = f" Course pages: {len(urls)}."
        except (academy_course.CourseError, ValueError, OSError) as err:
            sys.exit(f"Academy not updated: {err}")
    else:
        note = f" (No course source at {CONTENT}; course pages left as they are.)"
    if not preview:
        PAGE.write_text(render(data), encoding="utf-8")
    print(f"Academy page built: {sum(len(t['courses']) for t in data['tracks'])} courses in {len(data['tracks'])} tracks.{note}")


def update_sitemap(urls):
    """Keep one <url> per generated academy page, after the /academy/ entry."""
    if not SITEMAP.exists():
        return
    text = SITEMAP.read_text(encoding="utf-8")
    text = re.sub(r"  <url><loc>https://phortex\.com/academy/[a-z0-9-]+/[^<]*</loc>[^\n]*\n", "", text)
    lines = "".join(f"  <url><loc>https://phortex.com{u}</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>\n"
                    for u in urls if not u.endswith(("/checklist/",)))
    anchor = re.search(r"  <url><loc>https://phortex\.com/academy/</loc>[^\n]*\n", text)
    if anchor and lines:
        text = text[:anchor.end()] + lines + text[anchor.end():]
    SITEMAP.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
