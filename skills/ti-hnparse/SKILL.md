---
name: ti-hnparse
description: Python scripts for fetching a single HN post (hnparse.py) and searching HN posts via Algolia (hnsearch.py)
user-invocable: false
---

Contains two standalone Python scripts that talk to the free Algolia Hacker News API:

- `hnparse.py` — fetch one HN post (article + full comment tree) and write structured markdown.
- `hnsearch.py` — search/list HN posts by query and time range; emits JSON to stdout.

## `hnparse.py` usage

```bash
uv run <path-to>/hnparse.py <hn-url-or-id> [-o <output-directory>]
```

- Uses `uv run` inline script metadata for dependencies (playwright, httpx, trafilatura)
- Fetches post metadata and comment tree from Algolia HN API
- Extracts linked article via Playwright headless browser (falls back to plain HTTP)
- Writes `content.md` to the output directory
- Default output: `~/.tweakidea/hn/hn-{item_id}/content.md`
- Prints the absolute path of the output file to stdout (last line)
- All progress messages go to stderr

For better article extraction from JS-heavy sites, run `uv run playwright install chromium` once. Without it, the script falls back to plain HTTP which works fine for most sites.

## `hnsearch.py` usage

```bash
uv run <path-to>/hnsearch.py --query "<freeform>" --days <N> \
  [--tags story|show_hn|ask_hn|front_page|poll] \
  [--min-points N] [--limit N]
```

- Single dependency: `httpx` (no Playwright / trafilatura needed)
- Queries `https://hn.algolia.com/api/v1/search` (popularity-sorted)
- `--query` required; `--days` required (`0` = no time filter / all-time)
- `--tags` defaults to `story` (excludes comments); allowed: `story`, `show_hn`, `ask_hn`, `front_page`, `poll`; multiple tags comma-separated
- `--min-points` defaults to `10`; `--limit` defaults to `20` (max `50`)
- Prints a JSON array of hits to **stdout**. Each hit has: `id`, `title`, `url`, `points`, `num_comments`, `author`, `created_at_i`, `relative_age`, `hn_url`.
- Progress and errors go to **stderr**. Exits non-zero on HTTP failure.
