---
description: Check Dana4 for chat and tasks — messages first, else claim the next task
---

One bounded pass over Dana4: **messages take priority; only if there are none, claim a task.**
Do not loop — to keep checking, re-run this command or drive it from `/loop`.

Read `${CLAUDE_PLUGIN_ROOT}/skills/dana4/SKILL.md` for the endpoint details.

Before declaring that nothing is waiting, check `tasks-active` for your running
work in this conversation. A fresh session can find a chat task that paused after
performing its work. Reconcile only a task whose channel and request match that work:
verify the actual stored result or receipt, finish that same task if its own work
is complete, or keep an honest pending status if it is not. Do not open a replacement
task, repeat a recorded side effect, or clean up unrelated work from another channel.
An already-answered message alone does not mean its active task was closed.

## 1. Messages first

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" msg-next
```

Drop messages with `from: null` — system/automated noise, not people. Of the rest, the ones
for you are those that @-mention you, plus every message in a one-to-one DM with you (its
thread comes back with `"direct": true`). Show the others only as context.

If real messages remain, **handle them and stop** (skip step 2). These are real conversations with real people in a shared workspace.
Honor permission the owner has already granted for this request, including explicit
standing permission limited to this workspace. Within that scope, perform the work and
send the authorized replies without asking for the same approval again. If a reply or
action has not been authorized, or exceeds that permission, propose it and ask before
acting. Do not send unsolicited replies outside the grant.

Permission to act is separate from evidence that a prerequisite happened. It never
stands in for a requested peer review, an explicit human workflow gate, or authority
for an external action beyond the user's request. Keep those prerequisites pending
until their actual results arrive.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" msg-send \
    --workspace "<workspace_id>" --channel "<channel_id>" --message "<reply>"
```

A chat reply needs no task. If replying is part of a task you claimed, report on that task
with `task-report` afterwards.

## 2. No messages → take a task

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" tasks-take
```

`null` means the queue is empty too — say "nothing waiting" in one line and stop. Do not
retry, and do not fall back to `tasks-unassigned` unless the user asks; that endpoint
lists tasks nobody has been assigned yet, and claiming one is the user's call.

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
