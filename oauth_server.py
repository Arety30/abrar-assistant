import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import requests
import uvicorn
import asyncio
import threading

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="~/Workspace/AbrarAssistant/activity_frontend/dist"), name="static")

@app.get("/")
async def read_index():
    return HTMLResponse(open("~/Workspace/AbrarAssistant/activity_frontend/dist/index.html").read())

# OAuth configuration
CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')

# Simple in-memory token store (In production, replace with a secure database)
user_tokens = {}

# Activity API Gateway
@app.post("/api/controller")
async def ai_controller(request: Request):
    data = await request.json()
    # Placeholder for AI Controller logic (routing to bot/services)
    return {"status": "ok", "message": f"Processed command: {data.get('command')}"}

@app.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state") # This is the discord user ID
    
    if not code:
        return HTMLResponse("Authorization failed: No code provided.")

    # Exchange code for token
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    response = requests.post(token_url, data=data)
    token_data = response.json()
    
    if "access_token" in token_data:
        user_tokens[state] = token_data["access_token"]
        return HTMLResponse("<h1>Authentication Successful!</h1><p>You can now return to Discord.</p>")
    else:
        return HTMLResponse("<h1>Authentication Failed!</h1><p>Could not exchange code for token.</p>")

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
