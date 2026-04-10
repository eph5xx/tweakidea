---
name: ti-hnparse
description: Python script for fetching HN posts (article + comments via Algolia API)
user-invocable: false
---

Contains `hnparse.py` -- a Python script that fetches a Hacker News post (article + all comments) and writes structured markdown.

## Script Usage

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
