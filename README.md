# Weather MCP Server

Een simpele MCP (Model Context Protocol) server die actuele temperatuurdata ophaalt via de OpenMeteo API.

## Locatie
**Coördinaten:** 51.836316614873176, 5.79300494667676

## Functionaliteit
- **Tool:** `get_temperature` - Haalt de huidige temperatuur op voor de geconfigureerde locatie

## Installatie & Gebruik

### 1. Build de Docker container
```bash
docker-compose build
```

### 2. Start de server
```bash
docker-compose up -d
```

De server draait nu continu in de achtergrond.

### 3. Logs bekijken
```bash
docker-compose logs -f weather-mcp
```

### 4. Stoppen
```bash
docker-compose down
```

## OpenWebUI Integratie

Om deze MCP server te gebruiken met OpenWebUI:

### Standalone (lokaal testen)
De server draait op `http://localhost:8000` met de volgende endpoints:
- `/sse` - MCP server endpoint (SSE transport)
- `/health` - Health check

### Via Docker Network
1. Voeg de weather-mcp service toe aan hetzelfde Docker netwerk als OpenWebUI
2. Configureer OpenWebUI om de MCP server te gebruiken via: `http://weather-mcp-server:8000/sse`

### Configuratie in docker-compose
Voeg toe aan je OpenWebUI docker-compose.yml:

```yaml
services:
  open-webui:
    # ... je bestaande OpenWebUI config
    environment:
      - MCP_SERVERS=weather:http://weather-mcp-server:8000/sse
    networks:
      - webui-network

  weather-mcp:
    build: ./weer-mcp
    container_name: weather-mcp-server
    restart: unless-stopped
    ports:
      - "8000:8000"
    networks:
      - webui-network

networks:
  webui-network:
    driver: bridge
```

## Voorbeeld Tool Call

Wanneer je in OpenWebUI vraagt naar het weer, kan de AI de `get_temperature` tool gebruiken:

```
Vraag: "Wat is de huidige temperatuur?"
Tool: get_temperature
Resultaat: "Current temperature: 8.5°C"
```

## Technologie
- **Python 3.11**
- **MCP SDK** - Model Context Protocol
- **OpenMeteo API** - Gratis weer API
- **httpx** - Async HTTP client

## Dependencies
- mcp >= 1.0.0
- httpx >= 0.27.0
