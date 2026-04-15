---
name: ti-report
description: Jinja2 templates + CSS + data contract for TweakIdea evaluation reports
user-invocable: false
---

Reference files for rendering styled evaluation reports via `scripts/render_report.py`.
Not directly invoked by Claude — consumed by the script layer only.

---

## Files

| File | Purpose |
|------|---------|
| `template.html.j2` | Jinja2 HTML template. Rendered with `autoescape=True` to prevent XSS from idea text / LLM prose. Notion-style layout with sticky topbar, hero stats, dim-grid, collapsible per-dimension detail rows, tabbed research highlights, reach-potential callout, and dark-mode toggle. |
| `template.md.j2` | Jinja2 markdown template. Rendered with `autoescape=False` so raw markdown symbols (`>`, `—`, `|`) pass through unescaped. Mirrors the HTML section order but stays plain-text: lists, headings, tables — no tabs or collapsibles. |
| `styles.css` | All CSS rules extracted from the sample mock verbatim. Read at render time by `render_report.py` and inlined into a `<style>` tag in `report.html` (portable single-file artifact). Uses CSS custom properties for theming; `[data-theme="dark"]` flips the palette. |
| `SKILL.md` | This file. Documents files, rendering contract, and data extraction contract. |

---

## Dual-Environment Rendering Contract

`scripts/render_report.py` builds **two** Jinja2 environments sharing the same `FileSystemLoader`:

```python
from jinja2 import Environment, FileSystemLoader, select_autoescape

loader = FileSystemLoader(str(TI_REPORT_DIR))

html_env = Environment(
    loader=loader,
    autoescape=True,  # force escaping for this env
    trim_blocks=True,
    lstrip_blocks=True,
)

md_env = Environment(
    loader=loader,
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)
```

**Pitfall 2 warning:** Do NOT use `select_autoescape(["html", "htm"])` — `template.html.j2` ends in `.j2` and would not be matched. The `html_env` must use `autoescape=True` directly to guarantee HTML escaping regardless of filename.

The CSS is passed as a template variable `css`:

```python
data["css"] = (TI_REPORT_DIR / "styles.css").read_text()
```

The HTML template inlines it: `<style>{{ css | safe }}</style>`.

**`|safe` is used only for the `css` variable.** The CSS contains `>` combinators (`.rh-tabs > input`), `"` attribute selectors (`[data-panel="user"]`), and `&` characters; without `|safe`, Jinja2's autoescape mangles them into `&gt;` / `&#34;` / `&amp;` and breaks the CSS-only tab switcher plus many other selectors. The CSS comes from a static file on disk loaded by `render_report.py` — it is never user-supplied, so the `|safe` bypass is secure.

All *other* interpolated prose (idea text, narrative fields, assumption text, research text, key findings, score explanations) flows through either autoescape or the `linkify` filter (which escapes first, then wraps URLs). The only raw HTML beyond `css` is the inline SVG icon sprite and theme-toggle script, which are trusted template literals, not data.

---

## Data Contract

Template variables assembled by `render_report.py` from the run artifact family:

| Variable | Source JSON | Schema |
|----------|------------|--------|
| `timestamp` | arg `--timestamp` or `datetime.now()` | string |
| `css` | `skills/ti-report/styles.css` (file, not JSON) | string |
| `idea` | `idea.json` | `schemas/idea.json` |
| `numbers` | `numbers.json` | `schemas/numbers.json` |
| `strengths_weaknesses` | `strengths-weaknesses.json` | `schemas/strengths-weaknesses.json` |
| `next_steps` | `next-steps.json` | `schemas/next-steps.json` |
| `potential` | `potential.json` | `schemas/potential.json` |
| `version` | `version.json` | `schemas/version.json` |
| `hypotheses` | `hypotheses.json` (optional) | `schemas/hypotheses.json` |
| `assumptions` | `assumptions.json` (optional) | `schemas/assumptions.json` |
| `research` | `research.json` (optional) | `schemas/research.json` |
| `dimensions` | `dimensions/*.json` (all 14, keyed by slug) | `schemas/dimension-evaluation.json` |

Key lookups used in templates:

- `idea.codename`, `idea.icon`, `idea.subtitle` — all optional; template renders sensible fallbacks when absent (codename → "Evaluation", icon → 📋, subtitle → `idea.problem`).
- `numbers.rankings[i]` — each entry now carries `weight` (0–1 fraction of registry weight), used to render `{weight*100}%` in the dim-grid and the per-dimension collapsibles.
- `numbers.rankings[i].slug` → key into `dimensions` dict for `dimensions[r.slug].key_finding` and `dimensions[r.slug].score_explanation`.
- `numbers.verdict_bucket` → one of `GO|PIVOT|STOP` — used to select the verdict pill color (`green`, `yellow`, `red`) and the `.verdict-word` class.
- `numbers.verdict_label` → constant string in the form `"BUCKET — descriptor"` (e.g. `"PIVOT — Promising, address weak areas"`). The hero-stats meta line slices off the bucket prefix and renders the descriptor tail next to the styled `.verdict-word`. There is no LLM-authored verdict rationale.
- `numbers.rankings[i].evidence_strength` → `{both_confirmed, research_only, founder_only, assumed, grade}`; `grade` is one of `A+|A|A-|B+|B|B-|C|D|F`.
- `numbers.overall_grade` → single letter grade summarizing evidence strength across all dimensions (same enum as per-dim `grade`). Drives the hero-stats `.grade-big` badge and the properties grid.
- `numbers.evidence_totals` → aggregate tier counts `{both_confirmed, research_only, founder_only, assumed}` summed across all valid dimensions. Drives the hero-stats evidence breakdown bar and its legend counts.
- `numbers.reach_potential_blocks` → per-dimension grouping `{dim, slug, from, to, weighted_uplift, assumption_texts[]}`, sorted by `weighted_uplift` desc. Drives the Reach Potential section.
- `numbers.assumption_impact_math` → `[{assumption_text, dim, score_delta, weighted_uplift}]`. Kept for the markdown fallback and downstream tooling; the HTML template prefers `reach_potential_blocks`.
- `research.available` → boolean gate for the Research Highlights tabs.
- `research.clusters.{user,competitive,market}[i]` → each item is now `{text, source_url?, source_title?}`. Rows with `source_url` render a clickable chip; rows without (pure synthesis) render a grey "synthesis" chip.
- `strengths_weaknesses` — the HTML template renders only the first strength + first weakness as risk callouts; the markdown template matches. Upstream `ti-narrative` still produces top-3 of each, so future designs can show more without a data change.
