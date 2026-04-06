---
name: ti-html-report
description: Self-contained HTML report template with CSS styles and generation rules for TweakIdea evaluation reports
user-invocable: false
---

Reference data for generating styled HTML evaluation reports. The orchestrator (`evaluate.md`) uses this skill when HTML_REQUESTED is true to produce `report.html` in the run directory.

---

## Data Extraction Rules

The orchestrator reads FINAL_REPORT (the merger's markdown output) semantically (as structured markdown, not via regex) and extracts:

- **Verdict**: first line -- indicator, label, and weighted score (split on `|`)
- **Dealbreakers**: lines starting with `> DEALBREAKER:` (may be zero)
- **Scorecard rows**: the 14 data rows from the markdown table (after the header row `| Dimension | Score | ...`)
- **Evidence quality**: the `**Evidence Quality:**` line with percentages
- **Assumption impacts**: bullet items under `**Assumption Impact:**` starting with `- *`
- **Strengths**: numbered items under `### Top 3 Strengths`
- **Weaknesses**: numbered items under `### Top 3 Weaknesses`
- **Next steps**: numbered items under `### Next Steps`

Also include IDEA_TEXT as the idea summary section, and if RESEARCH_AVAILABLE is true, include the research brief highlights (Competitors, Market Data, User Evidence sections from RESEARCH_RESULTS).

---

## HTML Template

Generate this EXACT structure, filling in data values only:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TweakIdea Evaluation Report</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      line-height: 1.6; color: #1a1a1a; background-color: #f9fafb; padding: 2rem 1rem;
    }
    .container { max-width: 900px; margin: 0 auto; }
    h1 { font-size: 1.5rem; font-weight: 700; }
    h2 { font-size: 1.15rem; font-weight: 600; margin-bottom: 0.75rem; color: #374151; }

    /* Verdict banner */
    .verdict { padding: 1.25rem 1.5rem; border-radius: 8px; margin-bottom: 1.5rem; }
    .verdict-go { background-color: #dcfce7; border-left: 4px solid #22c55e; }
    .verdict-pivot { background-color: #fef9c3; border-left: 4px solid #eab308; }
    .verdict-stop { background-color: #fee2e2; border-left: 4px solid #ef4444; }
    .verdict-label { font-size: 1.25rem; font-weight: 700; }
    .verdict-score { font-size: 1rem; color: #4b5563; margin-top: 0.25rem; }

    /* Cards */
    .card { background: #fff; border-radius: 8px; padding: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 1rem; }

    /* Dealbreaker */
    .dealbreaker { background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; }
    .dealbreaker-title { color: #dc2626; font-weight: 700; }

    /* Scorecard table */
    .scorecard-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    .scorecard-table th { text-align: left; padding: 0.6rem 0.75rem; border-bottom: 2px solid #e5e7eb; color: #6b7280; font-weight: 600; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.03em; }
    .scorecard-table td { padding: 0.6rem 0.75rem; border-bottom: 1px solid #f3f4f6; vertical-align: middle; }
    .scorecard-table tr:last-child td { border-bottom: none; }

    /* Score badges */
    .score-badge { display: inline-block; width: 2.25rem; height: 2.25rem; line-height: 2.25rem; text-align: center; border-radius: 6px; font-weight: 700; font-size: 0.85rem; color: #1a1a1a; }
    .score-5 { background-color: #22c55e; }
    .score-4 { background-color: #14b8a6; }
    .score-3 { background-color: #eab308; }
    .score-2 { background-color: #f97316; }
    .score-1 { background-color: #ef4444; }

    /* Progress bars */
    .progress-container { background-color: #e5e7eb; border-radius: 9999px; height: 10px; width: 100%; overflow: hidden; display: inline-block; vertical-align: middle; }
    .progress-bar { height: 100%; border-radius: 9999px; }

    /* Evidence tier badges */
    .tier-badge { display: inline-block; padding: 2px 7px; border-radius: 9999px; font-size: 0.7rem; font-weight: 600; margin-right: 3px; }
    .tier-verified { background-color: #22c55e; color: #1a1a1a; }
    .tier-research { background-color: #3b82f6; color: #ffffff; }
    .tier-founder { background-color: #eab308; color: #1a1a1a; }
    .tier-assumed { background-color: #9ca3af; color: #1a1a1a; }

    /* Evidence quality bar */
    .evidence-bar { display: flex; height: 24px; border-radius: 6px; overflow: hidden; margin: 0.5rem 0; font-size: 0.75rem; font-weight: 600; }
    .evidence-bar > div { display: flex; align-items: center; justify-content: center; color: #1a1a1a; min-width: 2rem; }
    .evidence-bar .ev-verified { background-color: #22c55e; }
    .evidence-bar .ev-research { background-color: #3b82f6; color: #fff; }
    .evidence-bar .ev-founder { background-color: #eab308; }
    .evidence-bar .ev-assumed { background-color: #9ca3af; }

    /* Two-column layout */
    .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }

    /* Lists */
    .item-list { list-style: none; padding: 0; }
    .item-list li { padding: 0.5rem 0; border-bottom: 1px solid #f3f4f6; }
    .item-list li:last-child { border-bottom: none; }
    .dim-tag { display: inline-block; background: #e5e7eb; color: #374151; padding: 1px 6px; border-radius: 4px; font-size: 0.75rem; font-weight: 500; }

    /* Header and footer */
    header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid #e5e7eb; }
    footer { text-align: center; color: #9ca3af; font-size: 0.8rem; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; }

    /* Print */
    @media print {
      body { background: #fff; padding: 0; }
      .card { box-shadow: none; border: 1px solid #e5e7eb; }
      .verdict, .score-badge, .tier-badge, .evidence-bar > div, .dealbreaker {
        -webkit-print-color-adjust: exact; print-color-adjust: exact;
      }
      .card, .scorecard-table tr { break-inside: avoid; }
    }
    @media (max-width: 640px) {
      .two-col { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>TweakIdea Evaluation</h1>
      <span style="color:#6b7280;font-size:0.85rem;">{TIMESTAMP}</span>
    </header>

    <!-- VERDICT BANNER: use class verdict-go (>=4.0), verdict-pivot (3.0-3.99), verdict-stop (2.0-2.99 or <2.0) -->
    <div class="verdict {verdict-class}">
      <div class="verdict-label">{verdict indicator} {verdict label}</div>
      <div class="verdict-score">Weighted Score: {X.X}/5.0 | Potential: {Y.Y}/5.0</div>
    </div>

    <!-- DEALBREAKERS: only include this section if dealbreakers exist. One div per dealbreaker. -->
    <div class="dealbreaker">
      <span class="dealbreaker-title">DEALBREAKER: {Dimension Name}</span> scored 1/5 -- {brief explanation}
    </div>

    <!-- IDEA SUMMARY -->
    <div class="card">
      <h2>Idea</h2>
      <p>{IDEA_TEXT -- the full idea as provided by the founder}</p>
    </div>

    <!-- RESEARCH HIGHLIGHTS: only include if RESEARCH_AVAILABLE is true. Omit entire section if false. -->
    <div class="card">
      <h2>Research Highlights</h2>
      <p>{Summarize the key findings from the research brief -- Competitors, Market Data, and User Evidence sections. Keep to 3-5 bullet points or a brief paragraph highlighting the most important data points.}</p>
    </div>

    <!-- SCORECARD TABLE: 14 rows, one per dimension, ordered by weight descending -->
    <div class="card" style="overflow-x:auto;">
      <h2>Scorecard</h2>
      <table class="scorecard-table">
        <thead>
          <tr>
            <th>Dimension</th>
            <th>Score</th>
            <th style="width:120px;"></th>
            <th>Potential</th>
            <th>Evidence</th>
            <th>Key Finding</th>
          </tr>
        </thead>
        <tbody>
          <!-- Repeat for each of 14 dimensions. Score badge uses class score-{N} where N is the integer score (1-5). Progress bar width = score/5 * 100%. Evidence tier badges use the compact notation from the merger. -->
          <tr>
            <td>{Dimension name}</td>
            <td><span class="score-badge score-{N}">{N}</span></td>
            <td><div class="progress-container"><div class="progress-bar score-{N}" style="width:{N*20}%"></div></div></td>
            <td>{potential}/5</td>
            <td>
              <!-- If tier data available: render badge pills. If "(tier data unavailable)": show that text. -->
              <span class="tier-badge tier-verified">{count}V</span>
              <span class="tier-badge tier-research">{count}R</span>
              <span class="tier-badge tier-founder">{count}F</span>
              <span class="tier-badge tier-assumed">{count}A</span>
            </td>
            <td>{Key finding text}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- EVIDENCE QUALITY: stacked percentage bar -->
    <div class="card">
      <h2>Evidence Quality</h2>
      <div class="evidence-bar">
        <div class="ev-verified" style="width:{X}%">{X}% V</div>
        <div class="ev-research" style="width:{Y}%">{Y}% R</div>
        <div class="ev-founder" style="width:{Z}%">{Z}% F</div>
        <div class="ev-assumed" style="width:{W}%">{W}% A</div>
      </div>
      <div style="font-size:0.75rem;color:#6b7280;margin-top:0.25rem;">V=Verified R=Research-Backed F=Founder-Asserted A=Assumed</div>
    </div>

    <!-- ASSUMPTION IMPACT: only include if assumption impact items exist -->
    <div class="card">
      <h2>Assumption Impact</h2>
      <ul class="item-list">
        <li><span class="dim-tag">{Dimension}</span> If {unconfirmed hypothesis} is confirmed, score rises from {X} to {Y} (+{impact} on total)</li>
      </ul>
    </div>

    <!-- STRENGTHS & WEAKNESSES: two-column layout -->
    <div class="two-col">
      <div class="card">
        <h2>Top 3 Strengths</h2>
        <ol>
          <li><strong>{Dimension}</strong> ({X}/5): {Why this is strong}</li>
        </ol>
      </div>
      <div class="card">
        <h2>Top 3 Weaknesses</h2>
        <ol>
          <li><strong>{Dimension}</strong> ({X}/5): {Why this is weak}</li>
        </ol>
      </div>
    </div>

    <!-- NEXT STEPS -->
    <div class="card">
      <h2>Next Steps</h2>
      <ol class="item-list">
        <li>{Concrete validation task} -- <span class="dim-tag">{Dimension}</span> {current}/5 -> {potential}/5 (+{uplift} on total)</li>
      </ol>
    </div>

    <footer>
      Generated by TweakIdea &middot; {TIMESTAMP}
    </footer>
  </div>
</body>
</html>
```

---

## Generation Rules

- Copy the HTML template structure EXACTLY. Do not invent new CSS classes, sections, or layout elements.
- Fill in `{placeholder}` values with actual data extracted from FINAL_REPORT, IDEA_TEXT, and RESEARCH_RESULTS.
- For each of the 14 scorecard rows: use the integer score to select the CSS class (`score-1` through `score-5`) and compute the progress bar width percentage (score * 20).
- For the verdict banner: map the verdict prefix to the CSS class: label starts with "GO" = `verdict-go`, label starts with "PIVOT" = `verdict-pivot`, label starts with "STOP" = `verdict-stop`.
- If zero dealbreakers exist, omit the dealbreaker div(s) entirely.
- If RESEARCH_AVAILABLE is false, omit the "Research Highlights" card entirely.
- If a dimension shows `(tier data unavailable)` in the Evidence column instead of tier counts, render that text plain (no badge pills).
- If a dimension shows `--` in the Evidence column (e.g., Scalability with no compound tags), render "(tier data unavailable)".
- If no assumption impact items exist, omit the "Assumption Impact" card entirely.
- The `{TIMESTAMP}` in the header and footer uses the same TIMESTAMP generated in Stage 6 Step 1.
- All text content must be HTML-escaped (& -> `&amp;`, < -> `&lt;`, > -> `&gt;`) to prevent broken HTML from idea text containing special characters.
