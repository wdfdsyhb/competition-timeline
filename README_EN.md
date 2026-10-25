# competition-timeline · Chinese Collegiate Competition Deadlines

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> One page for Chinese collegiate competition deadlines — a monthly timeline of what's open and what's closing, plus a subscribable .ics calendar.

A static aggregation site for Chinese collegiate competitions: it collects
competitions that are open for registration or about to close, offers a
monthly timeline view, filtering and countdowns, and a **directly
subscribable calendar (.ics)**.

Live site: **https://wdfdsyhb.github.io/competition-timeline/**

## What problem this solves

Deadlines for national collegiate competitions (mathematical modeling,
electronics design contest, Lanqiao Cup, Challenge Cup, various
design/writing/programming contests…) are scattered across hundreds of
official sites, WeChat accounts and aggregators, with no unified "when does
it close" view. This project's approach:

1. **Scrape**: pull structured competition + phase times from the
   52jingsai.com leaderboard index (its list pages carry a
   `competition||phase: time` format that parses directly with regex)
2. **Enrich from source**: for records without a time on the list page,
   fetch the article page and parse three time-line patterns
   ("phase: date", "from now until X", "before X"), also extracting the
   competition's real official-site link
3. **Build**: validate, classify (11 subject categories), sort by lead date,
   and produce a single-file static site + RFC 5545 calendar
4. **Deploy**: pure static hosting on GitHub Pages, zero backend

## Current data scale

| Metric | Value |
|---|---|
| Source records | 208 |
| Site entries (with a concrete time) | 166 |
| Calendar events (VEVENT) | 245 |
| Data confidence | Student competitions `tentative` (auto-parsed); corporate ones `confirmed` (official APIs / official schedules) |

### Data source breakdown

| Source | Records | Confidence | Type |
|---|---|---|---|
| 52jingsai leaderboard index | 172 | tentative | Aggregator (GB18030 pages) |
| China Graduate Innovation & Practice Competitions (cpipc) | 21 | confirmed | Official schedule HTML |
| Alibaba Cloud Tianchi | 13 | confirmed | Official list API (no login) |
| Baidu Star | 1 | confirmed | webpack chunk embedded data |
| Huawei Software Elite Challenge | 1 | confirmed | vite chunk embedded data |

## Quick start

### Browse

Visit the live site, or double-click `index.html` (a purely offline single
file with the data embedded).

### Subscribe to the calendar

- In a calendar app (phone or desktop), "Add subscribed calendar" and paste:
  `https://wdfdsyhb.github.io/competition-timeline/competitions.ics`
- When opened via local file://, the "Subscribe" button degrades to
  downloading a merged .ics file

### Build locally

```bash
pip install nothing    # stdlib only, zero dependencies
python tools/fetch_52jingsai.py      # scrape the list → data/candidates.json
python tools/enrich_articles.py      # enrich from article pages
python tools/enrich_official.py      # enrich from official sites (low hit rate, optional)

# Corporate-competition sources (each scraped separately, merged at the end)
python tools/fetch_cpipc.py          # Graduate Innovation & Practice Competitions
python tools/fetch_baidustar.py      # Baidu Star (static webpack-chunk extraction)
python tools/fetch_codecraft.py      # Huawei Soft Challenge (static vite-chunk extraction)
python tools/fetch_tianchi.py        # Alibaba Cloud Tianchi (official API)
python tools/merge_corporate.py      # merge into candidates.json (idempotent)

python tools/build_draft.py          # generate index.html + competitions.ics
```

## Repository layout

```
├── index.html              # Single-file site (data embedded, opens by double-click)
├── competitions.ics        # Full calendar (for subscription)
├── data/
│   ├── candidates.json     # Main data (52jingsai + merged corporate competitions)
│   ├── cpipc.json          # Graduate competitions series
│   ├── candidates_baidustar.json
│   ├── candidates_codecraft.json
│   └── candidates_tianchi.json
├── tools/
│   ├── fetch_52jingsai.py  # S-grade source: leaderboard index scraper
│   ├── enrich_articles.py  # Enrich times/official links from article pages
│   ├── enrich_official.py  # Enrich from official sites (P2)
│   ├── fetch_cpipc.py      # Corporate: official schedule HTML
│   ├── fetch_baidustar.py  # Corporate: static webpack-chunk extraction
│   ├── fetch_codecraft.py  # Corporate: static vite-chunk extraction
│   ├── fetch_tianchi.py    # Corporate: official JSON API
│   ├── merge_corporate.py  # Source merge (title normalization dedup + idempotent ids)
│   └── build_draft.py      # Builder: candidates → site + ics
├── docs/
│   ├── DATASOURCES-2026-10-22.md   # Data source field report (grading, params, pitfalls)
│   ├── GITHUB-SURVEY-2026-10-22.md # Survey of similar projects (none shipped; this project's niche)
│   └── PROGRESS.md                 # Progress and decision log
```

## Confidence notes

Three `confidence` levels (consistent with deadline-project conventions on GitHub):

- `confirmed` — verified against the official site (currently none)
- `tentative` — auto-parsed from aggregators/article pages, **the vast majority of sources**
- `estimated` — inferred from official sites via auto-parsing

Every card on the site carries a confidence badge. **Auto-parsed times can be
wrong (especially the semantics of "from now until X" and cross-year
confusion) — for important competitions, defer to the official site**. The
data keeps a `source` field; click a card to trace back to the original page.

## Architecture trade-offs (for forks/contributors)

- **Zero dependencies, zero backend**: stdlib urllib + regex, no
  Scrapy/Playwright. The cost is that JS-rendered sites (Lanqiao Cup etc.)
  can't be scraped — graded conclusions in `docs/DATASOURCES`
- **GB18030**: old domestic sites have messy encodings; fetchers sniff the
  charset declaration with utf-8/gbk fallbacks
- **Structured times on list pages > body parsing**: 52jingsai list snippets
  carry time fields natively, hitting 69%; article-page enrichment brings it
  to 77%
- **Direct official-site scraping is poor value**: most competition sites are
  SPAs or publish dates as images; P2 hit 1 of 21, see PROGRESS.md
- **Annual refresh**: competition dates change yearly; re-run the fetch chain
  each September when the new season is announced

## Roadmap

- [ ] Manually verify top high-value competitions (MCM / electronics / Challenge Cup / Internet+) → confirmed
- [ ] Annual September sweep (GitHub Actions cron + auto PR)
- [ ] More sources: China University Students Online, national entrepreneurship service network
- [x] Corporate sources: cpipc / Baidu Star / Huawei Soft Challenge / Alibaba Tianchi
- [ ] Tencent AI Arena (API 403, competition-page chunk 404, shelved)
- [ ] Mini-program client (same JSON data)

## Three tricks for scraping corporate competitions

Corporate competition sites are almost all SPAs, but schedule data often
lives somewhere statically reachable. Three routes validated in this project:

| Trick | Applies when | Implementation |
|---|---|---|
| Official JSON API | Backend endpoints need no login | `fetch_tianchi.py`: `/v3/proxy/competition/api/race/page`; the `isActive` param must be the number `1` |
| Static webpack-chunk extraction | SSR/template data is embedded in build output | `fetch_baidustar.py`: get hash tables from `_buildManifest` (**take the last match**, one each for css/js), pull route chunks, regex out the schedule |
| Static vite-chunk extraction | Vite build, competition ID in env variables | `fetch_codecraft.py`: mine `VITE_APP_CompetitionId_2026` from the main bundle; route chunks carry the full schedule in `mu=[{id,date}]` |

Counter-example: Tencent AI Arena (`aiarena.tencent.com`) — endpoints like
`/api/v5/fe/AIArena/ListMatch` return 403 across the board and the `/match`
route chunk 404s; only the news list API works. No structured schedule, and
the reason for giving up is on record.

## Related docs

- Data source field report: [docs/DATASOURCES-2026-10-22.md](docs/DATASOURCES-2026-10-22.md)
- Survey of similar projects: [docs/GITHUB-SURVEY-2026-10-22.md](docs/GITHUB-SURVEY-2026-10-22.md)
- Progress and decisions: [docs/PROGRESS.md](docs/PROGRESS.md)

## License

Data is scraped from public web pages; copyright belongs to the original
publishers. Code is MIT.

---

> 🇨🇳 中文文档: [README.md](README.md)
