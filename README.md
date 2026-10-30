# phortex-website
## Security TL;DR (updated daily)

The homepage's Security TL;DR section and the full page at `/security-tldr/` are rebuilt every morning by a scheduled task:

1. The task researches the last day or two of security news, ranks the biggest stories (up to six) and writes them to `tldr/latest.json`. Each story has a `heat` score (1 to 5, 5 = top story of the day), a `cat` that picks its illustration (`vpn`, `phishing`, `ransomware`, `patch`, `breach`, `crypto`, `browser`, `malware`, `cloud`, `ai`, `policy`), a plain summary, one "Do this" action for small businesses, and an outside https source.
2. `python3 scripts/update_tldr.py tldr/latest.json` checks the data, replaces that day's stories in `tldr/feed.json` (so a rerun doesn't duplicate), keeps the last 60 days, and regenerates the homepage block between `<!-- TLDR:START -->` and `<!-- TLDR:END -->` (today's top 3) plus `security-tldr/index.html` (hottest this week, then every day, newest first). If a check fails, nothing is written.
3. The task commits `index.html`, `security-tldr/index.html`, `tldr/latest.json` and `tldr/feed.json` and pushes to `main`, which deploys through Cloudflare.

To fix a published story by hand, edit it in `tldr/feed.json` and run `python3 scripts/update_tldr.py --rebuild`.

## AI Security TL;DR page (/ai-security/)

`ai-security/index.html` is generated; don't edit it by hand. A daily scheduled task researches AI-security news, conference talks and posts from the voices we track, then edits `intel/feed.json` (threat of the week, feed items, voices). `python3 scripts/build_intel.py` checks the data (https sources, length limits, no markup, no duplicates, a current `updated` date) and rebuilds the page; if a check fails, the live page stays as it was. Every summary is written by Phortex and links to its source; no articles or transcripts are copied.

## Changing shared CSS or JS

`_headers` tells browsers to cache `/css/*`, `/js/*` and `/assets/*` for a year without re-checking. After editing `js/components.js`, `js/main.js` or `css/style.css`, bump the `?v=` tag on its `<script>`/`<link>` in every page (and in `scripts/build_intel.py`), or returning visitors keep the old file.
