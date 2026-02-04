#!/usr/bin/env python3
"""
MCP Weather Server - Simple temperature lookup via OpenMeteo API
"""
import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.routing import Route
import uvicorn
import json
from typing import Any
import asyncio

# Fixed location: 51.836316614873176, 5.79300494667676
LATITUDE = 51.836316614873176
LONGITUDE = 5.79300494667676

mcp_server = Server("weather-server")

@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="get_temperature",
            description=f"Get current temperature for location ({LATITUDE}, {LONGITUDE}) via OpenMeteo API",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    if name != "get_temperature":
        raise ValueError(f"Unknown tool: {name}")

    # Call OpenMeteo API
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": LATITUDE,
                "longitude": LONGITUDE,
                "current": "temperature_2m",
                "timezone": "Europe/Amsterdam"
            }
        )
        response.raise_for_status()
        data = response.json()

    # Extract temperature
    temp = data["current"]["temperature_2m"]
    unit = data["current_units"]["temperature_2m"]

    result = f"Current temperature: {temp}{unit}"

    return [TextContent(
        type="text",
        text=result
    )]

# SSE message handling
message_queue: asyncio.Queue = asyncio.Queue()

async def handle_sse_endpoint(request: Request):
    """Handle SSE endpoint - streams events to client or handles POST messages"""

    # Handle POST requests (MCP messages)
    if request.method == "POST":
        try:
            data = await request.json()
            method = data.get("method")
            print(f"Received MCP request: {method}")

            # Handle different MCP methods
            if method == "initialize":
                response_data = {
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "result": {
                        "protocolVersion": "2025-11-25",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "weather-server",
                            "version": "1.0.0"
                        }
                    }
                }

            elif method == "tools/list":
                response_data = {
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "result": {
                        "tools": [
                            {
                                "name": "get_temperature",
                                "description": f"Get current temperature for location ({LATITUDE}, {LONGITUDE}) via OpenMeteo API",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {},
                                    "required": []
                                }
                            }
                        ]
                    }
                }

            elif method == "tools/call":
                tool_name = data.get("params", {}).get("name")
                print(f"Calling tool: {tool_name}")

                if tool_name == "get_temperature":
                    # Call OpenMeteo API
                    async with httpx.AsyncClient() as client:
                        api_response = await client.get(
                            "https://api.open-meteo.com/v1/forecast",
                            params={
                                "latitude": LATITUDE,
                                "longitude": LONGITUDE,
                                "current": "temperature_2m",
                                "timezone": "Europe/Amsterdam"
                            }
                        )
                        api_response.raise_for_status()
                        api_data = api_response.json()

                    temp = api_data["current"]["temperature_2m"]
                    unit = api_data["current_units"]["temperature_2m"]
                    result_text = f"Current temperature: {temp}{unit}"

                    response_data = {
                        "jsonrpc": "2.0",
                        "id": data.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": result_text
                                }
                            ]
                        }
                    }
                else:
                    response_data = {
                        "jsonrpc": "2.0",
                        "id": data.get("id"),
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    }

            else:
                response_data = {
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Unknown method: {method}"
                    }
                }

            return Response(
                content=json.dumps(response_data),
                media_type="application/json"
            )
        except Exception as e:
            print(f"Error handling POST: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                content=json.dumps({
                    "jsonrpc": "2.0",
                    "id": data.get("id") if "data" in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }),
                status_code=500,
                media_type="application/json"
            )

    # Handle GET requests (SSE stream)
    async def event_stream():
        try:
            while True:
                # Wait for messages
                message = await asyncio.wait_for(message_queue.get(), timeout=30.0)
                yield f"data: {json.dumps(message)}\n\n"
        except asyncio.TimeoutError:
            # Send keepalive
            yield ": keepalive\n\n"
        except Exception as e:
            print(f"SSE error: {e}")
            return

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

async def handle_messages(request: Request):
    """Handle incoming MCP messages via POST"""
    try:
        data = await request.json()
        print(f"Received message: {data}")

        # Simple response for now
        response_data = {
            "jsonrpc": "2.0",
            "id": data.get("id"),
            "result": {"status": "ok"}
        }

        return Response(
            content=json.dumps(response_data),
            media_type="application/json"
        )
    except Exception as e:
        print(f"Error handling message: {e}")
        return Response(
            content=json.dumps({"error": str(e)}),
            status_code=500,
            media_type="application/json"
        )

async def health_check(_request: Request):
    """Health check endpoint"""
    return Response("OK", status_code=200)

async def root(_request: Request):
    """Root endpoint with info"""
    info = """MCP Weather Server

Available endpoints:
- GET / - This info page
- GET /health - Health check
- GET /sse - SSE event stream
- POST /messages - MCP message endpoint

Location: 51.836316614873176, 5.79300494667676
Tools: get_temperature

Status: Running
"""
    return Response(info, media_type="text/plain")

# Create Starlette app
app = Starlette(
    debug=True,
    routes=[
        Route("/", root, methods=["GET"]),
        Route("/sse", handle_sse_endpoint, methods=["GET", "POST"]),
        Route("/messages", handle_messages, methods=["POST"]),
        Route("/health", health_check, methods=["GET"]),
    ]
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
