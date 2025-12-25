from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
import uvicorn
import httpx
import os

# Initialize FastMCP server
# We set the host to 0.0.0.0 to make it accessible externally
# Render sets the PORT environment variable, so we need to use it.
port = int(os.environ.get("PORT", 8000))
mcp = FastMCP("healthco-mcp", host="0.0.0.0", port=port)

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
    if len(sys.argv) > 1 and sys.argv[1] == "stdio":
        mcp.run(transport="stdio")
    else:
        # Run the server using SSE transport
        print(f"Starting MCP server on http://0.0.0.0:{port}")
        
        # Get the underlying Starlette app
        app = mcp.sse_app()
        
        # Add CORS middleware to allow Retell AI (and others) to connect
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        uvicorn.run(app, host="0.0.0.0", port=port)
