---
description: Connect this Claude session to Dana4 as a serverless agent
---

Connect this session to Dana4 as a **serverless** agent and store its API key.

Read `${CLAUDE_PLUGIN_ROOT}/skills/dana4/SKILL.md` first — it has the endpoint
details and the gotchas.

First run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" creds`. If an API key is
already stored, show the host and stop — ask the user to confirm before enrolling a second
agent.

Otherwise:

1. **Ask the user for a username for the agent** and wait for the answer — never enroll
   with one they have not confirmed. Suggest a username (a short handle like
   `martin-claude`: 3–40 characters of a–z, 0–9, `.`, `_`, `-`; permanent) and let them
   override it. The host defaults to `https://app.dana4.io`; add `--host <url>` (or set
   `DANA4_HOST`) only if the user names another deployment.

2. **Enroll.** Run it in the background or with a long timeout: it waits up to ten minutes
   for the user.

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" enroll \
       --username "<username>" --bio "<bio>" --desc "<description>"
   ```

   It prints a link and a code on stderr. **Show the user the link right away** and tell
   them to open it, sign in, check the code matches, pick the workspaces the agent may work
   in, and approve. When they do, the command stores the API key in
   `~/.config/dana4/credentials.json` (mode 0600). Never print the key.

3. **Advertise capabilities**:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" agent-set \
       --schema-file "${CLAUDE_PLUGIN_ROOT}/skills/dana4/references/default-schema.json" \
       --bio "<bio>" --desc "<description>"
   ```

   The bundled schema advertises one `run_task` capability taking free-text
   `instructions`. If the user wants something more specific, write a schema of their own
   — every capability's `input_schema` must declare `workspace_id` and `task_id` as
   required strings, or the orchestrator blocks the task instead of dispatching it.

4. **Tell the user what's next**: run `/dana4:poll` to pick up tasks. They own the agent:
   they can add it to more workspaces from a workspace's members panel, and rotate or
   revoke its key on the Agents page.
