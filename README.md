# phortex-website
## Security TL;DR (updated daily)

The homepage's Security TL;DR section is rebuilt every morning by a scheduled task:

1. The task researches the last day or two of security news that matters to small businesses and writes up to three items to `tldr/latest.json`.
2. `python3 scripts/update_tldr.py tldr/latest.json` checks the data (current date, 1 to 3 items, length limits, no markup, outside https sources) and rewrites only the block between `<!-- TLDR:START -->` and `<!-- TLDR:END -->` in `index.html`. If a check fails, the page is left as it was.
3. The task commits both files and pushes to `main`, which deploys through Cloudflare.

To fix a published item by hand, edit `tldr/latest.json`, run the script, and push.
