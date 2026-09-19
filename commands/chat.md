---
description: Read Dana4 chat addressed to this agent and reply
argument-hint: "[workspace_id] [channel_id]"
---

Read the Dana4 chat waiting for this agent and reply where a reply is wanted.

Arguments (both optional): `$1` a workspace id, `$2` a channel id.

Read `${CLAUDE_PLUGIN_ROOT}/skills/dana4/SKILL.md` for the endpoint details.

1. Read the agent inbox:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" msg-next
   ```

2. **Also poll any channel the user named**, because the inbox is not the channel log:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" msg-fetch \
       --workspace "<workspace_id>" --channel "<channel_id>"
   ```

   `msg-next` only returns chats the server routed to this agent. A message posted in a
   channel this agent was never formally added to will not appear there — that is the
   single most common cause of "I tagged the agent and it never answered". If the user
   reports a missing message and gave no channel, ask for the workspace and channel id and
   fetch them directly.

3. Drop messages with `from: null` — those are system/automated noise, not people.

4. Summarise what is waiting. **Do not reply on your own initiative**: show the user the
   messages and what you propose to say, and send only what they approve. These are real
   conversations with real people in a shared workspace.

5. To send an approved reply:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/dana4_cli.py" msg-send \
       --workspace "<workspace_id>" --channel "<channel_id>" --message "<reply>"
   ```

   If replying is part of a task you claimed, open a task first with `task-start` and close
   it with `task-report` afterwards.
