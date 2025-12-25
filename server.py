from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
import uvicorn
import httpx
import os

# Initialize FastMCP server
# Render/Cloud Run set the PORT environment variable.
port = int(os.environ.get("PORT", 8000))
mcp = FastMCP("healthco-mcp", host="0.0.0.0", port=port)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "name": mcp.name})


@mcp.custom_route("/", methods=["GET"])
async def index(_: Request) -> PlainTextResponse:
    return PlainTextResponse(
        "MCP server is running. Streamable HTTP endpoint: /mcp"
    )

@mcp.tool()
async def create_patient(name: str, phone: str, secretKey: str, email: str = None, dateOfBirth: str = None) -> str:
    """Create a new patient in the clinic system.

    Args:
        name: The name of the patient.
        phone: The phone number of the patient.
        secretKey: The secret key for authentication.
        email: The email of the patient.
        dateOfBirth: The date of birth of the patient.
    """
    url = "http://49.50.66.74:5003/api/mcp/tools/create-patient"
    
    payload = {
        "name": name,
        "phone": phone,
        "secretKey": secretKey
    }
    if email:
        payload["email"] = email
    if dateOfBirth:
        payload["dateOfBirth"] = dateOfBirth

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return f"Successfully created patient: {response.text}"
        except httpx.HTTPStatusError as e:
            return f"Failed to create patient. Status: {e.response.status_code}, Error: {e.response.text}"
        except Exception as e:
            return f"An error occurred: {str(e)}"

if __name__ == "__main__":
    import sys
    arg_transport = sys.argv[1].lower() if len(sys.argv) > 1 else None

    # Modes:
    # - stdio: local VS Code MCP (spawned process)
    # - streamable-http: remote deployments (endpoint at /mcp)
    if arg_transport == "stdio":
        mcp.run(transport="stdio")
        raise SystemExit(0)

    # Always serve MCP over Streamable HTTP for deployments.
    # Endpoint is /mcp (FastMCP default).
    app = mcp.streamable_http_app()

    # CORS is mainly relevant for browser-based clients.
    # If you truly need credentialed requests, set MCP_CORS_ORIGINS to a comma-separated allowlist.
    cors_origins = os.environ.get("MCP_CORS_ORIGINS", "*")
    allow_origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
    allow_credentials = os.environ.get("MCP_CORS_ALLOW_CREDENTIALS", "false").lower() == "true"

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    print(f"Starting MCP server on http://0.0.0.0:{port} (streamable-http)")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
