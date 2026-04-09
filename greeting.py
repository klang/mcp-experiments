from mcp.server.fastmcp import FastMCP

mcp = FastMCP("greeting")


@mcp.tool()
async def get_greeting() -> str:
    """Get a greeting."""
    return "Hello, World!"


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
