from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import uvicorn
import httpx
import os

# 1. Load the secret from environment variables
API_SECRET_KEY = os.environ.get("API_SECRET_KEY", "default_secret_if_needed")

port = int(os.environ.get("PORT", 8000))

# Initialize FastMCP
mcp = FastMCP("healthco-mcp")

@mcp.tool()
async def create_patient(name: str, phone: str, email: str = None, dateOfBirth: str = None) -> str:
    """Create a new patient in the clinic system.
    
    Args:
        name: The name of the patient.
        phone: The phone number of the patient.
        email: The email of the patient.
        dateOfBirth: The date of birth of the patient.
    """
    url = "http://49.50.66.74:5003/api/mcp/tools/create-patient"
    
    payload = {
        "name": name,
        "phone": phone,
        "secretKey": API_SECRET_KEY
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
        except Exception as e:
            return f"Error: {str(e)}"

# --- PRODUCTION FIX STARTS HERE ---
# The ASGI app must be exposed at the module level (global scope).
# If this is inside 'if __main__', production servers cannot import 'app'.
app = mcp.sse_app()


# Lightweight health endpoint for service checks
async def health(request):
    return JSONResponse({"status": "ok"})


app.add_route("/health", health, methods=["GET"])


# CORS Middleware must be attached to the global app instance
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- PRODUCTION FIX ENDS HERE ---


if __name__ == "__main__":
    import sys
    print(f"Starting MCP server on http://0.0.0.0:{port}")
    # In development/local, we run the app explicitly
    uvicorn.run(app, host="0.0.0.0", port=port)