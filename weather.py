from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"


# Helper functions
async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    # Create a dictionary of HTTP headers to send with the request
    # User-Agent identifies our app to the server, Accept specifies we want geo+json format
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    # Create an async HTTP client using httpx's AsyncClient context manager
    # The 'async with' ensures the client is properly closed after use
    async with httpx.AsyncClient() as client:
        try:
            # Make an asynchronous GET request to the URL with the headers and a 30-second timeout
            # 'await' waits for the HTTP request to complete before continuing
            response = await client.get(url, headers=headers, timeout=30.0)
            # Check if the response status code indicates an error (4xx or 5xx)
            # If so, this raises an HTTPStatusError exception
            response.raise_for_status()
            # Parse the response body as JSON and return it as a Python dictionary
            return response.json()
        except Exception:
            return None


def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get("event", "Unknown")}
Area: {props.get("areaDesc", "Unknown")}
Severity: {props.get("severity", "Unknown")}
Description: {props.get("description", "No description available")}
Instructions: {props.get("instruction", "No specific instructions provided")}
"""