---
name: dana4
description: "Work inside a Dana4 workspace as a serverless agent — poll and report tasks, read and answer channel chat, and read/write/search workspace documents over the Dana4 SDK REST API. Use when the user mentions Dana4 — a Dana4 workspace, channel, task or document — or asks to register a Dana4 agent, check or claim Dana4 tasks, post to a Dana4 channel, or read/edit/search a Dana4 document."
---

# Dana4

Drive the Dana4 collaborative platform (humans + agents in shared workspaces) from this
session. The session is registered as a **serverless** agent: Dana4 never calls in, so
everything happens by pulling.

All calls go through the bundled stdlib-only CLI — no `pip install`, no dependencies:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" <subcommand> [flags]
```

`dana4_cli.py --help` lists all subcommands; `<subcommand> --help` lists its flags.
For request/response shapes see `references/endpoints.md` — read it before calling an
endpoint you have not used yet.

## Credentials

Resolved per field, first hit wins: explicit flags → `DANA4_HOST` / `DANA4_USERNAME` /
`DANA4_PASSWORD` env vars → `~/.config/dana4/credentials.json` (written by `register`,
mode 0600). Run `dana4_cli.py creds` to see what is configured; it never prints the
password. If nothing is configured, run `/dana4:register` — do not guess a host.

## Registering (once)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" register \
    --host https://app.dana4.example \
    --username my_agent --password '<generated>' --email you@example.com \
    --bio "Claude Code session" --desc "Runs Dana4 tasks inside Claude"
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" agent-set \
    --schema-file "${CLAUDE_PLUGIN_ROOT}/skills/dana4/references/default-schema.json" \
    --bio "Claude Code session" --desc "Runs Dana4 tasks inside Claude"
```

Omitting `--url` sends `url: null`, which is what makes the agent serverless.

**Ask the user for the email. Never infer one** — not from git config, not from an
OpenAPI `info.contact` block, not from anything else. The email is write-only and can
only be set at register time; a re-register does **not** change it, and fixing a wrong
one means deleting the agent record server-side. It is also the identity a human uses to
invite the agent into a workspace, so a wrong address means the agent can never be
invited.

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

These are field-verified against a live deployment; the OpenAPI spec is wrong about
several of them.

- **Workspace membership is required and cannot be self-served.** There is no API to join
  a workspace. A human invites the agent by **email** from the Dana4 web app. Until then
  every workspace-scoped call returns `401`. A `401` on a workspace you expected to have
  is almost always a missing invite, not bad credentials — check `creds` and then ask the
  user to invite the email.
- **Serverless agents always show `Offline` in the UI.** The orchestrator marks any agent
  with no `url` offline because there is no health endpoint to ping. This is by design and
  does not stop task polling. Do not "fix" it.
- **Nothing is pushed.** Tasks are assigned and then sit until `tasks-take` claims them;
  chat notifications are skipped entirely for serverless agents. Polling is the only path.
- **Capability input schemas must declare `workspace_id` and `task_id` as required
  strings.** The orchestrator validates the assembled payload against the schema and turns
  a missing required property into a workspace blocker instead of dispatching the task.
- Capabilities are advertised with `PATCH /agents/me` (`agent-set`). `bio` and
  `description` are required strings on that call.
- `documents/edit` requires `task_id` in the body — it is what authorizes the write, and a
  missing one surfaces as `422 missing field task_id`.
- `tasks-unassigned` returns the same queue on every call. If you poll it in a loop, track
  which ids you have already reported or you will repeat yourself.

## Scope

Serverless (polling) only. Server mode — where Dana4 pushes to a webhook you host — needs a
publicly reachable HTTPS endpoint and is out of scope for a Claude session; see
`references/serverless-mode.md` for the mode this plugin implements.
