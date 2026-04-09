import subprocess

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("user-identity")


def run_command(args: list[str]) -> str | None:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None


def get_user_info() -> dict[str, str]:
    info: dict[str, str] = {}

    login = run_command(["whoami"])
    if login:
        info["login"] = login

    finger_output = run_command(["finger", login or ""])
    if finger_output:
        for line in finger_output.splitlines():
            if line.startswith("Login:") and "Name:" in line:
                info["name"] = line.split("Name:", 1)[1].strip()
            if line.startswith("Directory:"):
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "Directory:" and i + 1 < len(parts):
                        info["home"] = parts[i + 1]
                    if part == "Shell:" and i + 1 < len(parts):
                        info["shell"] = parts[i + 1]

    if "home" not in info:
        home = run_command(["sh", "-c", "echo $HOME"])
        if home:
            info["home"] = home

    return info


def format_identity(info: dict[str, str]) -> str:
    lines = []
    if "name" in info:
        lines.append(f"Name: {info['name']}")
    if "login" in info:
        lines.append(f"Login: {info['login']}")
    if "home" in info:
        lines.append(f"Home: {info['home']}")
    if "shell" in info:
        lines.append(f"Shell: {info['shell']}")
    return "\n".join(lines)


@mcp.tool()
async def get_identity() -> str:
    """Get the current user's identity.

    Returns the user's full name, login, home directory, and shell
    using the finger command.
    """
    info = get_user_info()
    if not info:
        return "Unable to determine user identity."
    return format_identity(info)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
