from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os, re, httpx
from dotenv import load_dotenv
load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
FORM_SECRET         = os.getenv("FORM_SECRET")

if not DISCORD_WEBHOOK_URL or not FORM_SECRET:
    raise RuntimeError("Missing DISCORD_WEBHOOK_URL or FORM_SECRET env vars")

app = FastAPI()

# CORS — allow your frontend (edit origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# Same phone regex you use on the frontend (+XXXXXXXX…)
PHONE_RE = re.compile(r"^\+\d{7,15}$")

class ContactPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    phone: str
    pack: int
    message: str | None = Field(default=None, max_length=2000)

@app.post("/api/contact")
async def relay_to_discord(
    body: ContactPayload,
    x_secret: str | None = Header(default=None, convert_underscores=False),
):
    # Basic auth
    
    # if x_secret != FORM_SECRET:
    #     raise HTTPException(status_code=401, detail="Unauthorized")

    # Validate phone again on server
    if not PHONE_RE.match(body.phone.replace(" ", "")):
        raise HTTPException(status_code=400, detail="Invalid phone")
    # Build Discord embed
    embed = {
        "title": "🆕 New form submission",
        "color": 0x2ECC71,
        "fields": [
            {"name": "Name",    "value": body.name,                "inline": True},
            {"name": "Phone",   "value": body.phone,               "inline": True},
            {"name": "Package", "value": f"{body.pack}h"},
            {"name": "Message", "value": body.message or "—"},
        ],
    }

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            DISCORD_WEBHOOK_URL,
            json={"username": "Improglish Server", "embeds": [embed]},
            headers={"Content-Type": "application/json"},
        )
    if r.status_code >= 300:
       
        raise HTTPException(status_code=502, detail="Discord relay failed")

    return {"ok": True}
