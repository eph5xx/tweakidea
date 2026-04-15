# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Search Hacker News posts via the free Algolia API and print JSON to stdout."""

import argparse
import json
import sys
import time
from datetime import datetime, timezone

import httpx  # type: ignore


ALGOLIA_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
VALID_TAGS = {"story", "show_hn", "ask_hn", "front_page", "poll"}


def relative_time_from_epoch(ts: int) -> str:
    """Convert a unix timestamp to a short relative-time string."""
    try:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        seconds = int((now - dt).total_seconds())
        if seconds < 60:
            return "just now"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m ago"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h ago"
        days = hours // 24
        if days < 30:
            return f"{days}d ago"
        months = days // 30
        if months < 12:
            return f"{months}mo ago"
        return f"{days // 365}y ago"
    except Exception:
        return ""


def build_tags_param(tags_csv: str) -> str:
    """Validate and format the Algolia tags= filter (comma = AND)."""
    parts = [t.strip() for t in tags_csv.split(",") if t.strip()]
    for p in parts:
        if p not in VALID_TAGS:
            raise ValueError(
                f"Invalid --tags value '{p}'. Allowed: {', '.join(sorted(VALID_TAGS))}"
            )
    return ",".join(parts)


def build_numeric_filters(min_points: int, days: int) -> str:
    """Build Algolia numericFilters string. Empty string if no filters apply."""
    filters = []
    if min_points > 0:
        filters.append(f"points>={min_points}")
    if days > 0:
        cutoff = int(time.time()) - days * 86400
        filters.append(f"created_at_i>={cutoff}")
    return ",".join(filters)


def search(
    query: str,
    days: int,
    tags: str,
    min_points: int,
    limit: int,
) -> list[dict]:
    params: dict[str, str | int] = {
        "query": query,
        "tags": tags,
        "hitsPerPage": limit,
    }
    numeric = build_numeric_filters(min_points, days)
    if numeric:
        params["numericFilters"] = numeric

    print(
        f"Searching HN: query={query!r} tags={tags} days={days} "
        f"min_points={min_points} limit={limit}",
        file=sys.stderr,
    )

    resp = httpx.get(ALGOLIA_SEARCH_URL, params=params, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    data = resp.json()
    hits = data.get("hits", [])
    print(f"Got {len(hits)} hits from Algolia.", file=sys.stderr)

    results = []
    for h in hits:
        object_id = h.get("objectID")
        if not object_id:
            continue
        created_ts = h.get("created_at_i") or 0
        results.append(
            {
                "id": object_id,
                "title": h.get("title") or h.get("story_title") or "",
                "url": h.get("url"),
                "points": h.get("points") or 0,
                "num_comments": h.get("num_comments") or 0,
                "author": h.get("author") or "",
                "created_at_i": created_ts,
                "relative_age": relative_time_from_epoch(created_ts) if created_ts else "",
                "hn_url": f"https://news.ycombinator.com/item?id={object_id}",
            }
        )
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Search Hacker News via Algolia and print JSON to stdout"
    )
    parser.add_argument("--query", required=True, help="Freeform search query")
    parser.add_argument(
        "--days",
        type=int,
        required=True,
        help="Lookback window in days (0 = no time filter)",
    )
    parser.add_argument(
        "--tags",
        default="story",
        help="Comma-separated Algolia tags (story, show_hn, ask_hn, front_page, poll). Default: story",
    )
    parser.add_argument(
        "--min-points",
        type=int,
        default=10,
        help="Minimum points on a hit (default: 10, set 0 to disable)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Max hits to return (default: 20, max: 50)",
    )
    args = parser.parse_args()

    if args.days < 0:
        parser.error("--days must be >= 0")
    if args.min_points < 0:
        parser.error("--min-points must be >= 0")
    if args.limit < 1 or args.limit > 50:
        parser.error("--limit must be between 1 and 50")

    try:
        tags = build_tags_param(args.tags)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        hits = search(
            query=args.query,
            days=args.days,
            tags=tags,
            min_points=args.min_points,
            limit=args.limit,
        )
    except httpx.HTTPError as e:
        print(f"HTTP error talking to Algolia HN API: {e}", file=sys.stderr)
        sys.exit(1)

    json.dump(hits, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
