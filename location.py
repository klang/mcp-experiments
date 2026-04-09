from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("location")

IP_API_BASE = "http://ip-api.com/json"


async def make_ip_api_request(ip: str = "") -> dict[str, Any] | None:
    async with httpx.AsyncClient() as client:
        try:
            url = f"{IP_API_BASE}/{ip}" if ip else f"{IP_API_BASE}/"
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "success":
                return None
            return data
        except Exception:
            return None


def format_location(data: dict[str, Any]) -> str:
    return (
        f"IP: {data.get('query', '?')}\n"
        f"City: {data.get('city', '?')}\n"
        f"Region: {data.get('regionName', '?')}\n"
        f"Country: {data.get('country', '?')} ({data.get('countryCode', '?')})\n"
        f"Latitude: {data.get('lat', '?')}\n"
        f"Longitude: {data.get('lon', '?')}\n"
        f"Timezone: {data.get('timezone', '?')}\n"
        f"ZIP: {data.get('zip', '?')}\n"
        f"ISP: {data.get('isp', '?')}\n"
        f"Org: {data.get('org', '?')}"
    )


@mcp.tool()
async def get_location() -> str:
    """Get the current geographic location based on the machine's public IP address.

    Returns city, region, country, latitude, longitude, timezone, and ISP.
    """
    data = await make_ip_api_request()
    if not data:
        return "Unable to determine location."
    return format_location(data)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
