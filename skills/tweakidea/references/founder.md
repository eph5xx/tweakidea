Reference data for all founder profile operations. The orchestrator (`evaluate.md`) uses this reference to create, read, and update `FOUNDER.md` at `~/.tweakidea/FOUNDER.md`.

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

Ask in chat: the preamble, then these 5 questions as a numbered list.

| # | Question | Maps to Section |
|---|----------|-----------------|
| 1 | "What's your professional background? (Industry experience, roles, education)" | Relevant Experience |
| 2 | "What domains do you have deep expertise in?" | Expertise & Domain Knowledge |
| 3 | "What relevant network or resources do you have? (Connections, advisors, potential early customers, capital access)" | Network & Market Access |
| 4 | "What can you or your team build? (Technical strengths, capabilities)" | Build Capabilities |
| 5 | "What drives you to work on hard problems? (Personal motivation, what keeps you going)" | Drive & Commitment |

Preamble: "I don't have a founder profile yet. I'll ask a few quick questions to understand your background -- this helps evaluate founder-market fit and only needs to happen once."

If during the questioning flow the user volunteers additional relevant information beyond what was asked, capture it in the appropriate section. Do not add new sections.

---

## Fit Question Guidance

After profile creation/load, ask 2-4 questions about the founder's connection to THIS specific idea. These questions serve a dual purpose: surface persistent founder attributes while assessing idea-specific fit.

### Design Principle

Each question must simultaneously:
1. Surface a **persistent founder attribute** (expertise, experience, network, capability) that would appear in FOUNDER.md
2. Assess **idea-specific fit** by anchoring that attribute to the current idea domain

Do NOT write questions that are purely idea-specific ("How big is this market?") or purely background ("What's your experience?"). The profile creation questions already captured generic background. Fit questions contextualize those attributes to this idea.

### Focus

Founder-idea fit exclusively -- NOT generic idea questions. Do not ask about target customers, market size, competitors, or other idea details already present in the idea text.

### Dynamic Generation

Questions must be generated based on:
- The idea domain (what industry/problem space is described)
- What FOUNDER.md already covers -- do NOT re-ask what is already known
- Gaps in understanding the founder-idea connection that would help evaluate founder-market fit

### Example Dual-Purpose Patterns

Adapt to the specific idea -- do not use these verbatim if they don't fit:
- "What experience or expertise gives you an edge in [the idea's specific domain]?" -- surfaces expertise (persistent) + idea relevance
- "Have you personally experienced [the specific problem], and what was your situation?" -- surfaces personal connection (persistent) + idea validation
- "Do you have existing relationships with [target segment], and how strong is that access?" -- surfaces network (persistent) + idea-specific channel
- "What have you already built or shipped that's relevant to [this problem area]?" -- surfaces build capability (persistent) + idea relevance

### Presentation

Ask in chat with this message, without answer options:

```
A few questions about how your background fits this idea. Answer in one reply, numbered to match:

1. [fit question]
2. [fit question]

Short answers are fine. Skip any that don't apply.
```

A skipped question gets the answer "(no answer)".

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

If no answers qualify, skip this. Otherwise ask in chat:

```
Some of your answers could be saved to your founder profile for future runs:

1. [summary] -> [Section name]
2. [summary] -> [Section name]

Reply with the numbers to save (like "1, 3"), or "none".
```

Append each picked item to its section in FOUNDER.md (never replace) and update the "Last updated" date in the footer.

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
