# GearBear

By ImpatientBeastStudios. Formerly called GarageManager; this repository keeps the old name so existing links keep working.

Free Windows app for car garages: appointments, vehicles, customers, job cards and service history. Works offline; the data stays on your PC.

**Website and download: https://gearbear.impatientbeaststudios.com**

This repository holds the website and the released installers (see [Releases](https://github.com/TeddyBear1998/garagemanager/releases)). The app's source code is not public.

- `index.html`, `img/`: the website, served by Cloudflare (Worker `gearbear`, `wrangler.jsonc`) on every push
- **Edit the website pages in `src/`, then run `python3 build.py`, then commit.** `src/index.html` and
  `src/privacy.html` hold both languages (`lang` spans and `<img lang>` pairs; Latvian title and
  descriptions in `data-lv`). The build writes `index.html`, `privacy.html` (English, `/`, `/privacy`),
  `lv/` (Latvian, `/lv/`, `/lv/privacy`) and `sitemap.xml`; never edit those by hand. One address per
  language since 10.11.2026, for Google and the AdSense review. `src/` and `build.py` are left out of
  the served site by `.assetsignore`. The script is shared by every IBS site
  (`~/Documents/impatientbeaststudios/README.md`)
- `latest.json`: the newest version; installed copies read it to show the "new version" bar
- `docs/`: the old address, https://teddybear1998.github.io/garagemanager/ (GitHub Pages, folder `/docs`).
  A "we've moved" page plus a copy of `latest.json`, which must stay: copies of GearBear up to
  0.12.x read their update feed from there. The release script writes both copies.
- Look: header, footer and colours follow the studio guide
  (`~/Documents/impatientbeaststudios/BRAND.md`): warm page, warm dark bar, `Gear`/`Bear`
  wordmark, the logo's wrench red as the accent (04.11.2026).
