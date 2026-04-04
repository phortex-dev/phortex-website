# Phortex Website — Deployment Guide

## Repository
`https://github.com/phortex-dev/phortex-website`

## File Structure
```
phortex-website/
├── index.html              ← Homepage
├── security/index.html     ← Phortex Secure
├── ai/index.html           ← Phortex AI  
├── campus/index.html       ← Phortex Campus
├── about/index.html        ← About / Founder
├── css/style.css           ← Shared design system
├── js/main.js              ← Shared interactions
├── js/components.js        ← Shared nav + footer
├── assets/favicon.svg      ← Site icon
├── _headers                ← Cloudflare security headers
├── _redirects              ← Cloudflare URL rules
├── robots.txt
└── sitemap.xml
```

---

## OPTION A — Deploy via Git (Recommended)

### One-time setup (if not already done)
```bash
# Clone your repo locally
git clone https://github.com/phortex-dev/phortex-website.git
cd phortex-website
```

### Deploy the new site
```bash
# Copy all new files into your repo (replace the old single index.html)
# Run this from the folder containing the phortex-website.zip you downloaded

# 1. Unzip the new site files
unzip phortex-website.zip -d new-site

# 2. Copy into your repo (replaces existing files)
cp -r new-site/phortex/* /path/to/phortex-website/

# 3. Stage, commit, push
cd /path/to/phortex-website
git add .
git status   # review what changed
git commit -m "feat: full site rebuild — 5 pages, subfolder architecture, complete design system"
git push origin main
```

Cloudflare Pages auto-deploys on push to `main`. Live in ~60 seconds.

---

## OPTION B — Deploy via Claude Code (Easiest)

Install Claude Code if not already:
```bash
npm install -g @anthropic-ai/claude-code
```

Then in your repo folder:
```bash
cd /path/to/phortex-website
claude
```

Tell Claude Code:
> "I have a ZIP file of new website files at [path]. Replace all current files in this repo with the contents, then commit with message 'feat: full site rebuild' and push to origin main."

Claude Code will handle the file operations and git commands for you.

---

## OPTION C — Cloudflare Pages Manual Upload

1. Go to https://dash.cloudflare.com → Pages → your phortex project
2. Click "Upload assets" (or drag and drop the whole folder)
3. This bypasses git but doesn't set up auto-deploy

---

## Post-Deploy Checklist

### Required (site won't work fully without these)
- [ ] **Contact form**: Sign up at formspree.io → create form → copy ID
  - In `index.html`, replace `YOUR_FORM_ID` in the form action URL
  - Commit and push

- [ ] **Calendly**: 
  - Set up at calendly.com
  - Replace `/#contact` in nav CTA with your actual Calendly URL

### Recommended (SEO and analytics)
- [ ] **Google Analytics**: 
  - Get GA4 tracking ID from analytics.google.com
  - Add `<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXX"></script>` to each page `<head>`

- [ ] **Google Search Console**:
  - Verify ownership at search.google.com/search-console
  - Submit sitemap: `https://phortex.com/sitemap.xml`

### Visual assets (use ChatGPT DALL-E 3 with these prompts)

**Logo/favicon upgrade:**
> "Professional vector-style logo for 'Phortex' — a dark navy (#070D1A) square with rounded corners, with a bold glowing cyan (#00D4F0) letter P centered. Clean, minimal, tech company aesthetic. No gradients on the letter, just the cyan color. Add a subtle horizontal line below the P. SVG style."

**LinkedIn Company Page banner (1128×191px):**
> "Dark professional banner for cybersecurity/AI/college consulting company 'Phortex'. Very dark navy background (#070D1A) with subtle cyan (#00D4F0) grid lines. Left side: large 'PHORTEX.' text in bold white with cyan dot. Right side: three subtle glowing icons — lock, robot head, graduation cap — in cyan. Tagline below: 'Where Security Strategy Meets Business Reality'. Clean, premium, dark tech aesthetic."

**YouTube channel art (2560×1440px):**
> Same concept, wider format with safe zone for the center 1235×338px area.

**HeyGen avatar backgrounds:**
- Phortex Secure: "Professional dark studio background, deep navy blue (#0A1628), subtle diagonal light rays from upper right in cyan, slightly blurred. Clean, authoritative, TV news anchor aesthetic."
- Phortex AI: "Dark technology background, very dark navy with subtle purple (#8B5CF6) accent lighting from the left, faint circuit board pattern barely visible. Modern, forward-thinking."  
- Phortex Campus: "Clean, light-to-medium warm background, off-white or very light gray with subtle warm lighting. Professional but approachable. Like a tasteful office or library setting."

---

## Updating the Site

Every future update follows the same pattern:
1. Edit the relevant HTML file(s) locally
2. `git add . && git commit -m "your message" && git push`
3. Cloudflare auto-deploys in ~60 seconds

Or use Claude Code in your repo folder to make changes via conversation.

---

## Notes on the Architecture

- **No build step** — pure HTML/CSS/JS, no npm, no Node server required
- **Shared nav + footer** — injected by `js/components.js` — update once, applies everywhere
- **Cloudflare CDN** — your `_headers` file sets proper caching for all assets
- **SEO-ready** — canonical tags, OG tags, Schema.org JSON-LD, sitemap on every page
- **College comparison tool** — will be added as `campus/compare/index.html` in next session, uses College Scorecard API called directly from the browser (no backend needed)
