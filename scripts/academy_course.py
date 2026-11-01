"""Course, lesson, checklist and certificate pages for the Learning Academy.

Used by scripts/build_academy.py. Reads course source from the private phortex-academy repo
(see its README for the file formats) and writes static pages under academy/<slug>/.
Standard library only, like the rest of the site's scripts.
"""
import html
import json
import re
from pathlib import Path

ASSET_V = "20261031a"
SITE = "https://phortex.com"

INSTRUCTOR = {
    # Facts from /about/. Display name is a question for JT (outline.md, question 4).
    "name": "JT",
    "role": "Founder, Phortex",
    "bio": "25 years in IT and security, from systems engineering to enterprise security "
           "architecture in telecom and biopharma. CISSP since 2005, CCSP, and an MS in "
           "Technology Management from Penn and Wharton.",
}


class CourseError(Exception):
    pass


def e(s) -> str:
    return html.escape(str(s).strip(), quote=True)


# ---------------------------------------------------------------- tiny markdown

_SAFE_URL = re.compile(r"^(https://|/|#|mailto:)")


def inline(text: str) -> str:
    out = html.escape(text, quote=False)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", out)

    def link(m):
        label, url = m.group(1), html.unescape(m.group(2))
        if not _SAFE_URL.match(url):
            return label
        ext = ' target="_blank" rel="noopener"' if url.startswith("https://") else ""
        return f'<a href="{html.escape(url, quote=True)}"{ext}>{label}</a>'

    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, out)


def md(text: str) -> str:
    """Headings, paragraphs, lists, tick boxes, quotes, rules. Enough for scripts and checklists."""
    html_out, para, lst, quote = [], [], None, []

    def flush_quote():
        if quote:
            paras, cur = [], []
            for q in quote + [""]:
                if q:
                    cur.append(q)
                elif cur:
                    paras.append("<br />".join(inline(x) for x in cur)); cur = []
            html_out.append("<blockquote>" + "".join(f"<p>{x}</p>" for x in paras) + "</blockquote>")
            quote.clear()

    def flush_para():
        if para:
            html_out.append(f"<p>{inline(' '.join(para))}</p>")
            para.clear()

    def flush_list():
        nonlocal lst
        if lst:
            tag, items = lst
            html_out.append(f"<{tag}>" + "".join(items) + f"</{tag}>")
            lst = None

    for raw in text.splitlines():
        line = raw.rstrip()
        s = line.strip()
        if not s:
            flush_para(); flush_list(); flush_quote(); continue
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            flush_para(); flush_list()
            lvl = min(len(m.group(1)) + 1, 5)  # page owns h1
            html_out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            continue
        if re.fullmatch(r"-{3,}|\*{3,}", s):
            flush_para(); flush_list(); html_out.append("<hr />"); continue
        if s.startswith(">"):
            flush_para(); flush_list()
            quote.append(s[1:].strip())
            continue
        flush_quote()
        m = re.match(r"^[-*]\s+\[( |x|X)\]\s+(.*)$", s)
        if m:
            flush_para()
            if not lst or lst[0] != "ul class=\"lx-ticks\"":
                flush_list(); lst = ("ul class=\"lx-ticks\"", [])
            lst[1].append(f'<li><label><input type="checkbox" /> <span>{inline(m.group(2))}</span></label></li>')
            continue
        m = re.match(r"^([-*]|\d+\.)\s+(.*)$", s)
        if m:
            flush_para()
            tag = "ol" if m.group(1)[0].isdigit() else "ul"
            if not lst or lst[0] != tag:
                flush_list(); lst = (tag, [])
            lst[1].append(f"<li>{inline(m.group(2))}</li>")
            continue
        if lst and raw.startswith(("  ", "\t")):
            lst[1][-1] = lst[1][-1][:-5] + " " + inline(s) + "</li>"
            continue
        flush_list()
        para.append(s)
    flush_para(); flush_list(); flush_quote()
    return "\n".join(html_out).replace('<ul class="lx-ticks">', '<ul class="lx-ticks">').replace(
        '</ul class="lx-ticks">', "</ul>")


# ---------------------------------------------------------------- reading source

def front_matter(text: str):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            k, v = line.split(":", 1)
            meta[k.strip()] = re.sub(r"\s+#.*$", "", v).strip()
    return meta, m.group(2)


def sections(body: str) -> dict:
    out, name = {}, None
    for line in body.splitlines():
        m = re.match(r"^##\s+(.*)$", line)
        if m:
            name = m.group(1).strip().lower()
            out[name] = []
        elif name:
            out[name].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


LESSON_LINE = re.compile(r"^\s*(\d+)\.\s+\*\*(.+?)\*\*\s*(?:\((\d+)\s*min\))?\s*[—–-]+\s*(.+)$")
YT_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


def parse_quiz(text: str) -> dict:
    quiz, cur_lesson, q = {}, None, None
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^##\s+Lesson\s+(\d+)", s, re.I)
        if m:
            cur_lesson = int(m.group(1)); quiz[cur_lesson] = []; q = None; continue
        m = re.match(r"^###\s+(.*)$", s)
        if m and cur_lesson is not None:
            q = {"q": m.group(1).strip(), "options": [], "answer": None, "why": ""}
            quiz[cur_lesson].append(q); continue
        m = re.match(r"^[-*]\s+\[( |x|X)\]\s+(.*)$", s)
        if m and q is not None:
            if m.group(1).lower() == "x":
                q["answer"] = len(q["options"])
            q["options"].append(m.group(2).strip()); continue
        m = re.match(r"^Why:\s*(.*)$", s, re.I)
        if m and q is not None:
            q["why"] = m.group(1).strip()
    for n, qs in quiz.items():
        for item in qs:
            if item["answer"] is None or len(item["options"]) < 2:
                raise CourseError(f"quiz lesson {n}: '{item['q']}' needs 2+ options and one [x]")
    return quiz


def load_course(folder: Path, catalog_course: dict) -> dict:
    meta, body = front_matter((folder / "outline.md").read_text(encoding="utf-8"))
    sec = sections(body)
    slug = meta.get("slug") or folder.name
    if slug != folder.name:
        raise CourseError(f"{folder.name}: outline slug '{slug}' does not match the folder")
    plan = []
    for line in sec.get("lessons", "").splitlines():
        m = LESSON_LINE.match(line)
        if m:
            plan.append({"n": int(m.group(1)), "title": m.group(2).strip(),
                         "minutes": int(m.group(3) or 0), "goal": m.group(4).strip()})
    if not plan:
        raise CourseError(f"{slug}: outline has no lessons in the '1. **Title** (9 min) — goal' format")
    files = {}
    for p in sorted((folder / "lessons").glob("[0-9][0-9]-*.md")) if (folder / "lessons").is_dir() else []:
        lm, lbody = front_matter(p.read_text(encoding="utf-8"))
        n = int(p.name[:2])
        video = lm.get("video", "")
        if video and not YT_ID.match(video):
            raise CourseError(f"{p.name}: video must be an 11-character YouTube ID")
        lbody = re.sub(r"\[\[.*?\]\]", "", lbody, flags=re.S)  # JT's cues
        files[n] = {"title": lm.get("title"), "minutes": int(lm["minutes"]) if lm.get("minutes", "").isdigit() else None,
                    "video": video, "takeaway": lm.get("takeaway", ""), "body": md(lbody)}
    lessons = []
    for p in plan:
        f = files.get(p["n"], {})
        lessons.append({**p, "title": f.get("title") or p["title"], "minutes": f.get("minutes") or p["minutes"],
                        "video": f.get("video", ""), "takeaway": f.get("takeaway", ""),
                        "body": f.get("body", ""), "has_script": p["n"] in files})
    quiz = parse_quiz((folder / "quiz.md").read_text(encoding="utf-8")) if (folder / "quiz.md").exists() else {}
    checklist = md((folder / "checklist.md").read_text(encoding="utf-8")) if (folder / "checklist.md").exists() else ""
    objectives = [re.sub(r"^[-*]\s+", "", l).strip() for l in sec.get("what you'll learn", "").splitlines()
                  if l.strip().startswith(("-", "*"))]
    return {"slug": slug, "title": meta.get("title") or catalog_course["title"], "cat": catalog_course,
            "who": md(sec.get("who it's for", "")), "objectives": objectives, "lessons": lessons,
            "quiz": quiz, "checklist": checklist}


# ---------------------------------------------------------------- page shell

def shell(title, desc, path, body, base, noindex=False, extra_head=""):
    canon = f"{SITE}{path}"
    robots = '\n  <meta name="robots" content="noindex" />' if noindex else ""
    banner = ('<div class="lx-preview">Preview build. Not published.</div>' if base else "")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{e(title)} — Phortex Learning Academy</title>
  <meta name="description" content="{e(desc)}" />{robots}
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml" />
  <link rel="canonical" href="{canon}" />
  <meta property="og:title" content="{e(title)}" />
  <meta property="og:description" content="{e(desc)}" />
  <meta property="og:url" content="{canon}" />
  <link rel="stylesheet" href="/css/style.css?v={ASSET_V}" />{extra_head}
  <!-- Generated by scripts/build_academy.py from the phortex-academy course source. Do not edit by hand. -->
</head>
<body class="grid-bg">
<script src="/js/components.js?v={ASSET_V}"></script>
{banner}{body}
<script src="/js/academy.js?v={ASSET_V}"></script>
<script src="/js/main.js?v={ASSET_V}"></script>
</body>
</html>
"""


def mins(n: int) -> str:
    return f"{n} min" if n < 60 else f"{n // 60} hr" + (f" {n % 60} min" if n % 60 else "")


def crumbs(base, track, course=None, here=None):
    parts = [f'<a href="{base}/academy/">Academy</a>',
             f'<a href="{base}/academy/#{e(track["id"])}">{e(track["name"])}</a>']
    if course:
        parts.append(f'<a href="{base}/academy/{course["slug"]}/">{e(course["title"])}</a>')
    if here:
        parts.append(f'<span aria-current="page">{e(here)}</span>')
    return '<nav class="lx-crumbs" aria-label="Breadcrumb">' + '<span aria-hidden="true">/</span>'.join(parts) + "</nav>"


def instructor_card(base):
    i = INSTRUCTOR
    return f"""<div class="lx-card lx-instructor">
          <div class="lx-card-label">Your instructor</div>
          <div class="lx-inst-head"><div class="lx-avatar" aria-hidden="true">{e(i['name'][:2])}</div>
            <div><strong>{e(i['name'])}</strong><span>{e(i['role'])}</span></div></div>
          <p>{e(i['bio'])}</p>
          <a href="{base}/about/">More about JT &rarr;</a>
        </div>"""


# ---------------------------------------------------------------- course page

def course_page(c, track, base, published, related):
    cat, color = c["cat"], track["color"]
    total = sum(l["minutes"] for l in c["lessons"]) or cat["minutes"]
    any_pub = any(published.values())
    rows = []
    for l in c["lessons"]:
        n, url = l["n"], f'{base}/academy/{c["slug"]}/{l["n"]:02d}/'
        head = (f'<a href="{url}">{e(l["title"])}</a>' if published.get(n) else e(l["title"]))
        tag = "" if published.get(n) else '<span class="lx-soon">Coming soon</span>'
        rows.append(f"""<li class="lx-lesson" data-lesson="{n}">
            <span class="lx-num" aria-hidden="true">{n:02d}</span>
            <div><h3>{head}</h3><p>{e(l['goal'])}</p></div>
            <span class="lx-dur">{l['minutes']} min{tag}</span>
          </li>""")
    objectives = "".join(f"<li>{e(o)}</li>" for o in c["objectives"])
    includes = [f"{len(c['lessons'])} short video lessons", "A knowledge check after each lesson",
                "A one-page checklist to keep", "Certificate of completion (self-issued)"]
    inc = "".join(f"<li>{e(x)}</li>" for x in includes)
    if any_pub:
        first = next(n for n, ok in published.items() if ok)
        cta = (f'<a class="btn btn-emerald btn-lg btn-arrow" data-resume href="{base}/academy/{c["slug"]}/{first:02d}/">Start the course</a>')
    else:
        cta = f'<a class="btn btn-emerald btn-lg btn-arrow" href="{base}/academy/#waitlist">Get notified at launch</a>'
    status = "Available now" if cat["status"] == "live" else ("In production" if cat["status"] == "production" else "Coming soon")
    rel = "".join(f'<li><a href="{base}/academy/{r["slug"]}/">{e(r["title"])}</a></li>' if r.get("page")
                  else f'<li>{e(r["title"])}</li>' for r in related)
    rel_html = f'<div class="lx-card"><div class="lx-card-label">Related courses</div><ul class="lx-related">{rel}</ul></div>' if rel else ""
    checklist_link = (f'<a href="{base}/academy/{c["slug"]}/checklist/">Open the course checklist &rarr;</a>'
                      if c["checklist"] and any_pub else "")
    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "Course", "name": c["title"], "description": cat["desc"],
        "url": f"{SITE}/academy/{c['slug']}/", "educationalLevel": cat["level"], "inLanguage": "en",
        "isAccessibleForFree": True,
        "provider": {"@type": "Organization", "name": "Phortex", "sameAs": SITE},
        "teaches": c["objectives"],
    }).replace("</", "<\\/")
    body = f"""
<div class="page-hero lx-hero" style="--c:{color}">
  <div class="page-hero-bg"><div class="page-hero-glow" style="background:radial-gradient(ellipse, color-mix(in srgb, {color} 14%, transparent) 0%, transparent 65%)"></div></div>
  <div class="container" style="position:relative;">
    {crumbs(base, track)}
    <div class="lx-hero-grid">
      <div>
        <div class="lx-eyebrow">{e(track['name'])} &middot; {status}</div>
        <h1 class="heading-xl lx-h1">{e(c['title'])}</h1>
        <p class="lead lx-lead">{e(cat['desc'])}</p>
        <div class="lx-facts"><span>{e(cat['level'])}</span><span>{len(c['lessons'])} lessons</span><span>{mins(total)}</span><span>Free</span></div>
        <div class="lx-progress" data-course="{c['slug']}" data-total="{len(c['lessons'])}" hidden>
          <div class="lx-bar"><span></span></div><p></p>
        </div>
        <div class="lx-actions">{cta}</div>
      </div>
    </div>
  </div>
</div>

<section class="compact lx-body" style="--c:{color}">
  <div class="container lx-cols">
    <div class="lx-main">
      <h2 class="heading-md">What you&rsquo;ll learn</h2>
      <ul class="lx-objectives">{objectives}</ul>

      <h2 class="heading-md">Lessons</h2>
      <ol class="lx-lessons" data-course="{c['slug']}">
        {''.join(rows)}
      </ol>

      <h2 class="heading-md">Who it&rsquo;s for</h2>
      <div class="lx-prose">{c['who']}</div>
    </div>
    <aside class="lx-side">
      <div class="lx-card">
        <div class="lx-card-label">This course includes</div>
        <ul class="lx-includes">{inc}</ul>
        {checklist_link}
      </div>
      {instructor_card(base)}
      {rel_html}
    </aside>
  </div>
</section>
"""
    head = f'\n  <script type="application/ld+json">{jsonld}</script>'
    return shell(c["title"], cat["desc"], f"/academy/{c['slug']}/", body, base, noindex=bool(base), extra_head=head)


# ---------------------------------------------------------------- lesson page

def video_block(l, title):
    if l["video"]:
        vid = e(l["video"])
        return f"""<div class="lx-video" data-yt="{vid}" data-title="{e(title)}">
          <img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="" loading="lazy" />
          <button type="button" class="lx-play" aria-label="Play video: {e(title)}"><svg viewBox="0 0 68 48" aria-hidden="true"><path d="M66.5 7.7a8.5 8.5 0 0 0-6-6C55.2.3 34 .3 34 .3s-21.2 0-26.5 1.4a8.5 8.5 0 0 0-6 6C.1 13 .1 24 .1 24s0 11 1.4 16.3a8.5 8.5 0 0 0 6 6C12.8 47.7 34 47.7 34 47.7s21.2 0 26.5-1.4a8.5 8.5 0 0 0 6-6C67.9 35 67.9 24 67.9 24s0-11-1.4-16.3z" fill="currentColor"/><path d="M45 24L27 14v20" fill="#070D1A"/></svg></button>
          <noscript><a href="https://www.youtube.com/watch?v={vid}">Watch on YouTube</a></noscript>
        </div>"""
    return """<div class="lx-video lx-video-empty"><p><strong>Video coming soon.</strong><br />The full transcript is below.</p></div>"""


def quiz_block(qs, slug, n):
    if not qs:
        return ""
    items = []
    for qi, q in enumerate(qs):
        opts = "".join(
            f'<label class="lx-opt"><input type="radio" name="q{qi}" value="{oi}" /> <span>{inline(o)}</span></label>'
            for oi, o in enumerate(q["options"]))
        items.append(f"""<fieldset class="lx-q" data-answer="{q['answer']}">
            <legend><span class="lx-qn">{qi + 1}.</span> {inline(q['q'])}</legend>
            {opts}
            <p class="lx-why" hidden><strong></strong> {inline(q['why'])}</p>
          </fieldset>""")
    return f"""<section class="lx-quiz" aria-labelledby="quiz-h">
        <h2 class="heading-md" id="quiz-h">Knowledge check</h2>
        <p class="lx-muted">{len(qs)} quick questions. Nothing is recorded; this is just for you.</p>
        <form data-quiz="{slug}:{n}">
          {''.join(items)}
          <div class="lx-quiz-foot"><button type="submit" class="btn btn-emerald">Check my answers</button><p class="lx-score" role="status" aria-live="polite"></p></div>
        </form>
      </section>"""


CUR = ' aria-current="page"'


def lesson_page(c, track, l, base, published):
    slug, n, color = c["slug"], l["n"], track["color"]
    nums = [x["n"] for x in c["lessons"] if published.get(x["n"])]
    i = nums.index(n)
    prev_n = nums[i - 1] if i > 0 else None
    next_n = nums[i + 1] if i + 1 < len(nums) else None
    side = "".join(
        (f'<li data-lesson="{x["n"]}"{CUR if x["n"] == n else ""}>'
         + (f'<a href="{base}/academy/{slug}/{x["n"]:02d}/">' if published.get(x["n"]) else "<span>")
         + f'<span class="lx-num">{x["n"]:02d}</span><span class="lx-st">{e(x["title"])}</span><span class="lx-sm">{x["minutes"]} min</span>'
         + ("</a>" if published.get(x["n"]) else "</span>") + "</li>")
        for x in c["lessons"])
    prev_html = (f'<a class="btn btn-ghost" href="{base}/academy/{slug}/{prev_n:02d}/">&larr; Previous</a>' if prev_n else "<span></span>")
    nxt = (f'{base}/academy/{slug}/{next_n:02d}/' if next_n else f'{base}/academy/{slug}/' )
    next_label = "Next lesson" if next_n else "Back to the course"
    takeaway = (f'<div class="lx-takeaway"><div class="lx-card-label">Key takeaway</div><p>{e(l["takeaway"])}</p></div>'
                if l["takeaway"] else "")
    transcript = (f'<details class="lx-transcript" open><summary><h2 class="heading-md">Transcript</h2></summary>'
                  f'<div class="lx-prose">{l["body"]}</div></details>' if l["body"] else "")
    checklist = (f'<a class="lx-side-link" href="{base}/academy/{slug}/checklist/">Course checklist &rarr;</a>' if c["checklist"] else "")
    body = f"""
<section class="compact lx-lesson-page" style="--c:{color}">
  <div class="container">
    {crumbs(base, track, c, f"Lesson {n}")}
    <div class="lx-lcols">
      <div class="lx-main">
        {video_block(l, l['title'])}
        <div class="lx-lhead">
          <div class="lx-eyebrow">Lesson {n} of {len(c['lessons'])} &middot; {l['minutes']} min</div>
          <h1 class="heading-lg">{e(l['title'])}</h1>
          <p class="lx-muted">{e(l['goal'])}</p>
        </div>
        {takeaway}
        {transcript}
        {quiz_block(c['quiz'].get(n, []), slug, n)}
        <div class="lx-done-row">
          <button type="button" class="btn btn-ghost lx-done" data-course="{slug}" data-lesson="{n}" aria-pressed="false">Mark lesson complete</button>
        </div>
        <nav class="lx-pager" aria-label="Lesson navigation">{prev_html}<a class="btn btn-emerald btn-arrow" href="{nxt}" data-complete-on-click="{slug}:{n}">{next_label}</a></nav>
      </div>
      <aside class="lx-side">
        <div class="lx-card lx-toc">
          <div class="lx-card-label"><a href="{base}/academy/{slug}/">{e(c['title'])}</a></div>
          <div class="lx-progress" data-course="{slug}" data-total="{len(c['lessons'])}" hidden><div class="lx-bar"><span></span></div><p></p></div>
          <ol class="lx-toc-list" data-course="{slug}">{side}</ol>
          {checklist}
        </div>
      </aside>
    </div>
  </div>
</section>
"""
    desc = f"Lesson {n} of {c['title']}: {l['goal']}"
    return shell(f"{l['title']} | {c['title']}", desc, f"/academy/{slug}/{n:02d}/", body, base, noindex=bool(base))


# ---------------------------------------------------------------- checklist and certificate

def checklist_page(c, track, base):
    body = f"""
<section class="compact lx-print" style="--c:{track['color']}">
  <div class="container lx-narrow">
    {crumbs(base, track, c, "Checklist")}
    <div class="lx-eyebrow">Course checklist</div>
    <h1 class="heading-lg">{e(c['title'])}</h1>
    <p class="lx-muted lx-noprint">Tick items as you go, or print it and keep it at your desk. Ticks are not saved.</p>
    <div class="lx-prose lx-checklist">{c['checklist']}</div>
    <p class="lx-noprint"><button type="button" class="btn btn-emerald" data-print>Print or save as PDF</button></p>
    <p class="lx-print-foot">phortex.com/academy/{c['slug']}/</p>
  </div>
</section>
"""
    return shell(f"Checklist | {c['title']}", f"One-page checklist for {c['title']}.",
                 f"/academy/{c['slug']}/checklist/", body, base, noindex=bool(base))


def certificate_page(c, track, base):
    body = f"""
<section class="compact lx-print" style="--c:{track['color']}">
  <div class="container lx-narrow">
    {crumbs(base, track, c, "Certificate")}
    <div class="lx-cert-gate lx-noprint" data-cert="{c['slug']}" data-total="{len(c['lessons'])}">
      <h1 class="heading-lg">Certificate of completion</h1>
      <p class="lx-muted lx-cert-locked">Finish every lesson in this course on this device to unlock your certificate.</p>
      <form class="lx-cert-form" hidden>
        <label class="form-label" for="cert-name">Name to show on the certificate</label>
        <input class="form-input" id="cert-name" maxlength="60" required autocomplete="name" />
        <button type="submit" class="btn btn-emerald">Create certificate</button>
      </form>
    </div>
    <div class="lx-cert" hidden>
      <div class="lx-cert-brand">PHORTEX<span>.</span> Learning Academy</div>
      <p class="lx-cert-k">Certificate of completion</p>
      <p class="lx-cert-name"></p>
      <p>completed the course</p>
      <p class="lx-cert-course">{e(c['title'])}</p>
      <p class="lx-cert-meta">{len(c['lessons'])} lessons &middot; <span class="lx-cert-date"></span></p>
      <p class="lx-cert-note">Self-issued on completion of all lessons. Not an accredited qualification.</p>
      <p class="lx-noprint" style="margin-top:1.5rem"><button type="button" class="btn btn-emerald" data-print>Print or save as PDF</button></p>
    </div>
  </div>
</section>
"""
    return shell(f"Certificate | {c['title']}", f"Certificate of completion for {c['title']}.",
                 f"/academy/{c['slug']}/certificate/", body, base, noindex=True)


# ---------------------------------------------------------------- build

def build(content_root: Path, catalog: dict, out_root: Path, base: str, preview: bool) -> list:
    """Write pages for every catalog course with an outline. Returns the public URLs written."""
    by_slug = {c["slug"]: (c, t) for t in catalog["tracks"] for c in t["courses"]}
    courses_dir = content_root / "courses"
    loaded = {}
    for folder in sorted(p for p in courses_dir.iterdir() if p.is_dir()) if courses_dir.is_dir() else []:
        if not (folder / "outline.md").exists():
            continue
        if folder.name not in by_slug:
            raise CourseError(f"course folder '{folder.name}' has no matching slug in catalog.json")
        loaded[folder.name] = load_course(folder, by_slug[folder.name][0])
    urls = []
    for slug, c in loaded.items():
        track = by_slug[slug][1]
        published = {l["n"]: bool(l["has_script"] and (l["video"] or preview)) for l in c["lessons"]}
        related = []
        for r in (c["cat"].get("related") or []):
            if r in by_slug:
                related.append({"slug": r, "title": by_slug[r][0]["title"], "page": r in loaded})
        out = out_root / slug
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(course_page(c, track, base, published, related), encoding="utf-8")
        urls.append(f"/academy/{slug}/")
        for l in c["lessons"]:
            if published[l["n"]]:
                d = out / f"{l['n']:02d}"
                d.mkdir(exist_ok=True)
                (d / "index.html").write_text(lesson_page(c, track, l, base, published), encoding="utf-8")
                urls.append(f"/academy/{slug}/{l['n']:02d}/")
        if c["checklist"] and any(published.values()):
            (out / "checklist").mkdir(exist_ok=True)
            (out / "checklist" / "index.html").write_text(checklist_page(c, track, base), encoding="utf-8")
            urls.append(f"/academy/{slug}/checklist/")
        if all(published.values()):
            (out / "certificate").mkdir(exist_ok=True)
            (out / "certificate" / "index.html").write_text(certificate_page(c, track, base), encoding="utf-8")
    return urls
