#!/usr/bin/env python3
"""Refresh data/auctions.json and data/reading.json from watchlist.txt and reading.txt.

Standard library only, so it runs anywhere (locally or in GitHub Actions).
Respects Bring a Trailer's robots.txt crawl delay of 1 second between requests.
"""
import html
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (personal portfolio feed; github.com)"
DELAY = 1.5


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def meta(page, prop):
    m = re.search(r'<meta[^>]+(?:property|name)="%s"[^>]+content="([^"]*)"' % re.escape(prop), page)
    if not m:
        m = re.search(r'<meta[^>]+content="([^"]*)"[^>]+(?:property|name)="%s"' % re.escape(prop), page)
    return html.unescape(m.group(1)).strip() if m else None


def read_lines(name):
    path = ROOT / name
    if not path.exists():
        return []
    return [l.strip() for l in path.read_text().splitlines() if l.strip() and not l.strip().startswith("#")]


def auction(url):
    page = fetch(url)
    title = meta(page, "og:title") or url
    no_reserve = title.lower().startswith("no reserve:")
    title = re.sub(r"^No Reserve:\s*", "", title)

    bid = re.search(r'data-testid="current-bid-amount">\s*([^<]+)<', page)
    until = re.search(r'data-until="(\d+)"', page)
    sold = re.search(r'(Sold for|Bid to)\s*(?:<[^>]+>\s*)*(?:USD\s*)?(\$[\d,]+)', page)

    ends = int(until.group(1)) if until else None
    live = ends is not None and ends > time.time()
    if live:  # a brand-new listing has no bid field yet
        status, amount = "live", bid.group(1).replace("USD", "").strip() if bid else None
    elif sold:
        status, amount = ("sold" if sold.group(1) == "Sold for" else "bid-to"), sold.group(2)
    else:
        status, amount = "ended", bid.group(1).replace("USD", "").strip() if bid else None

    return {
        "url": url,
        "title": title,
        "noReserve": no_reserve,
        "image": meta(page, "og:image"),
        "status": status,
        "amount": amount,
        "ends": ends,
    }


def clipping(line):
    parts = [p.strip() for p in line.split("|")]
    url, note = parts[0], (parts[1] if len(parts) > 1 else "")
    title_override = parts[2] if len(parts) > 2 else ""
    host = urlparse(url).netloc.replace("www.", "")
    item = {"url": url, "note": note, "title": title_override, "source": host, "published": None}
    try:
        page = fetch(url)
        item["title"] = title_override or meta(page, "og:title") or meta(page, "twitter:title") or ""
        item["source"] = meta(page, "og:site_name") or host
        item["published"] = (meta(page, "article:published_time") or "")[:10] or None
    except Exception as e:  # paywalls and bot walls are common; keep the link anyway
        print(f"  reading: could not fetch {url}: {e}", file=sys.stderr)
    if not item["title"]:
        item["title"] = host
    return item


def main():
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    auctions = []
    for url in read_lines("watchlist.txt"):
        try:
            auctions.append(auction(url))
            print(f"  auction: {auctions[-1]['title']} -> {auctions[-1]['status']} {auctions[-1]['amount']}")
        except Exception as e:
            print(f"  auction: could not fetch {url}: {e}", file=sys.stderr)
        time.sleep(DELAY)
    # Live auctions ending soonest first, then finished ones
    auctions.sort(key=lambda a: (a["status"] != "live", a["ends"] or 0))

    clippings = []
    for line in read_lines("reading.txt"):
        clippings.append(clipping(line))
        time.sleep(DELAY)

    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data/auctions.json").write_text(json.dumps({"updated": now, "auctions": auctions}, indent=2) + "\n")
    (ROOT / "data/reading.json").write_text(json.dumps({"updated": now, "clippings": clippings}, indent=2) + "\n")


if __name__ == "__main__":
    main()
