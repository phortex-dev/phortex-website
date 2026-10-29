# phortex-website
## Security TL;DR (updated daily)

The homepage's Security TL;DR section is rebuilt every morning by a scheduled task:

1. The task researches the last day or two of security news that matters to small businesses and writes up to three items to `tldr/latest.json`.
2. `python3 scripts/update_tldr.py tldr/latest.json` checks the data (current date, 1 to 3 items, length limits, no markup, outside https sources) and rewrites only the block between `<!-- TLDR:START -->` and `<!-- TLDR:END -->` in `index.html`. If a check fails, the page is left as it was.
3. The task commits both files and pushes to `main`, which deploys through Cloudflare.

To fix a published item by hand, edit `tldr/latest.json`, run the script, and push.

## AI Security TL;DR page (/ai-security/)

`ai-security/index.html` is generated; don't edit it by hand. A daily scheduled task researches AI-security news, conference talks and posts from the voices we track, then edits `intel/feed.json` (threat of the week, feed items, voices). `python3 scripts/build_intel.py` checks the data (https sources, length limits, no markup, no duplicates, a current `updated` date) and rebuilds the page; if a check fails, the live page stays as it was. Every summary is written by Phortex and links to its source; no articles or transcripts are copied.

## Changing shared CSS or JS

`_headers` tells browsers to cache `/css/*`, `/js/*` and `/assets/*` for a year without re-checking. After editing `js/components.js`, `js/main.js` or `css/style.css`, bump the `?v=` tag on its `<script>`/`<link>` in every page (and in `scripts/build_intel.py`), or returning visitors keep the old file.
