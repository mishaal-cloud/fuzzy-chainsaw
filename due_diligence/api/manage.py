"""CLI tool for managing API keys and viewing analyses.

Usage:
    python -m due_diligence.api.manage create-key --name "John Doe" --email "john@example.com" --tier pro
    python -m due_diligence.api.manage list-keys
    python -m due_diligence.api.manage revoke-key <key-id>
    python -m due_diligence.api.manage list-analyses <key-id>
"""

import argparse
import sys

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from due_diligence.api.database import (
    init_db,
    create_api_key,
    list_api_keys,
    revoke_api_key,
    get_analyses_for_key,
)

console = Console()


def cmd_create_key(args):
    init_db()
    result = create_api_key(args.name, args.email or "", args.tier)

    console.print()
    console.print(Panel(
        f"[bold green]API Key Created Successfully[/bold green]\n\n"
        f"[bold]Name:[/bold]     {result['name']}\n"
        f"[bold]Email:[/bold]    {result['email']}\n"
        f"[bold]Tier:[/bold]     {result['tier']}\n"
        f"[bold]Credits:[/bold]  {result['credits_remaining']}\n"
        f"[bold]Key ID:[/bold]   {result['id']}\n\n"
        f"[bold yellow]API Key (save this — it won't be shown again):[/bold yellow]\n"
        f"[bold white]{result['api_key']}[/bold white]",
        title="New API Key",
        style="green",
    ))
    console.print()


def cmd_list_keys(args):
    init_db()
    keys = list_api_keys()

    if not keys:
        console.print("[dim]No API keys found. Create one with 'create-key'.[/dim]")
        return

    table = Table(title="API Keys")
    table.add_column("ID", style="dim")
    table.add_column("Prefix")
    table.add_column("Name", style="bold")
    table.add_column("Email")
    table.add_column("Tier")
    table.add_column("Credits")
    table.add_column("Created")
    table.add_column("Last Used")
    table.add_column("Active")

    for k in keys:
        table.add_row(
            k["id"][:8] + "...",
            k["key_prefix"],
            k["name"],
            k["email"] or "",
            k["tier"],
            str(k["credits_remaining"]),
            k["created_at"][:10],
            (k["last_used_at"] or "")[:10],
            "[green]Yes[/green]" if k["is_active"] else "[red]No[/red]",
        )

    console.print(table)


def cmd_revoke_key(args):
    init_db()
    if revoke_api_key(args.key_id):
        console.print(f"[green]API key {args.key_id} revoked.[/green]")
    else:
        console.print(f"[red]API key {args.key_id} not found.[/red]")


def cmd_list_analyses(args):
    init_db()
    analyses = get_analyses_for_key(args.key_id)

    if not analyses:
        console.print("[dim]No analyses found for this key.[/dim]")
        return

    table = Table(title="Analyses")
    table.add_column("ID", style="dim")
    table.add_column("Query", max_width=40)
    table.add_column("Status")
    table.add_column("Stage")
    table.add_column("Created")
    table.add_column("Elapsed")

    for a in analyses:
        status_style = {
            "queued": "yellow",
            "running": "blue",
            "completed": "green",
            "failed": "red",
        }.get(a["status"], "")

        elapsed = f"{a['elapsed_seconds']:.0f}s" if a.get("elapsed_seconds") else "-"

        table.add_row(
            a["id"][:8] + "...",
            a["query"][:40],
            f"[{status_style}]{a['status']}[/{status_style}]",
            f"{a['current_stage']}/7 {a.get('stage_name', '')}",
            a["created_at"][:16],
            elapsed,
        )

    console.print(table)


def main():
    parser = argparse.ArgumentParser(
        prog="due_diligence.api.manage",
        description="Manage API keys and analyses for the Due Diligence API",
    )
    sub = parser.add_subparsers(dest="command")

    # create-key
    p_create = sub.add_parser("create-key", help="Create a new API key")
    p_create.add_argument("--name", required=True, help="User or organization name")
    p_create.add_argument("--email", default="", help="Contact email")
    p_create.add_argument("--tier", choices=["free", "pro", "enterprise"], default="free", help="Pricing tier")
    p_create.set_defaults(func=cmd_create_key)

    # list-keys
    p_list = sub.add_parser("list-keys", help="List all API keys")
    p_list.set_defaults(func=cmd_list_keys)

    # revoke-key
    p_revoke = sub.add_parser("revoke-key", help="Revoke an API key")
    p_revoke.add_argument("key_id", help="API key ID to revoke")
    p_revoke.set_defaults(func=cmd_revoke_key)

    # list-analyses
    p_analyses = sub.add_parser("list-analyses", help="List analyses for an API key")
    p_analyses.add_argument("key_id", help="API key ID")
    p_analyses.set_defaults(func=cmd_list_analyses)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
