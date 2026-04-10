# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright", "httpx", "trafilatura"]
# ///
"""Fetch a Hacker News post (article + all comments) and write to markdown."""

import argparse
import html
import os
import re
import sys
from datetime import datetime, timezone

import httpx # type: ignore
import trafilatura # type: ignore
from playwright.sync_api import sync_playwright # type: ignore


def parse_hn_id(input_str: str) -> str:
    """Extract numeric HN item ID from a URL or bare ID."""
    input_str = input_str.strip()
    if input_str.isdigit():
        return input_str
    m = re.search(r"[?&]id=(\d+)", input_str)
    if m:
        return m.group(1)
    raise ValueError(f"Cannot parse HN item ID from: {input_str}")


def fetch_hn_data(item_id: str) -> dict:
    """Fetch full post + comment tree from Algolia HN API."""
    url = f"https://hn.algolia.com/api/v1/items/{item_id}"
    resp = httpx.get(url, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    return resp.json()


def fetch_article(url: str) -> str | None:
    """Render a page with Playwright and extract article text via trafilatura."""
    article_html = None

    # Try Playwright first for JS-rendered pages
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            article_html = page.content()
            browser.close()
    except Exception:
        pass

    # Fall back to plain HTTP if Playwright failed
    if not article_html:
        try:
            resp = httpx.get(
                url,
                timeout=30,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; hnparse/1.0)"},
            )
            resp.raise_for_status()
            article_html = resp.text
        except Exception:
            return None

    return trafilatura.extract(
        article_html,
        output_format="markdown",
        include_links=True,
        include_tables=True,
        include_formatting=True,
        favor_recall=True,
    )


def clean_comment_html(text: str) -> str:
    """Convert HN comment HTML to plain markdown-ish text."""
    if not text:
        return ""
    s = text
    # <p> tags to double newline
    s = re.sub(r"<p>", "\n\n", s)
    # <a href="...">text</a> to [text](href)
    s = re.sub(r'<a\s+href="([^"]*)"[^>]*>(.*?)</a>', r"[\2](\1)", s)
    # <i>text</i> to *text*
    s = re.sub(r"<i>(.*?)</i>", r"*\1*", s)
    # <pre><code>text</code></pre> to fenced code block
    s = re.sub(
        r"<pre><code>(.*?)</code></pre>", lambda m: f"\n```\n{m.group(1)}\n```\n", s, flags=re.DOTALL
    )
    # <code>text</code> to `text`
    s = re.sub(r"<code>(.*?)</code>", r"`\1`", s)
    # Strip remaining tags
    s = re.sub(r"<[^>]+>", "", s)
    # Decode HTML entities
    s = html.unescape(s)
    return s.strip()


def relative_time(iso_str: str) -> str:
    """Convert ISO timestamp to a relative time string."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - dt
        seconds = int(delta.total_seconds())
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
        return iso_str or ""


def count_comments(children: list[dict]) -> int:
    """Count total comments recursively."""
    total = 0
    for child in children:
        if child is None:
            continue
        total += 1
        total += count_comments(child.get("children", []))
    return total


def format_comments(children: list[dict], depth: int = 0) -> str:
    """Recursively format comment tree using blockquote nesting."""
    lines = []
    for child in children:
        if child is None:
            continue

        prefix = ">" * (depth + 1) + " "
        author = child.get("author")
        text = child.get("text")
        created = child.get("created_at", "")

        if author is None or text is None:
            lines.append(f"{prefix}*[deleted]*")
            lines.append("")
        else:
            time_str = relative_time(created)
            cleaned = clean_comment_html(text)
            # Prefix every line of the comment body
            body_lines = cleaned.split("\n")
            lines.append(f"{prefix}**{author}** | {time_str}")
            for bl in body_lines:
                if bl.strip():
                    lines.append(f"{prefix}{bl}")
                else:
                    lines.append(f"{'>' * (depth + 1)}")
            lines.append("")

        # Recurse into replies
        sub = child.get("children", [])
        if sub:
            lines.append(format_comments(sub, depth + 1))

    return "\n".join(lines)


def build_markdown(hn_data: dict, article_text: str | None) -> str:
    """Assemble the full markdown document."""
    title = hn_data.get("title", "Untitled")
    author = hn_data.get("author", "unknown")
    points = hn_data.get("points", 0)
    created = hn_data.get("created_at", "")
    item_id = hn_data.get("id", "")
    url = hn_data.get("url")
    post_text = hn_data.get("text")
    children = hn_data.get("children", [])

    date_str = relative_time(created) if created else ""
    total_comments = count_comments(children)

    parts = []
    parts.append(f"# {title}\n")
    parts.append(f"**Author:** {author} | **Score:** {points} points | **Date:** {date_str}")
    parts.append(f"**HN Link:** https://news.ycombinator.com/item?id={item_id}")
    if url:
        parts.append(f"**Article URL:** {url}")
    parts.append("\n---\n")

    # Article or self-post body
    parts.append("## Article\n")
    if url and article_text:
        parts.append(article_text)
    elif url and not article_text:
        parts.append("*[Article could not be extracted -- may be paywalled or require authentication]*")
    elif post_text:
        parts.append(clean_comment_html(post_text))
    else:
        parts.append("*[No article or text content]*")

    parts.append("\n---\n")

    # Comments
    parts.append(f"## Comments ({total_comments} comments)\n")
    if children:
        parts.append(format_comments(children))
    else:
        parts.append("*No comments yet.*")

    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Fetch a HN post to markdown")
    parser.add_argument("hn_id", help="HN URL or numeric item ID")
    parser.add_argument(
        "-o", "--output-dir",
        help="Output directory (default: ~/.tweakidea/hn/hn-{id})",
        default=None,
    )
    args = parser.parse_args()

    item_id = parse_hn_id(args.hn_id)
    print(f"Fetching HN item {item_id}...", file=sys.stderr)

    hn_data = fetch_hn_data(item_id)
    url = hn_data.get("url")

    article_text = None
    if url:
        print(f"Fetching article: {url}", file=sys.stderr)
        article_text = fetch_article(url)
        if article_text:
            print("Article extracted successfully.", file=sys.stderr)
        else:
            print("Could not extract article content.", file=sys.stderr)
    else:
        print("Self-post (no external URL).", file=sys.stderr)

    markdown = build_markdown(hn_data, article_text)

    if args.output_dir:
        out_dir = args.output_dir
    else:
        out_dir = os.path.join(
            os.path.expanduser("~"), ".tweakidea", "hn", f"hn-{item_id}"
        )

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "content.md")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    # Print the absolute path to stdout so the caller knows where to read
    print(os.path.abspath(out_path))


if __name__ == "__main__":
    main()
