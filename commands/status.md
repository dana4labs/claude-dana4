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

Summarise in a few lines: which host is configured, whether an API key is stored, how many tasks are running vs. waiting to be claimed, and any blockers.

Interpreting what comes back:

- `creds` reporting no host or API key means the agent was never enrolled here — point
  the user at `/dana4:enroll`.
- A `401` on `tasks-active` or `tasks-assigned` with a key present means the key was
  rotated or the agent deleted. The owner can issue a new key on the Agents page of the
  Dana4 web app, or the user can enroll again.
- Tasks under `tasks-assigned` are waiting for `/dana4:poll` to claim them. Nothing is
  pushed to a serverless agent, so they will sit there until someone polls.
- The Dana4 UI shows this agent **Online** only while it polls; **Offline** between polls
  is expected and not a fault.
