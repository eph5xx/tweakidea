---
name: ti-founder
description: Founder profile template, creation questions, section definitions, and fit question guidance for TweakIdea evaluations
user-invocable: false
---

Reference data for all founder profile operations. The orchestrator (`evaluate.md`) uses this skill to create, read, and update `FOUNDER.md` at `~/.tweakidea/FOUNDER.md`.

---

## FOUNDER.md Template

```
# Founder Profile

## Expertise & Domain Knowledge
- Domain: [domain/industry]
- Depth: [depth/level]
- Insight: [unique perspective]

## Relevant Experience
- Role: [most relevant role]
- Achievement: [relevant accomplishment]
- Duration: [time in space]

## Network & Market Access
- Connections: [network]
- Channel: [customer access]
- Capital: [resources/funding]

## Build Capabilities
- Technical: [build capability]
- Team: [team composition]
- Speed: [shipping ability]

## Drive & Commitment
- Motivation: [why this problem]
- Experience: [personal connection]
- Commitment: [commitment level]

---
*Created: [date] | Last updated: [date]*
```

### Template Rules

- Field names (Domain, Depth, Insight, etc.) are starter suggestions. Use whatever tagged entries naturally emerge from the founder's answers.
- Not every section needs all suggested fields -- some may have 1 entry, some may have 5.
- Keep FOUNDER.md under 100 lines (context budget).
- Do NOT add new sections beyond the 5 defined above. Fit additional information into the most relevant existing section as tagged list entries (e.g., `- Key: Value`).

---

## Profile Creation Questions

Ask these 5 questions one at a time using AskUserQuestion, waiting for each answer before proceeding to the next:

| # | Question | Maps to Section |
|---|----------|-----------------|
| 1 | "What's your professional background? (Industry experience, roles, education)" | Relevant Experience |
| 2 | "What domains do you have deep expertise in?" | Expertise & Domain Knowledge |
| 3 | "What relevant network or resources do you have? (Connections, advisors, potential early customers, capital access)" | Network & Market Access |
| 4 | "What can you or your team build? (Technical strengths, capabilities)" | Build Capabilities |
| 5 | "What drives your passion for this problem space? (Personal connection, motivation)" | Drive & Commitment |

Preamble before asking: "I don't have a founder profile yet. I'll ask a few quick questions to understand your background -- this helps evaluate founder-market fit and only needs to happen once."

If during the questioning flow the user volunteers additional relevant information beyond what was asked, capture it in the appropriate section. Do not add new sections.

---

## Fit Question Guidance

After profile creation/load and hypothesis confirmation, ask 2-4 questions about the founder's connection to THIS specific idea.

### Focus

Founder-idea fit exclusively -- NOT generic idea questions. Do not ask about target customers, market size, competitors, or other idea details already present in the idea text.

### Dynamic Generation

Questions must be generated based on:
- The idea domain (what industry/problem space is described)
- What FOUNDER.md already covers -- do NOT re-ask what is already known
- Gaps in understanding the founder-idea connection that would help evaluate founder-market fit

### Example Question Areas

Adapt to the specific idea -- do not use these verbatim if they don't fit:
- "What personal experience do you have with [the specific problem]?"
- "Do you have existing relationships with [the target customer segment]?"
- "What domain-specific knowledge gives you an edge in [the idea's space]?"
- "How long have you been thinking about this problem, and what triggered your interest?"

### Presentation

1. Preview all questions upfront: "I have {N} questions about your connection to this idea:" followed by a numbered list
2. Ask each question one at a time using AskUserQuestion, waiting for each response
3. Use single-select options where appropriate (e.g., "Direct experience" / "Observed it" / "Researched it" / "Other") or allow free-text

### Storage

Store all question-answer pairs as FOUNDER_FIT_ANSWERS:
```
Q: [question text]
A: [founder's answer]
```

Always ask fit questions even when FOUNDER.md already exists (returning user). The session covers founder-market fit for the current idea.

---

## Profile Update Rules

After fit Q&A, review answers for NEW persistent attributes about the founder -- information about background, expertise, network, capabilities, or motivation relevant across multiple evaluation runs.

### What qualifies as persistent

- Background, expertise, network, capabilities, motivation details
- NOT idea-specific observations (e.g., "I think this market is growing")

### Update mechanics

1. Present relevant answers to the founder using AskUserQuestion with multiSelect
2. Each option shows a summary and which FOUNDER.md section it would update
3. Follow AskUserQuestion 2-4 option limit; chunk if more than 4 qualify
4. If founder selects answers to persist: read current FOUNDER.md, **append** to relevant section (never replace), write updated file
5. Update the "Last updated" date in the footer
6. If founder selects nothing or no answers qualify, skip entirely

### Old-Format Section Name Mapping

If an existing FOUNDER.md uses old-format section headers, map them:

| Old Section Name | New Section Name |
|---|---|
| Background | Relevant Experience |
| Domain Expertise | Expertise & Domain Knowledge |
| Network & Resources | Network & Market Access |
| Technical Capabilities | Build Capabilities |
| Passion & Motivation | Drive & Commitment |

If headers are unrecognized, try keyword proximity matching. If completely unparseable, display raw content to the user with a warning.

---

## Section Picker Flow

For standalone profile editing (outside of an evaluation run), use a two-call section picker:

### First AskUserQuestion call (multiSelect: true)

Question: "Which sections of your founder profile would you like to update?"

Options (4 items):
1. label: "No changes needed", description: "Looks good — exit without editing"
2. label: "Expertise & Domain Knowledge", description: "Your domain expertise, industry knowledge, and unique insights"
3. label: "Relevant Experience", description: "Professional background, roles, and achievements"
4. label: "Network & Market Access", description: "Connections, customer access, and resources"

If "No changes needed" is selected: exit without editing.

### Second AskUserQuestion call (multiSelect: true)

Question: "Any other sections to update?"

Options (2 items):
1. label: "Build Capabilities", description: "Technical skills, team, and ability to ship"
2. label: "Drive & Commitment", description: "Motivation, personal connection, and commitment level"

### Conversational Editing

For each selected section, in selection order:
1. Show current entries from that section (or "This section is currently empty" if new)
2. Ask: "Here are your current entries for [section name]. What would you like to add, change, or remove?"
3. Process response conversationally -- add, change, or remove tagged list entries using natural language understanding

After all sections processed, write updated FOUNDER.md and update the "Last updated" date.
