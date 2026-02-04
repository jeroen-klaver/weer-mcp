# MCP Weather Server Project Plan

## Doel
Een MCP (Model Context Protocol) server maken in een Docker container die temperatuurdata ophaalt via OpenMeteo API en beschikbaar maakt voor OpenWebUI.

**Locatie:** 51.836316614873176, 5.79300494667676

## Todo Items

### 1. Project Setup
- [x] Kies technologie stack (Python met MCP SDK)
- [x] Maak basis projectstructuur
- [x] Maak package.json of requirements.txt

### 2. MCP Server Implementation
- [x] Implementeer MCP server met OpenMeteo tool
- [x] Maak functie om temperatuur op te halen voor gegeven locatie
- [ ] Test de server lokaal

### 3. Docker Setup
- [x] Maak Dockerfile
- [x] Maak docker-compose.yml voor eenvoudige deployment
- [x] Configureer juiste poorten en networking

### 4. OpenWebUI Integratie
- [x] Documenteer hoe OpenWebUI de MCP server kan verbinden
- [ ] Test de verbinding

### 5. Documentatie
- [x] README met instructies
- [x] Voorbeeld gebruik

## Technische Keuzes
- **Taal:** Python (goede MCP SDK support)
- **MCP SDK:** @modelcontextprotocol/sdk voor Python
- **API:** OpenMeteo (gratis, geen API key nodig)
- **Container:** Docker met continue werking
- **Communicatie:** MCP protocol via stdio of SSE

## Eenvoudige Aanpak
- Minimale dependencies
- Alleen de essentiële functionaliteit (temperatuur ophalen)
- Simpele Docker configuratie
- Duidelijke documentatie

---

## Review

### Gemaakte Bestanden
1. **[src/weather_server.py](../src/weather_server.py)** - MCP server implementatie
   - Gebruikt MCP SDK voor Python
   - Één tool: `get_temperature`
   - Haalt data op van OpenMeteo API voor vaste locatie
   - Draait via stdio protocol

2. **[requirements.txt](../requirements.txt)** - Python dependencies
   - mcp >= 1.0.0
   - httpx >= 0.27.0

3. **[Dockerfile](../Dockerfile)** - Container definitie
   - Python 3.11 slim image
   - Installeert dependencies
   - Draait weather_server.py

4. **[docker-compose.yml](../docker-compose.yml)** - Orchestration
   - Simpele configuratie
   - restart: unless-stopped voor continue werking
   - stdin_open en tty voor interactieve communicatie

5. **[README.md](../README.md)** - Documentatie
   - Installatie instructies
   - OpenWebUI integratie voorbeeld
   - Gebruik voorbeelden

6. **[.dockerignore](../.dockerignore)** - Docker optimalisatie
   - Sluit onnodige bestanden uit

### Implementatie Details
- **Simpel:** Alleen de essentiële functionaliteit, geen overhead
- **Robuust:** Gebruikt async/await voor non-blocking API calls
- **Container:** Draait continu, altijd beschikbaar voor OpenWebUI
- **Configuratie:** Vaste locatie gecodeerd (51.836316614873176, 5.79300494667676)

### Volgende Stappen voor Gebruik
1. Build: `docker-compose build`
2. Start: `docker-compose up -d`
3. Configureer OpenWebUI om MCP server te gebruiken
4. Test de verbinding

### Mogelijke Verbeteringen (indien nodig)
- HTTP/SSE endpoint toevoegen als OpenWebUI geen stdio ondersteunt
- Meerdere locaties ondersteunen via parameters
- Meer weer-informatie (luchtvochtigheid, wind, etc.)
- Error handling en logging verbeteren
