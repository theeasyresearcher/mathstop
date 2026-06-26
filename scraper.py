"""
scraper.py — MathStatDS Hub
Scrapes all sources from master_maths_websites.csv
Outputs: data/raw_items.json, scraper_errors.log
"""

import csv
import hashlib
import json
import logging
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    filename="scraper_errors.log",
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MathStatDSBot/1.0)"}
TIMEOUT = 20
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(t: str) -> str:
    if not t:
        return ""
    return re.sub(r"\s+", " ", t).strip()


def truncate(t: str, n: int = 400) -> str:
    return t[:n] if len(t) <= n else t[: n - 1] + "…"


def parse_date(text: str):
    """Best-effort date parse → YYYY-MM-DD or None."""
    if not text:
        return None
    import dateutil.parser as dp
    patterns = [
        r"\b(\d{4}-\d{2}-\d{2})\b",
        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
        r"\b(\d{1,2}\s+\w+\s+\d{4})\b",
        r"\b(\w+\s+\d{1,2},?\s+\d{4})\b",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                return dp.parse(m.group(1), dayfirst=True).strftime("%Y-%m-%d")
            except Exception:
                continue
    return None


def make_item(title, description, url, deadline, event_date, source_name, source_url):
    return {
        "id": md5(url),
        "title": clean_text(title)[:250],
        "description": truncate(clean_text(description)),
        "url": url,
        "deadline": deadline,
        "event_date": event_date,
        "location": None,   # filled by classify.py
        "category": None,   # filled by classify.py
        "source_name": source_name,
        "source_url": source_url,
        "is_new": True,
        "scraped_at": now_iso(),
    }


# ── Domain-level delay tracker ────────────────────────────────────────────────
_last_request: dict[str, float] = {}


def polite_get(url, session):
    domain = urlparse(url).netloc
    wait = random.uniform(1, 2)
    since = time.time() - _last_request.get(domain, 0)
    if since < wait:
        time.sleep(wait - since)
    _last_request[domain] = time.time()
    resp = session.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp


# ── Generic requests scraper ──────────────────────────────────────────────────

def scrape_requests(source, session):
    url = source["url"]
    resp = polite_get(url, session)
    soup = BeautifulSoup(resp.text, "lxml")
    items = []

    # Collect all <a> tags with reasonable link text
    for a in soup.find_all("a", href=True):
        text = clean_text(a.get_text())
        if len(text) < 10 or len(text) > 300:
            continue
        href = urljoin(url, a["href"])
        if not href.startswith("http"):
            continue
        # Find nearby date text
        parent = a.parent
        context = clean_text(parent.get_text()) if parent else ""
        deadline = parse_date(context)
        event_date = deadline  # best guess; classify may refine
        desc = truncate(context)
        items.append(make_item(text, desc, href, deadline, event_date,
                               source["name"], url))
    return items


# ── Playwright scraper ────────────────────────────────────────────────────────

def scrape_playwright(source):
    from playwright.sync_api import sync_playwright
    url = source["url"]
    items = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(extra_http_headers=HEADERS)
        page.goto(url, timeout=60000)
        page.wait_for_timeout(3000)
        html = page.content()
        browser.close()
    soup = BeautifulSoup(html, "lxml")
    for a in soup.find_all("a", href=True):
        text = clean_text(a.get_text())
        if len(text) < 10 or len(text) > 300:
            continue
        href = urljoin(url, a["href"])
        if not href.startswith("http"):
            continue
        parent = a.parent
        context = clean_text(parent.get_text()) if parent else ""
        deadline = parse_date(context)
        items.append(make_item(text, context[:400], href, deadline, deadline,
                               source["name"], url))
    return items


# ── Per-source custom scrapers ────────────────────────────────────────────────

def scrape_atmschools(source, session):
    resp = polite_get(source["url"], session)
    soup = BeautifulSoup(resp.text, "lxml")
    items = []
    for div in soup.select(".views-row, article, .event-item, li"):
        a = div.find("a", href=True)
        if not a:
            continue
        title = clean_text(a.get_text())
        if len(title) < 10:
            continue
        href = urljoin(source["url"], a["href"])
        desc = truncate(clean_text(div.get_text()))
        date = parse_date(div.get_text())
        items.append(make_item(title, desc, href, date, date, source["name"], source["url"]))
    return items or scrape_requests(source, session)


def scrape_ams_calendar(source, session):
    resp = polite_get(source["url"], session)
    soup = BeautifulSoup(resp.text, "lxml")
    items = []
    for tr in soup.select("table tr"):
        cells = tr.find_all("td")
        if len(cells) < 2:
            continue
        a = tr.find("a", href=True)
        if not a:
            continue
        title = clean_text(a.get_text())
        href = urljoin(source["url"], a["href"])
        text = clean_text(tr.get_text())
        date = parse_date(text)
        items.append(make_item(title, text[:400], href, date, date, source["name"], source["url"]))
    return items or scrape_requests(source, session)


def scrape_wikicfp(source, session):
    resp = polite_get(source["url"], session)
    soup = BeautifulSoup(resp.text, "lxml")
    items = []
    for row in soup.select("table.gglu tr, tr.even, tr.odd"):
        a = row.find("a", href=True)
        if not a:
            continue
        title = clean_text(a.get_text())
        href = urljoin("http://www.wikicfp.com", a["href"])
        text = clean_text(row.get_text())
        date = parse_date(text)
        items.append(make_item(title, text[:400], href, date, date, source["name"], source["url"]))
    return items or scrape_requests(source, session)


def scrape_researchseminars(source, session):
    resp = polite_get(source["url"], session)
    soup = BeautifulSoup(resp.text, "lxml")
    items = []
    for div in soup.select(".seminar-row, .talk-row, article, .event"):
        a = div.find("a", href=True)
        if not a:
            continue
        title = clean_text(a.get_text())
        if len(title) < 5:
            continue
        href = urljoin(source["url"], a["href"])
        text = clean_text(div.get_text())
        date = parse_date(text)
        items.append(make_item(title, text[:400], href, date, date, source["name"], source["url"]))
    return items or scrape_requests(source, session)


def scrape_siam(source, session):
    resp = polite_get(source["url"], session)
    soup = BeautifulSoup(resp.text, "lxml")
    items = []
    for div in soup.select(".views-row, .conference-item, article, li.conference"):
        a = div.find("a", href=True)
        if not a:
            continue
        title = clean_text(a.get_text())
        href = urljoin(source["url"], a["href"])
        text = clean_text(div.get_text())
        date = parse_date(text)
        items.append(make_item(title, text[:400], href, date, date, source["name"], source["url"]))
    return items or scrape_requests(source, session)


CUSTOM_SCRAPERS = {
    "https://www.atmschools.org/": scrape_atmschools,
    "https://www.ams.org/calendar/mathcalendar.pl": scrape_ams_calendar,
    "https://www.ams.org/meetings/math-calendar": scrape_ams_calendar,
    "http://www.wikicfp.com/cfp/call?conference=data+science": scrape_wikicfp,
    "http://www.wikicfp.com/cfp/call?conference=mathematics": scrape_wikicfp,
    "http://www.wikicfp.com/cfp/call?conference=statistics": scrape_wikicfp,
    "https://researchseminars.org/": scrape_researchseminars,
    "https://mathseminars.org": scrape_researchseminars,
    "https://www.siam.org/conferences/": scrape_siam,
    "https://www.siam.org": scrape_siam,
}


# ── Main ──────────────────────────────────────────────────────────────────────

def load_sources() -> list[dict]:
    sources = []
    with open("master_maths_websites.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sources.append(row)
    return sources


def main():
    sources = load_sources()
    all_items: list[dict] = []
    session = requests.Session()

    for src in sources:
        name = src.get("name", "")
        url = src.get("url", "").strip()
        method = src.get("scrape_method", "requests").strip().lower()
        print(f"[scraper] {name} ({method}) …", flush=True)
        try:
            if url in CUSTOM_SCRAPERS and method == "requests":
                items = CUSTOM_SCRAPERS[url](src, session)
            elif method == "playwright":
                items = scrape_playwright(src)
            else:
                items = scrape_requests(src, session)
            print(f"  → {len(items)} items")
            all_items.extend(items)
        except Exception as exc:
            log.error("Source %s (%s): %s", name, url, exc)
            print(f"  ✗ ERROR: {exc}")

    out = DATA_DIR / "raw_items.json"
    out.write_text(json.dumps(all_items, ensure_ascii=False, indent=2))
    print(f"\n[scraper] Done. {len(all_items)} raw items → {out}")


if __name__ == "__main__":
    main()
