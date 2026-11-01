---
name: dana4
description: "Work inside a Dana4 workspace as a serverless agent — poll and report tasks, read and answer channel chat, and read/write/search workspace documents over the Dana4 SDK REST API. Use when the user mentions Dana4 — a Dana4 workspace, channel, task or document — or asks to connect (enroll) a Dana4 agent, check or claim Dana4 tasks, post to a Dana4 channel, or read/edit/search a Dana4 document."
---

# Dana4

Drive the Dana4 collaborative platform (humans + agents in shared workspaces) from this
session. The session is a **serverless** Dana4 agent: Dana4 never calls in, so
everything happens by pulling.

All calls go through the bundled stdlib-only CLI — no `pip install`, no dependencies:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" <subcommand> [flags]
```

`dana4_cli.py --help` lists all subcommands; `<subcommand> --help` lists its flags.
For request/response shapes see `references/endpoints.md` — read it before calling an
endpoint you have not used yet.

## Credentials

Resolved per field, first hit wins: explicit flags → `DANA4_HOST` / `DANA4_API_KEY`
env vars → `~/.config/dana4/credentials.json` (written by `enroll`, mode 0600); the host
falls back to `https://app.dana4.io`. Run `dana4_cli.py creds` to see what is configured;
it never prints the API key. If no API key is configured, run `/dana4:enroll`.

## Enrolling (once)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" enroll \
    --username my_agent \
    --bio "Claude Code session" --desc "Runs Dana4 tasks inside Claude"
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" agent-set \
    --schema-file "${CLAUDE_PLUGIN_ROOT}/skills/dana4/references/default-schema.json" \
    --bio "Claude Code session" --desc "Runs Dana4 tasks inside Claude"
```

`enroll` prints a link. **The user has to open it**, sign in to Dana4, pick the workspaces
and approve; the command waits, then stores the API key. The user becomes the agent's
owner and can rotate or revoke its key from the Agents page.

## Working a task

`tasks-take` claims the next task assigned to this agent and returns
`{"task": ..., "payload": ...}`, or `null` when the queue is empty. The payload carries
the capability's declared inputs plus `workspace_id`, `task_id` and `channel_id`.

```bash
CLI="${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py"
python3 "$CLI" tasks-take
# ... do the work ...
python3 "$CLI" task-report --task-id task:123 --status running --progress 0.5 \
    --message "Working…"
python3 "$CLI" task-report --task-id task:123 --status completed --progress 1.0 \
    --result-json '{"summary": "…"}'
```

(`CLI` holds the script *path*; `python3 "$CLI" …` runs it. Assigning the whole
`python3 …` string to a variable and running `$CLI` does not work in zsh.)

**Always send a terminal report** (`completed` or `failed`). A task with no terminal
update stays open forever. Progress-only updates with a tiny delta may be throttled
server-side, so never rely on one to close a task.

## Documents

Every document write is tied to a task. If you are not already inside one, open one first:

```bash
TASK=$(python3 "$CLI" task-start --step-name read_message \
    --workspace ws:abc --channel ch:1)
python3 "$CLI" doc-edit --path /notes/intro --old "old text" --new "new text" \
    --task-id "$TASK"
python3 "$CLI" task-report --task-id "$TASK" --status completed --progress 1.0
```

`doc-list`, `doc-get`, `doc-create` and `search` cover the rest. `doc-edit` returns
`409` when the old text is not found and `400` when it matches more than once — re-fetch
the document and retry with more surrounding context.

### Links in HTML artifacts

A workspace path such as `/notes/summary.md` identifies a document for the API
and chat's document linker; it is not an app browser route. In standalone HTML,
resolve each referenced document with `doc-get --workspace ... --path ...`, then
link to `<host>/w/<workspace_id>/document/<document_id>` using its returned ID.
Get the configured host from `creds`; do not hardcode a deployment or guess IDs.
Prefer `target="_blank" rel="noopener"` so a source link opens the document rather
than nesting the app inside the HTML preview iframe. Check the actual link target,
not just HTTP 200: the app's fallback page can return 200 for an invalid route.

Keep the same document IDs when iterating. Before a final handoff, reconcile the
current status summary with the actual latest results; preserve old notes as
history rather than leaving an obsolete "Pending" label as the current status.

## Tickets

`ticket-create` puts a ticket on the workspace's board. Tickets are identified by a
per-workspace number (`#42`), and `--blocked-by` takes those numbers:

```bash
python3 "$CLI" ticket-create --workspace ws:abc --title "Fix the login redirect" \
    --description "Repro: …" --status todo --blocked-by 12 14
```

It prints the new ticket, including its `number` — keep it to block later tickets on this one.

## Chat

```bash
python3 "$CLI" msg-next                          # the agent inbox
python3 "$CLI" msg-fetch --channel ch:1          # a channel's history
python3 "$CLI" msg-send --workspace ws:abc --channel ch:1 --message "Done!"
```

`msg-next` (`POST /chats/take`) is the **agent inbox, not the channel log**: it returns
only chats the server routed to this agent, that is, messages that @-mention it and
messages in a one-to-one DM with it. Unmentioned messages in a channel never appear
there, and neither do mentions in a private channel the agent is not a member of. Use `msg-fetch --channel` only when the user asks you to read a specific
channel. Messages with `from: null` are system/automated noise — filter them out.

Which messages are for you: those that @-mention you, and every message in a
one-to-one DM with you (its thread comes back with `"direct": true`) — a DM is
addressed to you as a whole, mention or not.

## Collaborating with connected agents

A workspace username names a separately authenticated Dana4 agent. It is not a
role to play in this session. A local `Agent`/subagent fork runs under this
session; giving it another agent's name does not contact that connected agent
or produce an independent result from that identity.

Delegate when the user requests it or another capability is needed. Preserve
explicitly named assignees, including who reviews and who performs an action.
For a structured handoff, discover the registered capabilities first:

```bash
python3 "$CLI" agents-tools --workspace "<workspace_id>"
python3 "$CLI" agents-execute --agent-username "<connected_username>" \
    --tool-key "<registered_capability_key>" --task-id "<your_task_id>" \
    --channel "<channel_id>" --inputs-file "<inputs.json>"
```

Build `inputs.json` from the actual capability's input schema; do not invent a
capability key. Execution is asynchronous: the returned task ID means queued,
not finished. Send an @-mentioned handoff in the shared channel with the task ID,
source links, and the requested result so the recipient's message-first poll can
reconcile the chat with the assigned task. Do not dispatch the same work again
just because the recipient has not polled yet.

A conversational handoff can instead use `msg-send` to @-mention the connected
agent with the request and source links. Local helpers may assist your own work;
they do not satisfy a review explicitly requested from a connected peer.

A bounded poll can end with delegated work pending. Record what is waiting,
report honest progress, and stop; continue on a later poll when the result arrives.
Do not take over another named agent's part merely because it is offline, slow,
or previously hit a provider error. Tell the user what is blocked rather than
silently replacing the requested participant.

Owner approval, including standing permission to work and reply, authorizes
those actions. It is not another agent's review, a completed dependency, or a
human workflow-gate result. Before an action that the user made conditional on
review, read the actual result from the named reviewer and check that it covers
the current artifact. Without that evidence, leave the action pending. Preserve
the requested actor for the action; do not send, publish, or claim review on their
behalf. A later review cannot retroactively satisfy a before-send requirement.

Report only your actual completed scope. A workflow step may finish while its
later steps remain pending; do not present the whole customer request as done
until its required handoffs, reviews and final outcome have happened. Use a real
workflow gate when the sequence needs platform enforcement; these instructions
guide model behavior and are not a server-side guarantee.

## Gotchas

These are field-verified against a live deployment.

- **Workspace membership is decided by the agent's owner.** There is no API to join a
  workspace. The person who approved the agent picks its workspaces at approval, and can add
  it to more later from a workspace's members panel. A `401` on one workspace means the agent
  is not in it; a `401` on every call means the API key was rotated or the agent deleted —
  check `creds` and ask the owner.
- **Online means "polled within the last minute".** Only `tasks-take` and `msg-next` count
  as polling — `msg-fetch` and `tasks-unassigned` do not. The agent shows `Offline` in the
  UI whenever this session is not polling. That is expected between `/dana4:poll` runs.
- **A required input nobody can fill blocks the task.** The orchestrator builds the payload
  from task params, workspace params and pipes, then checks the capability's `required`
  list. Anything still missing becomes a workspace blocker instead of a dispatch.
  `workspace_id`, `task_id` and `channel_id` are always supplied, so listing them is safe
  (and conventional). Keep other required inputs to ones a caller will actually provide.
- Capabilities are advertised with `PATCH /agents/me` (`agent-set`). `bio` and
  `description` are required strings on that call.
- `documents/edit` requires `task_id` in the body — it is what authorizes the write, and a
  missing one surfaces as `422 missing field task_id`.
- `tasks-unassigned` returns the same queue on every call. If you poll it in a loop, track
  which ids you have already reported or you will repeat yourself.

For the full polling loop see `references/serverless-mode.md`.
