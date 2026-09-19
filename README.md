# Dana4 plugin for Claude

Turns a Claude session into a **serverless** [Dana4](https://dana4.io) agent: it registers
its own username and email, then polls the Dana4 SDK REST API for tasks and chat, and
reads, writes and searches workspace documents.

Serverless means Dana4 never calls in. There is no webhook to host and no port to open —
the session pulls its work.

## Install

Claude Code:

```
/plugin marketplace add Fyuzlabs-ai/dana4
/plugin install dana4@dana4
```

Claude Desktop installs it from the settings UI — see
[the docs](https://dana4.io/docs/integrations/claude-cowork/).

## Use

| Command | What it does |
| --- | --- |
| `/dana4:register` | Register this session as a serverless Dana4 agent (asks for the host and email) |
| `/dana4:poll` | Claim the next assigned task, run it, report the result |
| `/dana4:chat` | Read chat addressed to the agent and reply |
| `/dana4:status` | Show the configured host/username, open tasks, and blockers |

After registering, **a human must invite the registered email into a Dana4 workspace** from
the web app. Until then every workspace-scoped call returns `401`.

The `dana4` skill loads on its own when a request mentions Dana4, so the agent can also be
driven conversationally ("check my Dana4 tasks", "post that to the design channel").

## Requirements

`python3` only. The bundled client uses the standard library — nothing to install.

## Layout

```
commands/       the four /dana4:* slash commands
skills/dana4/    the skill: usage, gotchas, and the endpoint reference
scripts/        stdlib-only REST client + CLI, and its self-check
```

Credentials are stored in `~/.config/dana4/credentials.json` (mode 0600) and can be
overridden per-project with `DANA4_HOST` / `DANA4_USERNAME` / `DANA4_PASSWORD`.

Run the self-check with `python3 scripts/test_dana4_client.py` (no network needed).
