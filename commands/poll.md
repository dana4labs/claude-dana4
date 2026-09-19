---
description: Claim and run the next Dana4 task assigned to this agent
---

Claim the next Dana4 task and do it. **One bounded pass — do not loop.** If the user wants
continuous polling, they can re-run this command or drive it from `/loop`.

Read `${CLAUDE_PLUGIN_ROOT}/skills/dana4/SKILL.md` for the endpoint details.

1. Claim:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" tasks-take
   ```

   `null` means the queue is empty — say so in one line and stop. Do not retry, and do not
   fall back to `tasks-unassigned` unless the user asks; that endpoint returns tasks
   assigned to other agents.

2. A task comes back as `{"task": ..., "payload": ...}`. The payload has the capability's
   inputs plus `workspace_id`, `task_id` and `channel_id`. Report that you have started:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" task-report \
       --task-id "<task_id>" --status running --progress 0.1 --message "Picked this up"
   ```

3. Do the work in this session. Use the Dana4 CLI for anything that touches the workspace —
   `doc-get`, `doc-create`, `doc-edit`, `search`, `msg-send` — passing the task's
   `task_id` on every document write. Use the repo's own tools for local work.

4. **Always finish with a terminal report**, even when the work failed:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" task-report \
       --task-id "<task_id>" --status completed --progress 1.0 \
       --result-json '{"summary": "…"}'
   ```

   On failure use `--status failed` with a `--message` saying what went wrong. A task with
   no terminal update stays open forever, so do this even if you are interrupted or the
   work is only partly done — report what actually happened rather than claiming success.

Then summarise for the user: what the task asked, what you did, and how you closed it.
