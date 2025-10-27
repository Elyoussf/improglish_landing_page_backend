from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, conint
import os, re, httpx
from dotenv import load_dotenv
from typing import Optional

# Load environment variables for webhook URL and secret
load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
FORM_SECRET         = os.getenv("FORM_SECRET")

# Ensure required environment variables are set
if not DISCORD_WEBHOOK_URL or not FORM_SECRET:
    # Use a logger or standard print for local debugging
    print("WARNING: Missing DISCORD_WEBHOOK_URL or FORM_SECRET env vars. Running without authentication/relay.")
    # raise RuntimeError("Missing DISCORD_WEBHOOK_URL or FORM_SECRET env vars") # Commented out for easier testing

app = FastAPI()

# --- CORS Configuration ---
# Allow all origins for development. Adjust to specific frontend URL in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# --- Validation and Models ---

# Regex for phone: International format starting with + and 7-15 digits
PHONE_RE = re.compile(r"^\+\d{7,15}$")

# Update the payload model to match the fields sent by the React frontend
class ContactPayload(BaseModel):
    # name: str = Field(min_length=1, max_length=120)
    # phone: str
    # age: conint(ge=10, le=99)  # Expects an integer between 10 and 99
    # language: str = Field(min_length=2, max_length=5) # e.g., 'FR' or 'EN'
    # study_language: str
    # pack_name: str
    # pack_total_price:str
    # pack_total_hours:str
    # pack_price_per_hour: str
    # pack_option_selected: str
    # availability_summary: str
    # message: Optional[str] = Field(default="N/A", max_length=2000)
    # # The frontend is sending a pre-formatted message. We capture it here.
    discord_message: str


@app.post("/api/contact")
async def relay_to_discord(
    body: ContactPayload,
    x_secret: str | None = Header(default=None, convert_underscores=False),
):
 
    
   

   
    
    discord_payload = {
        "username": "Improglish Server", 
        "content": body.discord_message
    }

    if DISCORD_WEBHOOK_URL:
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                r = await client.post(
                    DISCORD_WEBHOOK_URL,
                    json=discord_payload,
                    headers={"Content-Type": "application/json"},
                )
                r.raise_for_status() # Raises HTTPError for bad status codes
            except httpx.HTTPStatusError as e:
                # Log or handle Discord API failure
                print(f"Discord relay failed: {e.response.text}")
                # We return success to the user, as the failure is external (Discord side), but log it
                # Optionally, raise 502 here if relay failure must halt user request:
                # raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Discord relay failed")
            except httpx.RequestError as e:
                print(f"HTTPX Request Error: {e}")
                # Optionally, raise 502 here
        
    return {"ok": True, "message": "Request processed."}
