---
description: Check Dana4 for chat and tasks — messages first, else claim the next task
argument-hint: "[workspace_id] [channel_id]"
---

One bounded pass over Dana4: **messages take priority; only if there are none, claim a task.**
Do not loop — to keep checking, re-run this command or drive it from `/loop`.

Arguments (both optional): `$1` a workspace id, `$2` a channel id to read directly.

Read `${CLAUDE_PLUGIN_ROOT}/skills/dana4/SKILL.md` for the endpoint details.

## 1. Messages first

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" msg-next
```

If the user named a channel, **also** read it, because the inbox is not the channel log:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" msg-fetch \
    --workspace "<workspace_id>" --channel "<channel_id>"
```

`msg-next` only returns chats the server routed to this agent. A message posted in a channel
this agent was never added to will not appear there — the most common cause of "I tagged the
agent and it never answered". If the user reports a missing message and gave no channel,
ask for the workspace and channel id.

Drop messages with `from: null` — system/automated noise, not people. Of the rest, the ones
for you are those that @-mention you, plus every message in a one-to-one DM with you (a
private channel with two owners; `dms --workspace <workspace_id>` lists them). Show the others
only as context.

If real messages remain, **handle them and stop** (skip step 2). **Do not reply on your own
initiative**: show the user the messages and what you propose to say, and send only what
they approve. These are real conversations with real people in a shared workspace.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" msg-send \
    --workspace "<workspace_id>" --channel "<channel_id>" --message "<reply>"
```

If replying is part of a task you claimed, open it with `task-start` and close it with
`task-report` afterwards.

## 2. No messages → take a task

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" tasks-take
```

`null` means the queue is empty too — say "nothing waiting" in one line and stop. Do not
retry, and do not fall back to `tasks-unassigned` unless the user asks; that endpoint
returns tasks assigned to other agents.

A task comes back as `{"task": ..., "payload": ...}`. The payload has the capability's
inputs plus `workspace_id`, `task_id` and `channel_id`. Report that you have started:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" task-report \
    --task-id "<task_id>" --status running --progress 0.1 --message "Picked this up"
```

Do the work in this session. Use the Dana4 CLI for anything that touches the workspace —
`doc-get`, `doc-create`, `doc-edit`, `search`, `msg-send` — passing the task's `task_id` on
every document write. Use the repo's own tools for local work.

**Always finish with a terminal report**, even when the work failed:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" task-report \
    --task-id "<task_id>" --status completed --progress 1.0 \
    --result-json '{"summary": "…"}'
```

On failure use `--status failed` with a `--message` saying what went wrong. A task with no
terminal update stays open forever, so do this even if you are interrupted or the work is
only partly done — report what actually happened rather than claiming success.

Then summarise for the user: what came in, what you did, and how you closed it.
