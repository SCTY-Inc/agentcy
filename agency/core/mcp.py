"""MCP server for agency tools.

Exposes stages as MCP tools for Claude/other agents.

Usage:
    agency serve --mcp
"""

import json
import sys
from typing import Any

from agency import plugins
from agency.schemas import CreativeResult, ResearchResult, StrategyResult
from agency.stages import activate, creative, research, strategy


def serve() -> None:
    """Run MCP server on stdio."""
    # MCP protocol over stdio
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line)
            response = _handle_request(request)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        except json.JSONDecodeError:
            _write_error("Invalid JSON")
        except Exception as e:
            _write_error(str(e))


def _handle_request(request: dict) -> dict:
    """Handle MCP request."""
    method = request.get("method", "")
    params = request.get("params", {})
    req_id = request.get("id")

    if method == "initialize":
        return _response(
            req_id,
            {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "agency", "version": "4.0.0"},
                "capabilities": {"tools": {}},
            },
        )

    if method == "tools/list":
        return _response(req_id, {"tools": _list_tools()})

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        result = _call_tool(tool_name, arguments)
        return _response(req_id, {"content": [{"type": "text", "text": result}]})

    return _error_response(req_id, -32601, f"Method not found: {method}")


def _list_tools() -> list[dict]:
    """List available tools."""
    tools = [
        {
            "name": "research",
            "description": "Market research and competitor analysis. Input: campaign brief string.",
            "inputSchema": {
                "type": "object",
                "properties": {"brief": {"type": "string", "description": "Campaign brief"}},
                "required": ["brief"],
            },
        },
        {
            "name": "strategy",
            "description": "Positioning and messaging strategy. Input: ResearchResult JSON.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "research": {"type": "object", "description": "ResearchResult JSON"},
                },
                "required": ["research"],
            },
        },
        {
            "name": "creative",
            "description": "Copy and headline generation. Input: StrategyResult JSON.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "strategy": {"type": "object", "description": "StrategyResult JSON"},
                },
                "required": ["strategy"],
            },
        },
        {
            "name": "activate",
            "description": "Channel planning and calendar. Input: Strategy + Creative JSON.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "strategy": {"type": "object", "description": "StrategyResult JSON"},
                    "creative": {"type": "object", "description": "CreativeResult JSON"},
                },
                "required": ["strategy", "creative"],
            },
        },
    ]

    # Add plugin tools
    for plugin in plugins.list_plugins():
        input_schema: dict[str, Any] = {"type": "object", "properties": {}, "required": []}
        if plugin.input_schema:
            input_schema["properties"]["input"] = {
                "type": "object",
                "description": f"{plugin.input_schema.__name__} JSON",
            }
            input_schema["required"] = ["input"]

        tools.append(
            {
                "name": plugin.name,
                "description": plugin.description,
                "inputSchema": input_schema,
            }
        )

    return tools


def _call_tool(name: str, arguments: dict) -> str:
    """Execute a tool and return JSON result."""
    try:
        if name == "research":
            result = research(arguments["brief"])
        elif name == "strategy":
            r = ResearchResult.model_validate(arguments["research"])
            result = strategy(r)
        elif name == "creative":
            s = StrategyResult.model_validate(arguments["strategy"])
            result = creative(s)
        elif name == "activate":
            s = StrategyResult.model_validate(arguments["strategy"])
            c = CreativeResult.model_validate(arguments["creative"])
            result = activate(s, c)
        else:
            # Try plugin
            plugin = plugins.get(name)
            if plugin:
                result = plugins.run_plugin(name, arguments.get("input", arguments))
            else:
                return json.dumps({"error": f"Unknown tool: {name}"})

        return result.model_dump_json(indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


def _response(req_id: Any, result: dict) -> dict:
    """Create JSON-RPC response."""
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _error_response(req_id: Any, code: int, message: str) -> dict:
    """Create JSON-RPC error response."""
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _write_error(message: str) -> None:
    """Write error to stderr."""
    sys.stderr.write(f"Error: {message}\n")
    sys.stderr.flush()
