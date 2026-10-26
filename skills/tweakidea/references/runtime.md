# Runtime capabilities

TweakIdea's references describe what they need as **capabilities**, not as tool names, so the skill runs in any Agent Skills-compatible agent. This is the only file that names the tools of a specific agent. At skill setup, map each capability below to the tool your runtime provides, then use those tools wherever a reference names the capability.

A tool counts as available if you can call it now or load it on demand (for example, a deferred tool you can load by name).

## Capability map

| Capability | What it means | Claude Code | Fallback when missing |
|---|---|---|---|
| `ask-user` | Ask the user one question with 2–4 options and wait for one pick | `AskUserQuestion` with one question per call, `multiSelect: false`, and a `header` of at most 12 characters | Ask in chat with numbered options |
| `ask-user-many` | Ask several separate one-pick questions in one pass and wait for all the answers | `AskUserQuestion` with up to 4 questions per call, each `multiSelect: false`; make calls back to back until every question is asked | Ask in chat as one numbered list. Any runtime whose ask tool takes several questions per call has this capability; if unsure, use the fallback |
| `persistent-home` | `~/.tweakidea/` survives between sessions | Available. Also available in other local agents (Codex, Cursor, Droid, Antigravity) | Cloud sandboxes that reset between sessions (such as Manus) lack it; `evaluate` then skips the saved founder profile |
| `spawn-subagent` | Start a subagent with a fresh context, its own instructions, and a chosen model | `Agent` with `subagent_type: general-purpose` and an explicit `model` | `evaluate` stops. Other commands never spawn subagents |
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

Ask the user in only two ways. Never put several items that each need their own answer into one question.

### 1. `ask-user`: one decision, one pick

For a single decision with 2–4 options. References give `question`, an optional `header`, and `options` (each a `label` and an optional `description`).

- Send exactly one question per call, even when the tool accepts more.
- Put everything the user needs to see inside the question text, as plain text with blank lines. In Claude Code, text between tool calls is often hidden, and the question box renders markdown poorly.
- Never add an "Other" option. Free text is always accepted; Claude Code adds "Other" automatically.
- No header field: prefix the question with the header. No description field: append it to the label after a dash.
- More than 4 options, or no ask tool: ask in chat with numbered options.

### 2. Ask in chat: open questions and lists

For open questions (the idea text, a URL) and anything that needs several answers (marking each item in a list, picking many).

- Send one message with the context, the numbered items, and an example reply. End the turn and wait.
- A wake-up that is not the user's reply, such as a background subagent finishing, is not an answer. Keep waiting.
- Accept loose replies (any separators, ranges, mixed case). Apply the reference's default to items the reply does not mention, and re-ask only unclear items (conflicting or out of range).

### 3. `ask-user-many`: several separate one-pick items

For a list where each item gets its own one-pick answer (like yes/no per item), when the runtime has `ask-user-many`. Without it, ask in chat (section 2).

- Each item is its own question with its own options. Never merge items into one multi-select question.
- Put everything the user needs to see inside each question's text. Keep each header at most 12 characters.
- A free-text answer counts as a pick only when it clearly matches one option; otherwise apply the reference's default.
