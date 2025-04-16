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

@app.get("/pixel")
async def pixel(request: Request):
    data = dict(request.query_params)
    data["timestamp"] = datetime.utcnow()

    # ✅ Log extra info
    data["ip"] = request.client.host
    data["referrer"] = request.headers.get("referer")
    data["user_agent"] = request.headers.get("user-agent")

    # ✅ Throttle duplicates (90s per user + creative)
    last_entry = collection.find_one(
        {
            "user_id": data.get("user_id"),
            "creative_id": data.get("creative_id"),
        },
        sort=[("timestamp", -1)]
    )

    if last_entry:
        delta = datetime.utcnow() - last_entry["timestamp"]
        if delta.total_seconds() < 90:
            return Response(content="", media_type="image/gif")

    collection.insert_one(data)

    # Return 1x1 transparent pixel
    pixel_bytes = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF!' \
                  b'\xF9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01' \
                  b'\x00\x00\x02\x02D\x01\x00;'
    return Response(content=pixel_bytes, media_type="image/gif")
