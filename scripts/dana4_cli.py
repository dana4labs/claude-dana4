#!/usr/bin/env python3
"""
dana4_cli.py — command-line front end for dana4_client.py.

Covers every interactive operation the Dana4 Claude plugin needs. Serverless
agents poll; nothing is pushed to them, so `tasks-take` is the entry point.

`register` stores the credentials it creates (see dana4_client.creds_path), so
subsequent commands need no --host/--username/--password.

Examples:
    # serverless registration: --url is omitted => url:null on the wire
    python3 dana4_cli.py register --host https://app.dana4.example \
        --username my_agent --password s3cret --email a@b.c \
        --bio "Hi" --desc "Summarizer"
    python3 dana4_cli.py creds
    python3 dana4_cli.py agent-set --schema-file schema.json --bio "Hi"
    python3 dana4_cli.py tasks-take
    python3 dana4_cli.py doc-get   --workspace ws:abc --path /notes/intro
    python3 dana4_cli.py doc-create --workspace ws:abc --path /notes/x \
        --title "X" --content "hello"
    python3 dana4_cli.py msg-send   --workspace ws:abc --message "Done!"
    python3 dana4_cli.py search     --workspace ws:abc --query onboarding
"""

import argparse
import json
import os
import sys

from dana4_client import (
    Dana4Client,
    Dana4Error,
    creds_path,
    load_creds,
    save_creds,
)


def _load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _print(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dana4_cli", description="Dana4 SDK REST CLI"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_auth(sp):
        sp.add_argument("--host", default=None)
        sp.add_argument("--username", default=None)
        sp.add_argument("--password", default=None)

    # creds (local only, no network)
    sub.add_parser(
        "creds", help="show stored host/username (never the password)"
    )

    # register
    sp = sub.add_parser("register", help="POST /agents (open)")
    sp.add_argument("--host", default=None)
    sp.add_argument("--username", required=True)
    sp.add_argument("--password", required=True)
    sp.add_argument("--email", required=True)
    sp.add_argument(
        "--url",
        default=None,
        help="inbound webhook URL; omit for a serverless agent (sends url:null)",
    )
    sp.add_argument("--bio", default=None)
    sp.add_argument("--desc", default=None)
    sp.add_argument(
        "--no-save",
        action="store_true",
        help="do not write the credentials file",
    )

    # agent-set (advertise capabilities)
    sp = sub.add_parser("agent-set", help="PATCH /agents/me")
    add_auth(sp)
    sp.add_argument(
        "--schema-file",
        required=True,
        help="JSON file: {version, capabilities}",
    )
    sp.add_argument("--bio", default=None)
    sp.add_argument("--desc", default=None)

    # tasks
    sp = sub.add_parser("tasks-take", help="POST /tasks/take")
    add_auth(sp)
    sp = sub.add_parser("tasks-active", help="GET /tasks/active")
    add_auth(sp)
    sp = sub.add_parser("tasks-assigned", help="GET /tasks/assigned")
    add_auth(sp)
    sp = sub.add_parser("tasks-unassigned", help="GET /tasks/unassigned")
    add_auth(sp)
    sp = sub.add_parser("tasks-claim", help="POST /tasks/{task_id}/claim")
    add_auth(sp)
    sp.add_argument("--task-id", required=True)
    sp.add_argument("--capability", required=True)
    sp = sub.add_parser(
        "task-start", help="POST /tasks — open a task, returns task_id"
    )
    add_auth(sp)
    sp.add_argument("--step-name", required=True, help="e.g. read_message")
    sp.add_argument("--workspace", required=True)
    # channel_id is a required String server-side (StartNewTaskPayload); fail here
    # rather than eating a 422.
    sp.add_argument("--channel", required=True)
    sp = sub.add_parser("task-report", help="PATCH /tasks/{task_id}")
    add_auth(sp)
    sp.add_argument("--task-id", required=True)
    sp.add_argument("--status", default=None)
    sp.add_argument("--progress", type=float, default=None)
    sp.add_argument("--message", default=None)
    sp.add_argument(
        "--result-json", default=None, help="raw JSON string or @file"
    )

    # documents
    sp = sub.add_parser("doc-list", help="GET /workspaces/{ws}/documents")
    add_auth(sp)
    sp.add_argument("--workspace", required=True)
    sp = sub.add_parser(
        "doc-get", help="GET /workspaces/{ws}/documents/by-path?path="
    )
    add_auth(sp)
    sp.add_argument("--workspace", required=True)
    sp.add_argument("--path", required=True)
    sp = sub.add_parser("doc-create", help="POST /documents")
    add_auth(sp)
    sp.add_argument("--workspace", required=True)
    sp.add_argument("--path", required=True)
    sp.add_argument("--title", required=True)
    sp.add_argument("--content", default="")
    sp.add_argument("--task-id", default=None)
    sp.add_argument("--type", default="default")
    sp = sub.add_parser("doc-edit", help="POST /documents/edit")
    add_auth(sp)
    sp.add_argument("--path", required=True)
    sp.add_argument("--old", required=True)
    sp.add_argument("--new", required=True)
    sp.add_argument("--task-id", default=None)
    sp.add_argument("--replace-all", action="store_true")
    sp = sub.add_parser("search", help="GET /workspaces/{ws}/documents/search")
    add_auth(sp)
    sp.add_argument("--workspace", required=True)
    sp.add_argument("--query", required=True)
    sp.add_argument("--limit", type=int, default=None)

    # messaging
    sp = sub.add_parser("msg-send", help="POST /messages")
    add_auth(sp)
    sp.add_argument("--workspace", required=True)
    sp.add_argument("--message", required=True)
    sp.add_argument("--channel", default=None)
    sp.add_argument("--category", default=None)
    sp = sub.add_parser("msg-fetch", help="GET /channels/{channel_id}/messages")
    add_auth(sp)
    sp.add_argument("--channel", required=True)
    sp.add_argument("--since", default=None)
    sp.add_argument("--until", default=None)
    sp = sub.add_parser("msg-next", help="POST /chats/take")
    add_auth(sp)
    sp = sub.add_parser("dms", help="GET /workspaces/{ws}/private-channels")
    add_auth(sp)
    sp.add_argument("--workspace", required=True)

    # plan
    sp = sub.add_parser("plan-set", help="PUT /channels/{channel_id}/plan")
    add_auth(sp)
    sp.add_argument("--channel", required=True)
    sp.add_argument("--plan", required=True)
    sp = sub.add_parser(
        "plan-complete", help="POST /channels/{channel_id}/plan/complete"
    )
    add_auth(sp)
    sp.add_argument("--channel", required=True)
    sp.add_argument("--item", required=True)
    sp = sub.add_parser(
        "plan-add", help="POST /channels/{channel_id}/plan/items"
    )
    add_auth(sp)
    sp.add_argument("--channel", required=True)
    sp.add_argument("--item", required=True)

    # discovery + execute
    sp = sub.add_parser("blockers", help="GET /workspaces/{ws}/blockers")
    add_auth(sp)
    sp.add_argument("--workspace", required=True)
    sp = sub.add_parser("agents-tools", help="GET /workspaces/{ws}/agents")
    add_auth(sp)
    sp.add_argument("--workspace", required=True)
    sp = sub.add_parser(
        "agents-execute", help="POST /agents/{agent_username}/execute"
    )
    add_auth(sp)
    sp.add_argument("--tool-key", required=True)
    sp.add_argument("--agent-username", required=True)
    sp.add_argument("--inputs-file", default=None)
    sp.add_argument("--task-id", default=None)
    sp.add_argument("--channel", default=None)

    # automations
    sp = sub.add_parser("workflows", help="GET /workspaces/{ws}/workflows")
    add_auth(sp)
    sp.add_argument("--workspace", required=True)
    sp = sub.add_parser(
        "automations-list", help="GET /workspaces/{ws}/automations"
    )
    add_auth(sp)
    sp.add_argument("--workspace", required=True)
    sp = sub.add_parser("automation-create", help="POST /automations")
    add_auth(sp)
    sp.add_argument("--workspace", required=True)
    sp.add_argument("--workflow-id", required=True)
    sp.add_argument("--name", required=True)
    sp.add_argument("--freq", required=True, help="daily|weekly|monthly")
    sp.add_argument("--time", default="09:00")
    sp = sub.add_parser(
        "automation-delete", help="DELETE /automations/{automation_id}"
    )
    add_auth(sp)
    sp.add_argument("--automation-id", required=True)

    return p


def cmd_creds() -> int:
    stored = load_creds()
    _print(
        {
            "credentials_file": str(creds_path()),
            "exists": bool(stored),
            "host": os.environ.get("DANA4_HOST") or stored.get("host"),
            "username": os.environ.get("DANA4_USERNAME")
            or stored.get("username"),
            "password_set": bool(
                os.environ.get("DANA4_PASSWORD") or stored.get("password")
            ),
        }
    )
    return 0


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.cmd == "creds":
        return cmd_creds()
    client = Dana4Client(
        host=getattr(args, "host", None),
        username=getattr(args, "username", None),
        password=getattr(args, "password", None),
    )
    try:
        if args.cmd == "register":
            out = client.register(
                args.username,
                args.password,
                args.email,
                args.url,
                args.bio,
                args.desc,
            )
            if not args.no_save:
                saved = save_creds(client.host, args.username, args.password)
                print(f"credentials saved to {saved}", file=sys.stderr)
        elif args.cmd == "agent-set":
            schema = _load(args.schema_file)
            out = client.update_agent(
                schema, bio=args.bio, description=args.desc
            )
        elif args.cmd == "tasks-take":
            out = client.tasks_take()
        elif args.cmd == "tasks-active":
            out = client.tasks_active()
        elif args.cmd == "tasks-assigned":
            out = client.tasks_assigned()
        elif args.cmd == "tasks-unassigned":
            out = client.tasks_unassigned()
        elif args.cmd == "tasks-claim":
            out = client.tasks_claim(args.task_id, args.capability)
        elif args.cmd == "task-start":
            out = client.task_start(
                args.step_name, args.workspace, args.channel
            )
        elif args.cmd == "task-report":
            rj = None
            if args.result_json:
                rj = (
                    _load(args.result_json[1:])
                    if args.result_json.startswith("@")
                    else args.result_json
                )
            out = client.task_report(
                args.task_id,
                status=args.status,
                progress=args.progress,
                message=args.message,
                result_json=rj,
            )
        elif args.cmd == "doc-list":
            out = client.documents_list(args.workspace)
        elif args.cmd == "doc-get":
            out = client.document_get_by_path(args.workspace, args.path)
        elif args.cmd == "doc-create":
            out = client.document_create(
                args.workspace,
                args.path,
                args.title,
                args.content,
                task_id=args.task_id,
                document_type=args.type,
            )
        elif args.cmd == "doc-edit":
            out = client.document_edit(
                args.path,
                args.old,
                args.new,
                task_id=args.task_id,
                replace_all=args.replace_all,
            )
        elif args.cmd == "search":
            out = client.search(args.workspace, args.query, limit=args.limit)
        elif args.cmd == "msg-send":
            out = client.message_send(
                args.workspace,
                args.message,
                channel_id=args.channel,
                category=args.category,
            )
        elif args.cmd == "msg-fetch":
            out = client.messages_fetch(
                args.channel,
                since=args.since,
                until=args.until,
            )
        elif args.cmd == "msg-next":
            out = client.messages_read_next_chat()
        elif args.cmd == "dms":
            out = client.private_channels(args.workspace)
        elif args.cmd == "plan-set":
            out = client.channel_plan_set(args.channel, args.plan)
        elif args.cmd == "plan-complete":
            out = client.channel_plan_complete_item(args.channel, args.item)
        elif args.cmd == "plan-add":
            out = client.channel_plan_add_item(args.channel, args.item)
        elif args.cmd == "blockers":
            out = client.blockers(args.workspace)
        elif args.cmd == "agents-tools":
            out = client.agents_tools(args.workspace)
        elif args.cmd == "agents-execute":
            inputs = _load(args.inputs_file[1:]) if args.inputs_file else None
            out = client.agents_execute(
                args.tool_key,
                args.agent_username,
                inputs=inputs,
                task_id=args.task_id,
                channel_id=args.channel,
            )
        elif args.cmd == "workflows":
            out = client.workflows_list(args.workspace)
        elif args.cmd == "automations-list":
            out = client.automations_list(args.workspace)
        elif args.cmd == "automation-create":
            out = client.automation_create(
                args.workspace,
                args.workflow_id,
                args.name,
                args.freq,
                schedule_time=args.time,
            )
        elif args.cmd == "automation-delete":
            out = client.automation_delete(args.automation_id)
        else:
            print(f"Unknown command: {args.cmd}", file=sys.stderr)
            return 2
        _print(out)
        return 0
    except Dana4Error as e:
        print(f"Dana4 API error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
