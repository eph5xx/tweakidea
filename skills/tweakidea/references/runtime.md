# Runtime capabilities

TweakIdea's references describe what they need as **capabilities**, not as tool names, so the skill runs in any Agent Skills-compatible agent. This is the only file that names the tools of a specific agent. At skill setup, map each capability below to the tool your runtime provides, then use those tools wherever a reference names the capability.

A tool counts as available if you can call it now or load it on demand (for example, a deferred tool you can load by name).

## Capability map

| Capability | What it means | Claude Code | Fallback when missing |
|---|---|---|---|
| `ask-user` | Ask the user one question with 2–4 options, get one pick (free text always accepted), and wait for the answer | `AskUserQuestion` with exactly one question per call and `multiSelect: false`, a `header` chip of at most 12 characters, and the automatic "Other" option for free text | Ask in chat: print the question with numbered options, end the turn, and wait for the reply (see Asking questions) |
| `spawn-subagent` | Start a subagent with a fresh context, its own instructions, and a chosen model | `Agent` with `subagent_type: general-purpose` and an explicit `model` | `evaluate` stops (see its Stage 0 Step 0). Other commands never spawn subagents |
| `parallel-spawn` | Start several subagents at once and wait for all of them | Issue all `Agent` calls in one message | Spawn them one after another. Each still gets its own fresh context, so results stay independent; the run is just slower |
| `background-spawn` | Start a subagent and keep working while it runs | `Agent` with `run_in_background: true` | Run that subagent to completion first, then continue. In `evaluate`, run the researcher before the extractor and wait for it |
| `web-search` | Search the web | `WebSearch` | `evaluate` stops |
| `web-fetch` | Fetch a web page's content | `WebFetch` | `evaluate` stops |
| `read-file` | Read a file (in chunks for long files) | `Read` | — |
| `write-file` | Create or overwrite a file | `Write` | — |
| `find-files` | List files matching a glob pattern | `Glob` | — |
| `search-text` | Search file contents | `Grep` | — |
| `shell` | Run a shell command | `Bash` | — |

`evaluate` checks `spawn-subagent`, `web-search`, and `web-fetch` for the subagents it spawns. If your runtime gives subagents the same tools as the main session, check the session's tools.

## Model tiers

Subagent specs name a model tier instead of a model.

| Tier | Used for | Claude Code model | Fallback |
|---|---|---|---|
| `fast` | Researcher, extractor, 14 evaluators | `sonnet` | Use the session's model and note it in the run summary |
| `strong` | Narrative synthesis | `opus` | Use the session's model and note it in the run summary |

## Spawn preamble values

`evaluate` fills two placeholders in its subagent preamble:

- `{tools}`: the runtime tool names for the agent's capabilities, comma-separated, in the order listed. In Claude Code, `web-search, web-fetch, read-file, write-file` becomes `WebSearch, WebFetch, Read, Write`.
- `{web_preload}`: in Claude Code, the web tools are deferred and must be loaded before use, so `{web_preload}` is this exact text (including the leading comma): `, and if WebSearch/WebFetch are in your tool list, load them with ToolSearch query "select:WebSearch,WebFetch"`. In other runtimes it is empty.

## Arguments

| | Claude Code | Elsewhere |
|---|---|---|
| Invocation arguments | `$ARGUMENTS` in SKILL.md is replaced with the text after `/tweakidea` | Take the text after the skill name in the user's invoking message |

## Asking questions

References ask the user for input in only two ways. Never put several items that each need their own answer into one question.

### 1. `ask-user`: one decision, one pick

Use it for a single decision with 2–4 options. References describe the question with `question`, an optional `header`, and `options` (each a `label` and an optional `description`). Free text is always accepted as an answer.

- Send exactly one question per call on every runtime, including Claude Code, even when the tool accepts more. Behavior is then the same everywhere.
- Put everything the user needs to see inside the question text. In Claude Code, text written between tool calls is often not shown next to the question box, and the box renders markdown poorly, so use plain text with blank lines.
- Never add an explicit "Other" option. Claude Code adds one automatically; in chat, free text is always accepted.
- If the tool has no header field, drop the header or prefix the question with it. If it has no option description field, append the description to the label after a dash, or leave it out.
- If there are more than 4 options, or the runtime has no ask tool, ask in chat with numbered options instead.

### 2. Ask in chat: open questions and lists

Use it for open questions (no options, such as the idea text or a URL) and for anything that needs several answers (marking each item in a list, or picking many).

- Send one message with the context, the numbered items, and an example reply. Then end the turn and wait for the user's reply.
- A wake-up that is not the user's reply (for example, a background subagent finishing) is not an answer. Do not continue the flow; keep waiting.
- Accept loose replies (any separators, ranges, mixed case). Apply the reference's default to items the reply does not mention, and re-ask only the items that are still unclear (conflicting or out of range).
