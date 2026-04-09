from typing import Any
import math

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather-danish")

DMI_API_BASE = "https://opendataapi.dmi.dk/v2/metObs"


PARAMETER_LABELS = {
    "temp_dry": ("Temperature", "°C"),
    "temp_dew": ("Dew Point", "°C"),
    "humidity": ("Humidity", "%"),
    "pressure": ("Pressure (station)", "hPa"),
    "pressure_at_sea": ("Pressure (sea level)", "hPa"),
    "wind_speed": ("Wind Speed", "m/s"),
    "wind_dir": ("Wind Direction", "°"),
    "wind_max": ("Wind Gust", "m/s"),
    "precip_past1h": ("Precipitation (1h)", "mm"),
    "sun_last1h_glob": ("Solar Radiation (1h)", "W/m²"),
    "visibility": ("Visibility", "m"),
    "cloud_cover": ("Cloud Cover", "oktas"),
    "temp_grass": ("Grass Temperature", "°C"),
    "temp_soil": ("Soil Temperature", "°C"),
    "leav_hum_dur_past10min": ("Leaf Wetness (10min)", "min"),
}


async def make_dmi_request(url: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Make a request to the DMI Open Data API with proper error handling."""
    headers = {"Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two lat/lon points."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def format_station(feature: dict) -> str:
    """Format a station feature into a readable string."""
    props = feature["properties"]
    coords = feature["geometry"]["coordinates"]
    return (
        f"{props.get('name', 'Unknown')} (ID: {props.get('stationId', '?')})\n"
        f"  Type: {props.get('type', '?')} | Status: {props.get('status', '?')}\n"
        f"  Location: {coords[1]:.4f}N, {coords[0]:.4f}E\n"
        f"  Owner: {props.get('owner', '?')}"
    )


def format_observations(features: list[dict]) -> str:
    """Format observation features into a readable weather summary."""
    if not features:
        return "No observations available."

    latest: dict[str, dict] = {}
    for f in features:
        props = f["properties"]
        pid = props.get("parameterId", "")
        observed = props.get("observed", "")
        if pid not in latest or observed > latest[pid]["properties"]["observed"]:
            latest[pid] = f

    lines = []
    station_id = None
    observed_time = None

    for pid, f in sorted(latest.items()):
        props = f["properties"]
        if station_id is None:
            station_id = props.get("stationId")
        if observed_time is None or props.get("observed", "") > observed_time:
            observed_time = props.get("observed", "")

        value = props.get("value")
        if pid in PARAMETER_LABELS:
            label, unit = PARAMETER_LABELS[pid]
            lines.append(f"  {label}: {value} {unit}")
        else:
            lines.append(f"  {pid}: {value}")

    header = f"Station: {station_id or '?'}\nObserved: {observed_time or '?'}\n"
    return header + "\n".join(lines)


@mcp.tool()
async def get_stations(
    station_type: str = "",
    limit: int = 50,
) -> str:
    """Get active DMI weather stations in Denmark.

    Args:
        station_type: Filter by station type (e.g. Synop, Pluvio, Manual, SHIP). Leave empty for all.
        limit: Maximum number of stations to return (default 50, max 300000).
    """
    params: dict[str, Any] = {
        "status": "Active",
        "limit": limit,
    }
    if station_type:
        params["type"] = station_type

    url = f"{DMI_API_BASE}/collections/station/items"
    data = await make_dmi_request(url, params)

    if not data or "features" not in data:
        return "Unable to fetch stations from DMI."

    if not data["features"]:
        return "No active stations found."

    stations = [format_station(f) for f in data["features"]]
    return f"Found {len(stations)} active station(s):\n\n" + "\n\n".join(stations)


@mcp.tool()
async def get_observations(
    station_id: str,
    parameter_id: str = "",
    period: str = "latest-hour",
) -> str:
    """Get recent meteorological observations from a DMI station.

    Args:
        station_id: DMI station ID (e.g. '06180' for Copenhagen).
        parameter_id: Filter to a specific parameter (e.g. temp_dry, wind_speed, humidity). Leave empty for all.
        period: Time window for observations. Options: latest, latest-10-minutes, latest-hour, latest-day, latest-week, latest-month. Default: latest-hour.
    """
    params: dict[str, Any] = {
        "stationId": station_id,
        "period": period,
        "limit": 1000,
        "sortorder": "observed,DESC",
    }
    if parameter_id:
        params["parameterId"] = parameter_id

    url = f"{DMI_API_BASE}/collections/observation/items"
    data = await make_dmi_request(url, params)

    if not data or "features" not in data:
        return f"Unable to fetch observations for station {station_id}."

    if not data["features"]:
        return f"No recent observations for station {station_id} in period '{period}'."

    return format_observations(data["features"])


@mcp.tool()
async def get_weather(latitude: float, longitude: float) -> str:
    """Get current weather in Denmark by finding the closest active station.

    Args:
        latitude: Latitude of the location (Denmark is roughly 54.5-57.8N).
        longitude: Longitude of the location (Denmark is roughly 8.0-15.2E).
    """
    margin = 0.5
    bbox = f"{longitude - margin},{latitude - margin},{longitude + margin},{latitude + margin}"
    params: dict[str, Any] = {
        "status": "Active",
        "type": "Synop",
        "limit": 50,
        "bbox": bbox,
    }

    url = f"{DMI_API_BASE}/collections/station/items"
    data = await make_dmi_request(url, params)

    if not data or "features" not in data or not data["features"]:
        params["bbox"] = f"{longitude - 2},{latitude - 2},{longitude + 2},{latitude + 2}"
        data = await make_dmi_request(url, params)

    if not data or "features" not in data or not data["features"]:
        return "No active weather stations found near this location."

    closest = None
    closest_dist = float("inf")
    for station in data["features"]:
        coords = station["geometry"]["coordinates"]
        dist = haversine(latitude, longitude, coords[1], coords[0])
        if dist < closest_dist:
            closest_dist = dist
            closest = station

    if closest is None:
        return "Could not determine closest station."

    station_props = closest["properties"]
    station_id = station_props["stationId"]
    station_name = station_props.get("name", "Unknown")

    obs_params: dict[str, Any] = {
        "stationId": station_id,
        "period": "latest-hour",
        "limit": 1000,
        "sortorder": "observed,DESC",
    }
    obs_url = f"{DMI_API_BASE}/collections/observation/items"
    obs_data = await make_dmi_request(obs_url, obs_params)

    if not obs_data or "features" not in obs_data or not obs_data["features"]:
        return f"Found station {station_name} ({station_id}), {closest_dist:.1f} km away, but no recent observations available."

    obs_text = format_observations(obs_data["features"])
    return (
        f"Closest station: {station_name} (ID: {station_id}), {closest_dist:.1f} km away\n\n"
        f"{obs_text}"
    )


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
