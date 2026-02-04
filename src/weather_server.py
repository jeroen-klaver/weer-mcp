#!/usr/bin/env python3
"""
MCP Weather Server - Simple temperature lookup via OpenMeteo API
"""
import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response
import uvicorn

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

async def handle_sse(_request):
    """Handle SSE connection"""
    async with SseServerTransport("/messages") as transport:
        await mcp_server.run(
            transport.read_stream,
            transport.write_stream,
            mcp_server.create_initialization_options()
        )
    return Response()

async def health_check(_request):
    """Health check endpoint"""
    return Response("OK", status_code=200)

async def root(_request):
    """Root endpoint with info"""
    info = """MCP Weather Server

Available endpoints:
- GET /health - Health check
- GET /sse - MCP server endpoint (SSE transport)

Location: 51.836316614873176, 5.79300494667676
Tools: get_temperature
"""
    return Response(info, media_type="text/plain")

# Create Starlette app
app = Starlette(
    routes=[
        Route("/", root),
        Route("/sse", handle_sse),
        Route("/health", health_check),
    ]
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
