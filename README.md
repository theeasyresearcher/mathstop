# MathStatDS Hub ∑

**A zero-cost, auto-updated platform for Mathematics, Statistics & Data Science events** — exams, conferences, workshops, fellowships, and webinars, for India and the World.  
Scraped daily from 65+ sources, classified automatically, and served as a static GitHub Pages site with no servers, no databases, and no paid APIs.

---

## Screenshot

> _(Replace this with a screenshot after first run)_
>
> ![MathStatDS Hub Screenshot](screenshot.png)

---

## Setup (3 steps)

### 1. Fork this repository
Click **Fork** on GitHub. Your copy lives at `https://github.com/yourusername/mathstatds-hub`.

### 2. Enable GitHub Pages
`Settings → Pages → Source: Deploy from branch → Branch: main / (root) → Save`

### 3. Enable GitHub Actions
`Actions tab → "I understand my workflows, go ahead and enable them"`

---

## First Run

Go to: `Actions → Daily Update → Run workflow → Run workflow`

This takes ~5 minutes. After it completes, your live site is at:

```
https://yourusername.github.io/mathstatds-hub
```

The pipeline runs automatically every day at **6:00 AM IST**.

---

## Adding / Editing Sources

Edit `master_maths_websites.csv`. Each row:

| Column | Description |
|--------|-------------|
| `id` | Unique integer |
| `name` | Display name |
| `url` | Page to scrape |
| `scrape_method` | `requests` or `playwright` |
| `priority` | 1 = highest |

Commit the CSV. The next scheduled run picks it up automatically.

---

## How Classification Works

**Pass 1 — Category** (first keyword match wins, priority order):

| Priority | Category | Example keywords |
|----------|----------|-----------------|
| 1 | Exam Notification | GATE, NET, JAM, hall ticket, result |
| 2 | Fellowship / Award | fellowship, JRF, scholarship, postdoc |
| 3 | Workshop / School | workshop, FDP, STTP, summer school |
| 4 | Webinar / Lecture | webinar, colloquium, zoom, virtual talk |
| 5 | Conference | conference, symposium, CFP |

**Pass 2 — Location:**
- **India** — matches keywords in `india_keywords.csv` (institutions, states, cities) or URL contains `.ac.in`
- **World** — everything else

Rules live in `classify_rules.csv` and `india_keywords.csv` — edit them to tune behaviour.

---

## File Structure

```
mathstatds-hub/
├── scraper.py              # Fetches all sources → data/raw_items.json
├── classify.py             # 2-pass classify + dedup + expiry → data/items.json
├── build_site.py           # Generates index.html from data/items.json
├── requirements.txt        # Python dependencies
├── master_maths_websites.csv  # 65+ source definitions
├── classify_rules.csv      # Category keyword rules
├── india_keywords.csv      # India location keywords
├── .github/
│   └── workflows/
│       └── update.yml      # Daily GitHub Actions cron
├── data/
│   ├── items.json          # Current listings (committed by Actions)
│   ├── seen_ids.json       # MD5 URL dedup store
│   └── seen_titles.json    # Title similarity dedup store
├── index.html              # Generated frontend (overwritten by pipeline)
└── scraper_errors.log      # Per-run error log (committed by Actions)
```

---

## Pipeline Flow

```
GitHub Actions cron (6 AM IST)
  └─ scraper.py       → data/raw_items.json   (all sources)
  └─ classify.py      → data/items.json        (classified, deduped, expired removed)
  └─ build_site.py    → index.html             (self-contained frontend)
  └─ git commit + push
```

---

## Tech Stack

| Layer | Tool | Cost |
|-------|------|------|
| Hosting | GitHub Pages | Free |
| Runner | GitHub Actions | Free (2,000 min/month) |
| Scraper | Python + requests + BeautifulSoup + Playwright | Free |
| Storage | Flat JSON in repo | Free |
| Frontend | Single HTML file, no CDN except Google Fonts | Free |

---

## License

MIT © 2026 — fork, modify, deploy freely.
