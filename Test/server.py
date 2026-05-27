import os
from dotenv import load_dotenv

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token
from fastmcp.server.auth.providers.google import GoogleProvider

# -----------------------------------------------------------------------------
# Load environment variables
# -----------------------------------------------------------------------------
load_dotenv()

# -----------------------------------------------------------------------------
# Google OAuth Provider
# -----------------------------------------------------------------------------
google_auth = GoogleProvider(
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],

    # MUST match Google Console redirect URI EXACTLY
    base_url="http://127.0.0.1:8000",

    # # Required scopes to fetch user info
    # scopes=[
    #     "openid",
    #     "email",
    #     "profile",
    # ],
)

# -----------------------------------------------------------------------------
# MCP Server
# -----------------------------------------------------------------------------
mcp = FastMCP(
    name="Google Auth MCP Server",
    auth=google_auth,
)

# -----------------------------------------------------------------------------
# Protected Tool
# -----------------------------------------------------------------------------
@mcp.tool()
def get_secure_data() -> dict:

    print("Tool called")

    token = get_access_token()

    print("Token:", token)

    if token is None:
        return {"error": "No authentication token"}

    claims = getattr(token, "claims", {}) or {}

    print("Claims:", claims)

    return {
        "name": claims.get("name"),
        "email": claims.get("email"),
        "sub": claims.get("sub"),
    }
# -----------------------------------------------------------------------------
# Public Tool
# -----------------------------------------------------------------------------
@mcp.tool()
def hello() -> dict:
    return {
        "message": "Hello from MCP server"
    }

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("Server running at:")
    print("http://127.0.0.1:8000/mcp")

    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000,
    )
