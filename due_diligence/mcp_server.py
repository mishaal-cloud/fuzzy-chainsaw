"""MCP (Model Context Protocol) server for the AI Due Diligence tool.

This allows Claude Desktop, Claude Code, and any MCP-compatible AI client
to run due diligence analyses directly.

Run with:
    python -m due_diligence.mcp_server
"""

import json
import sys
import time
import threading
from typing import Any

from due_diligence.api.database import (
    init_db,
    create_api_key,
    validate_api_key,
    create_analysis,
    get_analysis,
    get_analyses_for_key,
    decrement_credits,
)
from due_diligence.api.worker import run_analysis


# ── MCP Protocol Implementation ─────────────────────────────────────
# Implements JSON-RPC 2.0 over stdio as per MCP spec


def write_message(msg: dict):
    """Write a JSON-RPC message to stdout."""
    data = json.dumps(msg)
    sys.stdout.write(f"Content-Length: {len(data)}\r\n\r\n{data}")
    sys.stdout.flush()


def read_message() -> dict | None:
    """Read a JSON-RPC message from stdin."""
    headers = {}
    while True:
        line = sys.stdin.readline()
        if not line:
            return None
        line = line.strip()
        if not line:
            break
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()

    content_length = int(headers.get("Content-Length", 0))
    if content_length == 0:
        return None

    body = sys.stdin.read(content_length)
    return json.loads(body)


# ── Tool Definitions ─────────────────────────────────────────────────

TOOLS = [
    {
        "name": "analyze_company",
        "description": (
            "Run a comprehensive AI due diligence analysis on a startup or company. "
            "This runs a 7-stage pipeline: company research, market analysis, "
            "financial modeling, risk assessment, investor memo, HTML report, and infographic. "
            "Takes 3-7 minutes to complete. Returns an analysis ID you can poll for results."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The analysis query describing what company to analyze and the investment context. "
                        "Example: 'Analyze https://agno.com for Series A investment of $30-50M'"
                    ),
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "check_analysis_status",
        "description": (
            "Check the current status of a running due diligence analysis. "
            "Returns the current stage (1-7) and whether it's completed."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "analysis_id": {
                    "type": "string",
                    "description": "The analysis ID returned from analyze_company",
                },
            },
            "required": ["analysis_id"],
        },
    },
    {
        "name": "get_analysis_results",
        "description": (
            "Get the results of a completed due diligence analysis. "
            "Returns the investor memo, HTML report, and infographic. "
            "Only works after the analysis status is 'completed'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "analysis_id": {
                    "type": "string",
                    "description": "The analysis ID to retrieve results for",
                },
                "format": {
                    "type": "string",
                    "enum": ["memo", "report", "infographic", "all"],
                    "description": "Which result format to return. 'memo' is recommended for chat display.",
                    "default": "memo",
                },
            },
            "required": ["analysis_id"],
        },
    },
    {
        "name": "list_analyses",
        "description": "List recent due diligence analyses and their statuses.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]

# Internal MCP API key (auto-created on first run)
_mcp_key_id: str | None = None


def _ensure_mcp_key() -> str:
    """Ensure an internal API key exists for MCP usage."""
    global _mcp_key_id
    if _mcp_key_id:
        return _mcp_key_id

    # Check if MCP key already exists
    from due_diligence.api.database import list_api_keys
    keys = list_api_keys()
    for k in keys:
        if k["name"] == "__mcp_internal__" and k["is_active"]:
            _mcp_key_id = k["id"]
            return _mcp_key_id

    # Create one
    result = create_api_key("__mcp_internal__", tier="enterprise")
    _mcp_key_id = result["id"]
    return _mcp_key_id


def handle_tool_call(name: str, arguments: dict[str, Any]) -> dict:
    """Handle an MCP tool call and return the result."""
    key_id = _ensure_mcp_key()

    if name == "analyze_company":
        query = arguments["query"]
        analysis_id = create_analysis(key_id, query)

        # Run in background thread
        t = threading.Thread(target=run_analysis, args=(analysis_id, query), daemon=True)
        t.start()

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "status": "queued",
                        "analysis_id": analysis_id,
                        "message": (
                            f"Due diligence analysis started for: {query}\n\n"
                            f"Analysis ID: {analysis_id}\n"
                            "This will take 3-7 minutes. Use check_analysis_status "
                            "to monitor progress."
                        ),
                    }, indent=2),
                }
            ]
        }

    elif name == "check_analysis_status":
        analysis = get_analysis(arguments["analysis_id"])
        if not analysis:
            return {"content": [{"type": "text", "text": "Analysis not found."}]}

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "id": analysis["id"],
                        "query": analysis["query"],
                        "status": analysis["status"],
                        "current_stage": analysis["current_stage"],
                        "stage_name": analysis["stage_name"] or "",
                        "progress": f"{analysis['current_stage']}/7 stages complete",
                        "elapsed_seconds": analysis.get("elapsed_seconds"),
                        "error": analysis.get("error"),
                    }, indent=2),
                }
            ]
        }

    elif name == "get_analysis_results":
        analysis = get_analysis(arguments["analysis_id"])
        if not analysis:
            return {"content": [{"type": "text", "text": "Analysis not found."}]}
        if analysis["status"] != "completed":
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Analysis not yet complete. Current status: {analysis['status']} "
                                f"(Stage {analysis['current_stage']}/7: {analysis['stage_name']})",
                    }
                ]
            }

        fmt = arguments.get("format", "memo")
        result = {"id": analysis["id"], "query": analysis["query"], "status": "completed"}

        if fmt in ("memo", "all"):
            result["memo"] = analysis.get("result_memo", "")
        if fmt in ("report", "all"):
            result["report"] = analysis.get("result_report", "")
        if fmt in ("infographic", "all"):
            result["infographic"] = analysis.get("result_infographic", "")
        if fmt == "all":
            result["summary"] = analysis.get("result_summary", "")

        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

    elif name == "list_analyses":
        analyses = get_analyses_for_key(key_id)
        items = []
        for a in analyses:
            items.append({
                "id": a["id"],
                "query": a["query"],
                "status": a["status"],
                "stage": f"{a['current_stage']}/7",
                "created_at": a["created_at"],
            })
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({"analyses": items}, indent=2) if items
                    else "No analyses found. Use analyze_company to start one.",
                }
            ]
        }

    return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}]}


# ── Main MCP Server Loop ────────────────────────────────────────────


def main():
    """Run the MCP server over stdio."""
    init_db()

    while True:
        msg = read_message()
        if msg is None:
            break

        method = msg.get("method", "")
        msg_id = msg.get("id")

        if method == "initialize":
            write_message({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {
                        "name": "ai-due-diligence",
                        "version": "1.0.0",
                    },
                },
            })

        elif method == "notifications/initialized":
            pass  # No response needed for notifications

        elif method == "tools/list":
            write_message({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": TOOLS},
            })

        elif method == "tools/call":
            params = msg.get("params", {})
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})

            result = handle_tool_call(tool_name, tool_args)
            write_message({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result,
            })

        elif msg_id is not None:
            write_message({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            })


if __name__ == "__main__":
    main()
