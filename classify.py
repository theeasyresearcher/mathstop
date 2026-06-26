"""
classify.py — MathStatDS Hub
2-pass classification (category + location) + 2-layer deduplication + expiry
Reads:  data/raw_items.json, data/seen_ids.json, data/seen_titles.json
Writes: data/items.json, data/seen_ids.json, data/seen_titles.json
"""

import csv
import difflib
import json
import re
from datetime import date, timedelta
from pathlib import Path

DATA_DIR = Path("data")

# ── Load classification rules ─────────────────────────────────────────────────

def load_classify_rules() -> list[dict]:
    rules = []
    with open("classify_rules.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            kws = [k.strip().lower() for k in row["keywords"].split(",") if k.strip()]
            rules.append({
                "category": row["type"].strip().replace(" ", " / ") if "/" not in row["type"] else row["type"].strip(),
                "priority": int(row["priority"]),
                "keywords": kws,
            })
    # Normalise category names to match schema
    name_map = {
        "Exam Notification": "Exam Notification",
        "Fellowship Award": "Fellowship / Award",
        "Fellowship / Award": "Fellowship / Award",
        "Workshop School": "Workshop / School",
        "Workshop / School": "Workshop / School",
        "Webinar Lecture": "Webinar / Lecture",
        "Webinar / Lecture": "Webinar / Lecture",
        "Conference": "Conference",
    }
    for r in rules:
        r["category"] = name_map.get(r["category"], r["category"])
    rules.sort(key=lambda x: x["priority"])
    return rules


def load_india_keywords() -> list[str]:
    kws = []
    with open("india_keywords.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            kws.extend([k.strip() for k in row["keywords"].split(",") if k.strip()])
    return kws


RULES = load_classify_rules()
INDIA_KW = load_india_keywords()


# ── Pass 1: Category ──────────────────────────────────────────────────────────

def classify_category(item: dict) -> str:
    blob = (item.get("title", "") + " " + item.get("description", "")).lower()
    for rule in RULES:
        for kw in rule["keywords"]:
            if kw in blob:
                return rule["category"]
    return "Conference"


# ── Pass 2: Location ──────────────────────────────────────────────────────────

def classify_location(item: dict) -> str:
    blob = (item.get("title", "") + " " + item.get("description", "") +
            " " + item.get("url", "") + " " + item.get("source_url", "")).lower()
    # .ac.in domain check
    if ".ac.in" in blob or ".edu.in" in blob:
        return "India"
    for kw in INDIA_KW:
        if kw.lower() in blob:
            return "India"
    return "World"


# ── Expiry ────────────────────────────────────────────────────────────────────

def is_expired(item: dict) -> bool:
    today = date.today()
    ed = item.get("event_date")
    dl = item.get("deadline")
    try:
        if ed and date.fromisoformat(ed) < today - timedelta(days=3):
            return True
    except ValueError:
        pass
    try:
        if dl and date.fromisoformat(dl) < today - timedelta(days=1):
            return True
    except ValueError:
        pass
    return False


# ── Deduplication ─────────────────────────────────────────────────────────────

def dedup(raw_items: list[dict], seen_ids: dict, seen_titles: dict) -> list[dict]:
    kept = []
    for item in raw_items:
        uid = item["id"]
        # Layer 1: URL hash
        if uid in seen_ids:
            continue
        # Layer 2: title similarity
        title = item.get("title", "").lower().strip()
        duplicate = False
        for existing_title, existing_id in seen_titles.items():
            ratio = difflib.SequenceMatcher(None, title, existing_title).ratio()
            if ratio > 0.85:
                # Keep item with longer description
                existing_items = [i for i in kept if i["id"] == existing_id]
                if existing_items:
                    ex = existing_items[0]
                    if len(item.get("description", "")) > len(ex.get("description", "")):
                        kept.remove(ex)
                        del seen_titles[existing_title]
                        del seen_ids[ex["id"]]
                        break
                duplicate = True
                break
        if not duplicate:
            seen_ids[uid] = True
            seen_titles[title] = uid
            kept.append(item)
    return kept


# ── Main ──────────────────────────────────────────────────────────────────────

def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return default
    return default


def main():
    raw_items = load_json(DATA_DIR / "raw_items.json", [])
    seen_ids = load_json(DATA_DIR / "seen_ids.json", {})
    seen_titles = load_json(DATA_DIR / "seen_titles.json", {})
    existing_items = load_json(DATA_DIR / "items.json", [])

    print(f"[classify] {len(raw_items)} raw items")

    # Classify new items
    for item in raw_items:
        item["category"] = classify_category(item)
        item["location"] = classify_location(item)

    # Merge with existing (carry forward non-expired)
    active_existing = [i for i in existing_items if not is_expired(i)]
    # Mark existing as not-new
    for i in active_existing:
        i["is_new"] = False

    # Removed expired → clean seen_ids
    expired_ids = {i["id"] for i in existing_items if is_expired(i)}
    for eid in expired_ids:
        seen_ids.pop(eid, None)
    # Remove their titles
    for title, uid in list(seen_titles.items()):
        if uid in expired_ids:
            del seen_titles[title]

    print(f"[classify] {len(active_existing)} active existing, {len(expired_ids)} expired removed")

    # Dedup new items against each other and existing
    # First build seen from active_existing
    seen_ids_active = {i["id"]: True for i in active_existing}
    seen_titles_active = {i["title"].lower().strip(): i["id"] for i in active_existing}

    # Merge seen
    seen_ids_active.update(seen_ids)
    seen_titles_active.update(seen_titles)

    new_deduped = dedup(raw_items, seen_ids_active, seen_titles_active)
    print(f"[classify] {len(new_deduped)} new items after dedup")

    # Filter title-only items (too short / nav links)
    def is_meaningful(item):
        t = item.get("title", "")
        return (
            len(t) >= 15
            and not re.fullmatch(r"[\W\d]+", t)
            and item.get("url", "").startswith("http")
        )

    new_deduped = [i for i in new_deduped if is_meaningful(i)]
    print(f"[classify] {len(new_deduped)} after quality filter")

    # Combine
    all_items = active_existing + new_deduped

    # Sort by deadline soonest, nulls last
    def sort_key(i):
        d = i.get("deadline") or i.get("event_date")
        return d if d else "9999-99-99"
    all_items.sort(key=sort_key)

    # Persist
    (DATA_DIR / "items.json").write_text(
        json.dumps(all_items, ensure_ascii=False, indent=2))
    (DATA_DIR / "seen_ids.json").write_text(
        json.dumps(seen_ids_active, ensure_ascii=False, indent=2))
    (DATA_DIR / "seen_titles.json").write_text(
        json.dumps(seen_titles_active, ensure_ascii=False, indent=2))

    print(f"[classify] Done. {len(all_items)} total items in data/items.json")


if __name__ == "__main__":
    main()
