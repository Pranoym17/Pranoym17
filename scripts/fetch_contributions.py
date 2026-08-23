#!/usr/bin/env python3
"""
fetch_contributions.py <username>

Fetches the public contribution-calendar HTML fragment GitHub itself uses
(no GraphQL API, no token needed), parses each day cell, and writes
data/contributions.json with raw days plus derived stats.
"""
import re
import sys
import json
import datetime
import requests
from bs4 import BeautifulSoup

def fetch(username):
    url = f"https://github.com/users/{username}/contributions"
    headers = {"User-Agent": "Mozilla/5.0 (profile-readme-bot)"}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.text

# "5 contributions on August 24th." / "1 contribution on ..." / "No contributions on ..."
_COUNT_RE = re.compile(r"^(No|\d+)\s+contributions?\s+on", re.IGNORECASE)

def parse(html):
    soup = BeautifulSoup(html, "html.parser")

    # Current GitHub markup: each day is a <td class="ContributionCalendar-day">
    # with data-date/data-level but no count; the count lives in a sibling
    # <tool-tip for="<cell-id>">N contributions on <date>.</tool-tip>.
    tooltip_by_target = {}
    for tt in soup.select("tool-tip[for]"):
        tooltip_by_target[tt.get("for")] = tt.get_text(strip=True)

    days = []
    cells = soup.select("td.ContributionCalendar-day, td[data-date]")
    for cell in cells:
        date = cell.get("data-date")
        if date is None:
            continue
        level = cell.get("data-level")
        level = int(level) if level is not None else 0

        count = 0
        cell_id = cell.get("id")
        tooltip_text = tooltip_by_target.get(cell_id, "")
        m = _COUNT_RE.match(tooltip_text)
        if m:
            count = 0 if m.group(1).lower() == "no" else int(m.group(1))

        days.append({"date": date, "level": level, "count": count})

    days.sort(key=lambda d: d["date"])
    return days

def derive_stats(days):
    total = sum(d["count"] for d in days)
    # current streak (from most recent day backwards)
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break
    # longest streak
    longest = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    best_day = max(days, key=lambda d: d["count"]) if days else None
    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest,
        "best_day": best_day["date"] if best_day else None,
        "best_day_count": best_day["count"] if best_day else 0,
    }

def parse_header_total(html):
    soup = BeautifulSoup(html, "html.parser")
    h2 = soup.select_one("h2#js-contribution-activity-description")
    if not h2:
        return None
    m = re.search(r"([\d,]+)\s+contributions", h2.get_text(" ", strip=True))
    return int(m.group(1).replace(",", "")) if m else None

def main(username):
    html = fetch(username)
    days = parse(html)
    if not days:
        print("WARNING: parsed 0 days -- GitHub markup may have changed.", file=sys.stderr)
    stats = derive_stats(days)
    header_total = parse_header_total(html)
    if header_total is not None and header_total != stats["total"]:
        print(
            f"WARNING: parsed total ({stats['total']}) != page header total "
            f"({header_total}) -- tooltip parsing may have missed some cells.",
            file=sys.stderr,
        )
    out = {
        "username": username,
        "fetched_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "days": days,
        "stats": stats,
    }
    with open("data/contributions.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote data/contributions.json  ({len(days)} days, total={stats['total']})")

if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "pranoym17"
    main(username)
