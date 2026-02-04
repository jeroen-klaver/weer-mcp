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

# Weather code descriptions (WMO codes)
WEATHER_CODES = {
    0: "Helder",
    1: "Overwegend helder",
    2: "Gedeeltelijk bewolkt",
    3: "Bewolkt",
    45: "Mist",
    48: "Aanvriezende mist",
    51: "Lichte motregen",
    53: "Matige motregen",
    55: "Dichte motregen",
    61: "Lichte regen",
    63: "Matige regen",
    65: "Zware regen",
    71: "Lichte sneeuw",
    73: "Matige sneeuw",
    75: "Zware sneeuw",
    77: "Sneeuwkorrels",
    80: "Lichte buien",
    81: "Matige buien",
    82: "Zware buien",
    85: "Lichte sneeuwbuien",
    86: "Zware sneeuwbuien",
    95: "Onweer",
    96: "Onweer met lichte hagel",
    99: "Onweer met zware hagel"
}

def get_weather_description(code: int) -> str:
    """Get Dutch weather description from WMO code"""
    return WEATHER_CODES.get(code, "Onbekend")

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
                            "version": "2.0.0"
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
                            },
                            {
                                "name": "get_current_weather",
                                "description": f"Get detailed current weather including temperature, humidity, wind, and precipitation for location ({LATITUDE}, {LONGITUDE})",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {},
                                    "required": []
                                }
                            },
                            {
                                "name": "get_forecast",
                                "description": f"Get 5-day weather forecast for location ({LATITUDE}, {LONGITUDE})",
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
                    # Call OpenMeteo API - simple temperature
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

                elif tool_name == "get_current_weather":
                    # Call OpenMeteo API - detailed weather
                    async with httpx.AsyncClient() as client:
                        api_response = await client.get(
                            "https://api.open-meteo.com/v1/forecast",
                            params={
                                "latitude": LATITUDE,
                                "longitude": LONGITUDE,
                                "current": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
                                "timezone": "Europe/Amsterdam"
                            }
                        )
                        api_response.raise_for_status()
                        api_data = api_response.json()

                    current = api_data["current"]

                    # Wind direction conversion
                    wind_dir = current["wind_direction_10m"]
                    directions = ["N", "NO", "O", "ZO", "Z", "ZW", "W", "NW"]
                    wind_dir_text = directions[int((wind_dir + 22.5) / 45) % 8]

                    result_text = f"""Actueel weer:
🌡️ Temperatuur: {current['temperature_2m']}°C (voelt als {current['apparent_temperature']}°C)
💧 Luchtvochtigheid: {current['relative_humidity_2m']}%
🌧️ Neerslag: {current['precipitation']} mm
💨 Wind: {current['wind_speed_10m']} km/u {wind_dir_text}
☁️ Conditie: {get_weather_description(current['weather_code'])}"""

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

                elif tool_name == "get_forecast":
                    # Call OpenMeteo API - 5-day forecast
                    async with httpx.AsyncClient() as client:
                        api_response = await client.get(
                            "https://api.open-meteo.com/v1/forecast",
                            params={
                                "latitude": LATITUDE,
                                "longitude": LONGITUDE,
                                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
                                "timezone": "Europe/Amsterdam",
                                "forecast_days": 5
                            }
                        )
                        api_response.raise_for_status()
                        api_data = api_response.json()

                    daily = api_data["daily"]
                    forecast_lines = ["5-daagse weersverwachting:\n"]

                    for i in range(5):
                        date = daily["time"][i]
                        temp_max = daily["temperature_2m_max"][i]
                        temp_min = daily["temperature_2m_min"][i]
                        precip = daily["precipitation_sum"][i]
                        weather = get_weather_description(daily["weather_code"][i])

                        forecast_lines.append(
                            f"{date}: {weather}, {temp_min}°C - {temp_max}°C, neerslag: {precip}mm"
                        )

                    result_text = "\n".join(forecast_lines)

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
    info = """MCP Weather Server v2.0

Available endpoints:
- GET / - This info page
- GET /health - Health check
- GET /sse - SSE event stream (MCP)
- POST /messages - MCP message endpoint

Location: 51.836316614873176, 5.79300494667676 (Nederland)

Available Tools:
- get_temperature - Simpele temperatuur opvragen
- get_current_weather - Uitgebreid actueel weer (temp, vocht, wind, neerslag)
- get_forecast - 5-daagse weersverwachting

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
