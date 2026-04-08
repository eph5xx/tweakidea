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
      font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      line-height: 1.65; color: #1a1a2e; background-color: #f8f9fc; padding: 2.5rem 1.5rem;
      letter-spacing: -0.01em;
    }
    .container { max-width: 940px; margin: 0 auto; }
    h1 { font-size: 1.6rem; font-weight: 800; letter-spacing: -0.02em; color: #111827; }
    h2 { font-size: 1.2rem; font-weight: 700; margin-bottom: 0.85rem; color: #1f2937; letter-spacing: -0.01em; }

    /* Verdict banner */
    .verdict { padding: 1.5rem 1.75rem; border-radius: 10px; margin-bottom: 1.75rem; }
    .verdict-go { background-color: #dcfce7; border-left: 4px solid #22c55e; }
    .verdict-pivot { background-color: #fef9c3; border-left: 4px solid #eab308; }
    .verdict-stop { background-color: #fee2e2; border-left: 4px solid #ef4444; }
    .verdict-label { font-size: 1.25rem; font-weight: 700; }
    .verdict-score { font-size: 1rem; color: #4b5563; margin-top: 0.25rem; }

    /* Cards */
    .card { background: #fff; border-radius: 10px; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06); margin-bottom: 1.25rem; }

    /* Dealbreaker */
    .dealbreaker { background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1rem; }
    .dealbreaker-title { color: #dc2626; font-weight: 700; }

    /* Scorecard table */
    .scorecard-table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
    .scorecard-table th { text-align: left; padding: 0.65rem 0.75rem; border-bottom: 2px solid #d1d5db; color: #6b7280; font-weight: 700; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; }
    .scorecard-table td { padding: 0.65rem 0.75rem; border-bottom: 1px solid #f3f4f6; vertical-align: middle; }
    .scorecard-table tr:last-child td { border-bottom: none; }

    /* Score explanation (below each scorecard row) */
    .score-explanation td {
      padding: 0.25rem 0.75rem 0.75rem 0.75rem;
      border-bottom: 1px solid #e5e7eb;
      font-size: 0.85rem;
      color: #4b5563;
      line-height: 1.55;
      font-style: italic;
    }

    /* Radar chart */
    .radar-chart { text-align: center; padding: 1rem 0; }
    .radar-chart svg { max-width: 100%; height: auto; }

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
    header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; padding-bottom: 1.25rem; border-bottom: 2px solid #e5e7eb; }
    footer { text-align: center; color: #9ca3af; font-size: 0.78rem; margin-top: 2.5rem; padding-top: 1.25rem; border-top: 2px solid #e5e7eb; }

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

    <!-- RADAR CHART: inline SVG showing 14 dimension scores -->
    <div class="card">
      <h2>Dimension Overview</h2>
      <div class="radar-chart">
        <svg viewBox="0 0 500 440" xmlns="http://www.w3.org/2000/svg">
          <!-- Grid: 5 concentric polygons at r=30,60,90,120,150 from center (250,210) -->
          <!-- Computed via: for each level L (1-5), for each dim i (0-13): angle = i*(360/14)-90 deg, x = 250 + L*30*cos(angle_rad), y = 210 + L*30*sin(angle_rad) -->
          <g class="grid" stroke="#e5e7eb" fill="none" stroke-width="1">
            <polygon points="250.0,180.0 263.0,183.0 273.5,191.3 279.2,203.3 279.2,216.7 273.5,228.7 263.0,237.0 250.0,240.0 237.0,237.0 226.5,228.7 220.8,216.7 220.8,203.3 226.5,191.3 237.0,183.0"/>
            <polygon points="250.0,150.0 276.0,155.9 296.9,172.6 308.5,196.6 308.5,223.4 296.9,247.4 276.0,264.1 250.0,270.0 224.0,264.1 203.1,247.4 191.5,223.4 191.5,196.6 203.1,172.6 224.0,155.9"/>
            <polygon points="250.0,120.0 289.0,128.9 320.4,153.9 337.7,190.0 337.7,230.0 320.4,266.1 289.0,291.1 250.0,300.0 211.0,291.1 179.6,266.1 162.3,230.0 162.3,190.0 179.6,153.9 211.0,128.9"/>
            <polygon points="250.0,90.0 302.1,101.9 343.8,135.2 367.0,183.3 367.0,236.7 343.8,284.8 302.1,318.1 250.0,330.0 197.9,318.1 156.2,284.8 133.0,236.7 133.0,183.3 156.2,135.2 197.9,101.9"/>
            <polygon points="250.0,60.0 315.1,74.9 367.3,116.5 396.2,176.6 396.2,243.4 367.3,303.5 315.1,345.1 250.0,360.0 184.9,345.1 132.7,303.5 103.8,243.4 103.8,176.6 132.7,116.5 184.9,74.9"/>
          </g>

          <!-- Spoke lines from center (250,210) to outer grid for each dimension -->
          <g class="spokes" stroke="#e5e7eb" stroke-width="0.5">
            <line x1="250" y1="210" x2="250.0" y2="60.0"/>
            <line x1="250" y1="210" x2="315.1" y2="74.9"/>
            <line x1="250" y1="210" x2="367.3" y2="116.5"/>
            <line x1="250" y1="210" x2="396.2" y2="176.6"/>
            <line x1="250" y1="210" x2="396.2" y2="243.4"/>
            <line x1="250" y1="210" x2="367.3" y2="303.5"/>
            <line x1="250" y1="210" x2="315.1" y2="345.1"/>
            <line x1="250" y1="210" x2="250.0" y2="360.0"/>
            <line x1="250" y1="210" x2="184.9" y2="345.1"/>
            <line x1="250" y1="210" x2="132.7" y2="303.5"/>
            <line x1="250" y1="210" x2="103.8" y2="243.4"/>
            <line x1="250" y1="210" x2="103.8" y2="176.6"/>
            <line x1="250" y1="210" x2="132.7" y2="116.5"/>
            <line x1="250" y1="210" x2="184.9" y2="74.9"/>
          </g>

          <!-- Score polygon: filled area showing actual scores -->
          <!-- For each dim i (0-13): angle = i*(360/14)-90 deg, score_r = (score/5)*150, x = 250 + score_r*cos(angle_rad), y = 210 + score_r*sin(angle_rad) -->
          <!-- Dimension order: 0=Pain Intensity, 1=Willingness to Pay, 2=Solution Gap, 3=Founder-Market Fit, 4=Urgency, 5=Frequency, 6=Market Size, 7=Defensibility, 8=Market Growth, 9=Scalability, 10=Clarity of Target Customer, 11=Behavior Change Required, 12=Mandatory Nature, 13=Incumbent Indifference -->
          <polygon points="{x_0},{y_0} {x_1},{y_1} {x_2},{y_2} {x_3},{y_3} {x_4},{y_4} {x_5},{y_5} {x_6},{y_6} {x_7},{y_7} {x_8},{y_8} {x_9},{y_9} {x_10},{y_10} {x_11},{y_11} {x_12},{y_12} {x_13},{y_13}" fill="rgba(59,130,246,0.2)" stroke="#3b82f6" stroke-width="2"/>

          <!-- Dimension labels at radius 175 from center -->
          <g class="labels" font-size="9" fill="#4b5563" font-family="system-ui, sans-serif">
            <text x="250.0" y="35.0" text-anchor="middle" dy="0.35em">Pain Intensity</text>
            <text x="325.9" y="52.3" text-anchor="middle" dy="0.35em">Willingness to Pay</text>
            <text x="386.8" y="100.9" text-anchor="start" dy="0.35em">Solution Gap</text>
            <text x="420.6" y="171.1" text-anchor="start" dy="0.35em">Founder Fit</text>
            <text x="420.6" y="248.9" text-anchor="start" dy="0.35em">Urgency</text>
            <text x="386.8" y="319.1" text-anchor="start" dy="0.35em">Frequency</text>
            <text x="325.9" y="367.7" text-anchor="middle" dy="0.35em">Market Size</text>
            <text x="250.0" y="385.0" text-anchor="middle" dy="0.35em">Defensibility</text>
            <text x="174.1" y="367.7" text-anchor="middle" dy="0.35em">Market Growth</text>
            <text x="113.2" y="319.1" text-anchor="end" dy="0.35em">Scalability</text>
            <text x="79.4" y="248.9" text-anchor="end" dy="0.35em">Target Customer</text>
            <text x="79.4" y="171.1" text-anchor="end" dy="0.35em">Behavior Change</text>
            <text x="113.2" y="100.9" text-anchor="end" dy="0.35em">Mandatory Nature</text>
            <text x="174.1" y="52.3" text-anchor="middle" dy="0.35em">Incumbent</text>
          </g>

          <!-- Score value dots at each polygon vertex -->
          <g class="dots" fill="#3b82f6">
            <circle cx="{x_0}" cy="{y_0}" r="4"/>
            <circle cx="{x_1}" cy="{y_1}" r="4"/>
            <circle cx="{x_2}" cy="{y_2}" r="4"/>
            <circle cx="{x_3}" cy="{y_3}" r="4"/>
            <circle cx="{x_4}" cy="{y_4}" r="4"/>
            <circle cx="{x_5}" cy="{y_5}" r="4"/>
            <circle cx="{x_6}" cy="{y_6}" r="4"/>
            <circle cx="{x_7}" cy="{y_7}" r="4"/>
            <circle cx="{x_8}" cy="{y_8}" r="4"/>
            <circle cx="{x_9}" cy="{y_9}" r="4"/>
            <circle cx="{x_10}" cy="{y_10}" r="4"/>
            <circle cx="{x_11}" cy="{y_11}" r="4"/>
            <circle cx="{x_12}" cy="{y_12}" r="4"/>
            <circle cx="{x_13}" cy="{y_13}" r="4"/>
          </g>
        </svg>
      </div>
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
          <!-- Repeat for each of 14 dimensions. Score badge uses class score-{N} where N is the integer score (1-5). Progress bar width = score/5 * 100%. Evidence tier badges use the compact notation from the merger. After each dimension row, include a score-explanation row. -->
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
          <tr class="score-explanation">
            <td colspan="6">{2-3 sentence score explanation from merger blockquote}</td>
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
- For each scorecard dimension, extract the blockquote explanation line (starting with `>`) that follows the table row in FINAL_REPORT. Strip the `>` prefix and the bold dimension name prefix (e.g., `> **Pain Intensity:** ` becomes just the explanation text). Place the stripped text in the `<tr class="score-explanation">` row's `<td colspan="6">`.
- **Radar chart generation:** Compute SVG coordinates using the formula: center=(250,210), max_radius=150. For dimension index i (0-based, 0 through 13), angle_i = i * (360/14) - 90 degrees (so index 0 = Pain Intensity starts at top). Convert to radians: radian_i = angle_i * PI / 180. Score vertex: x = 250 + (score/5)*150*cos(radian_i), y = 210 + (score/5)*150*sin(radian_i). Grid polygon vertices use the same angles but with fixed radii (30, 60, 90, 120, 150). Dimension labels use radius 175. Use the Dimension Registry index order (01 through 14) for consistent spoke ordering. Abbreviate long dimension names: "Founder Fit" for "Founder-Market Fit", "Target Customer" for "Clarity of Target Customer", "Behavior Change" for "Behavior Change Required", "Incumbent" for "Incumbent Indifference".
- **Radar chart label positioning:** For labels at angles -45 to 45 degrees (right side), use text-anchor="start". For 135 to 225 degrees (left side), use text-anchor="end". For all others (top and bottom), use text-anchor="middle". Apply a dy="0.35em" baseline shift for vertical centering.
