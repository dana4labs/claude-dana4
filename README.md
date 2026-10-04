# Dana4 plugin for Claude

Turns a Claude session into a **serverless** [Dana4](https://dana4.io) agent: it gets an
API key through a link you approve in Dana4, then polls the Dana4 SDK REST API for tasks and chat, and
reads, writes and searches workspace documents.

Serverless means Dana4 never calls in. There is no webhook to host and no port to open —
the session pulls its work.

## Install

Claude Code:

```
/plugin marketplace add dana4labs/claude-dana4
/plugin install dana4@dana4
```

Claude Desktop installs it from the settings UI — see
[the docs](https://dana4.io/docs/integrations/claude-desktop/).

## Use

| Command | What it does |
| --- | --- |
| `/dana4:enroll` | Connect this session to Dana4 (asks for the host; you approve a link) |
| `/dana4:poll` | Check chat first (reply with your approval); if none, claim the next task, run it, report the result |
| `/dana4:status` | Show the configured host, open tasks, and blockers |

When you approve the link you pick the workspaces the agent may work in, and you become its
owner: rotate or revoke its key from the Agents page of the Dana4 web app.

The `dana4` skill loads on its own when a request mentions Dana4, so the agent can also be
driven conversationally ("check my Dana4 tasks", "post that to the design channel").

## Requirements

`python3` only. The bundled client uses the standard library — nothing to install.

## Layout

```
commands/       the three /dana4:* slash commands
skills/dana4/    the skill: usage, gotchas, and the endpoint reference
scripts/        stdlib-only REST client + CLI, and its self-check
```

Credentials are stored in `~/.config/dana4/credentials.json` (mode 0600) and can be
overridden per-project with `DANA4_HOST` / `DANA4_API_KEY`.

Run the self-check with `python3 scripts/test_dana4_client.py` (no network needed).
