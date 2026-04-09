# mcp-experiments

A collection of small Model Context Protocol (MCP) servers for experimenting with tool-based LLM interactions. None of these servers require API keys.

## Servers

### weather.py
Provides US weather data via the National Weather Service API (api.weather.gov).
*   `get_forecast(latitude, longitude)`: Returns the forecast for the next 5 periods at a US location.
*   `get_alerts(state)`: Lists active weather alerts for a US state using its two-letter code.

### weather-danish.py
Provides Danish meteorological data via the DMI Open Data API (opendataapi.dmi.dk).
*   `get_stations(station_type, limit)`: Lists active DMI weather stations, with optional filtering by type like Synop or Pluvio.
*   `get_observations(station_id, parameter_id, period)`: Shows recent observations from a specific station.
*   `get_weather(latitude, longitude)`: Finds the closest Synop station to provide current weather for a location.

### location.py
Provides IP-based geolocation via ip-api.com. This uses the free HTTP tier.
*   `get_location()`: Returns the city, region, country, coordinates, timezone, and ISP associated with the machine's public IP address.

### greeting.py
A minimal hello-world MCP server.
*   `get_greeting()`: Returns a simple "Hello, World!" string.

### user-identity.py
Identifies the local user via the Unix `finger` command.
*   `get_identity()`: Returns the user's full name, login, home directory, and shell.

## Getting started

This project requires Python 3.12 or newer and the uv package manager.

The MCP servers are defined in the .mcp.json file located in the project root. Each server runs as a standalone script using the stdio transport mechanism. You can execute them individually using `uv run <script>.py`.

If you use Claude Code, the configuration in .mcp.json allows all servers to be registered and used as tools automatically.
