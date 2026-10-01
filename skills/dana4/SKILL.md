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

## Chat

```bash
python3 "$CLI" msg-next                          # the agent inbox
python3 "$CLI" msg-fetch --channel ch:1          # a channel's history
python3 "$CLI" msg-send --workspace ws:abc --channel ch:1 --message "Done!"
```

`msg-next` (`POST /chats/take`) is the **agent inbox, not the channel log**,
and it has a blind spot: it only returns chats the server routed to this agent. A message
posted in a channel the agent was never formally added to will never appear there.
When a user says "I tagged the agent on Dana4 but it didn't get it", suspect this first and
poll the channel directly with `msg-fetch --channel`. Messages with `from: null` are
system/automated noise — filter them out.

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
