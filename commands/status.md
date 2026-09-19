---
description: Show Dana4 connection, tasks, and workspace blockers
---

Report the state of this session's Dana4 agent. Read-only — change nothing.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" creds
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" tasks-active
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" tasks-assigned
```

If the user names a workspace, also run the same script with
`blockers --workspace <workspace_id>`.

Summarise in a few lines: which host and username are configured, whether a password is
stored, how many tasks are running vs. waiting to be claimed, and any blockers.

Interpreting what comes back:

- `creds` reporting no host or username means the agent was never registered here — point
  the user at `/dana4:register`.
- A `401` on `tasks-active` or `tasks-assigned` with credentials present almost always
  means the agent has not been invited into any workspace. Tell the user to invite the
  registered email from the Dana4 web app; do not report it as a broken login.
- Tasks under `tasks-assigned` are waiting for `/dana4:poll` to claim them. Nothing is
  pushed to a serverless agent, so they will sit there until someone polls.
- The Dana4 UI showing this agent as **Offline** is expected and not a fault.
