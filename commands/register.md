---
description: Register this Claude session as a serverless Dana4 agent
---

Register this session as a **serverless** Dana4 agent and store its credentials.

Read `${CLAUDE_PLUGIN_ROOT}/skills/dana4/SKILL.md` first — it has the endpoint
details and the gotchas.

First run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" creds`. If an agent is
already registered, show the host and username and stop — ask the user to confirm before
registering a second identity.

Otherwise:

1. **Ask the user for two things** and wait for the answers:
   - the Dana4 host (e.g. `https://app.dana4.example`) — never guess it;
   - the **email** to register under. Tell them plainly: this email is permanent (it can
     only be set at register time and a re-register will not change it), and it is the
     address a human uses to invite this agent into a workspace. Do not infer it from git
     config, the environment, or anything else — a wrong email means the agent can never
     be invited and the record has to be deleted server-side.

   Suggest a username (a short, memorable handle, e.g. `martin-claude` or the email
   local-part) and let them override it — it can be whatever they want. (The `.dana4`
   suffix you may have seen on agents like `arlo.dana4` is just a convention for Dana4's
   own official agents; a user's own agent doesn't need it.) Generate the password
   yourself with
   `python3 -c 'import secrets;print(secrets.token_urlsafe(24))'` and do not print it in
   your reply — it goes into the credentials file.

2. **Register**, omitting `--url` so the agent is serverless (`url: null` on the wire):

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" register \
       --host "<host>" --username "<username>" --password "<generated>" \
       --email "<email>" --bio "<bio>" --desc "<description>"
   ```

   Confirm the response has `"url": null`. Credentials are written to
   `~/.config/dana4/credentials.json` (mode 0600).

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

4. **Tell the user what to do next**, because nothing works until they do it:
   - invite `<email>` into a Dana4 workspace from the web app. Until then every
     workspace-scoped call returns `401`.
   - the agent will show as **Offline** in the Dana4 UI. That is correct for a serverless
     agent — there is no health endpoint to ping — and does not prevent it receiving work.
   - then run `/dana4:poll` to pick up tasks.
