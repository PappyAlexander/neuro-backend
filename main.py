from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["neuro"]
collection = db["impressions"]

@app.get("/track")
async def track_get(request: Request):
    data = dict(request.query_params)
    data["timestamp"] = datetime.utcnow()
    collection.insert_one(data)
    return {"status": "logged"}

@app.get("/dashboard-data")
async def dashboard():
    records = list(collection.find({}, {"_id": 0}))
    return {"data": records}

from fastapi.responses import Response
import base64

# Base64-encoded 1x1 transparent GIF
TRANSPARENT_PIXEL = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
)

@app.get("/pixel")
async def pixel(request: Request):
   from fastapi.responses import Response
import base64
from datetime import timedelta

TRANSPARENT_PIXEL = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
)

@app.get("/pixel")
async def pixel(request: Request):
    data = dict(request.query_params)
    data["timestamp"] = datetime.utcnow()

    # ✅ Add metadata
    data["ip"] = request.client.host
    data["referrer"] = request.headers.get("referer")
    data["user_agent"] = request.headers.get("user-agent")


    # ✅ Throttle if seen in last 90 seconds
    lookback = datetime.utcnow() - timedelta(seconds=90)
    existing = collection.find_one({
        "campaign_id": data.get("campaign_id"),
        "creative_id": data.get("creative_id"),
        "user_id": data.get("user_id"),
        "timestamp": { "$gte": lookback }
    })

    if not existing:
        collection.insert_one(data)

    return Response(content=TRANSPARENT_PIXEL, media_type="image/gif")

