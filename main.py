from fastapi import FastAPI, Request, Query
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime, timedelta
from typing import Optional
import os

# Initialize app
app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["neuro"]
collection = db["impressions"]

# Transparent 1x1 GIF
ONE_BY_ONE_GIF = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF!' \
                 b'\xF9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01' \
                 b'\x00\x00\x02\x02D\x01\x00;'

# Pixel fire and log endpoint
@app.get("/pixel")
async def pixel(request: Request):
    data = dict(request.query_params)
    data["timestamp"] = datetime.utcnow()
    data["ip"] = request.client.host
    data["referrer"] = request.headers.get("referer")
    data["user_agent"] = request.headers.get("user-agent")

    # Throttle duplicates for same user/creative combo within 90 seconds
    if "user_id" in data and "creative_id" in data:
        cutoff = datetime.utcnow() - timedelta(seconds=90)
        existing = collection.find_one({
            "user_id": data.get("user_id"),
            "creative_id": data.get("creative_id"),
            "timestamp": {"$gte": cutoff}
        })
        if existing:
            return Response(content=ONE_BY_ONE_GIF, media_type="image/gif")

    collection.insert_one(data)
    return Response(content=ONE_BY_ONE_GIF, media_type="image/gif")

# Count all impressions
@app.get("/count")
async def get_count():
    count = collection.count_documents({})
    return JSONResponse(content={"count": count})

# Filtered impressions endpoint
@app.get("/impressions")
async def get_impressions(
    campaign_id: Optional[str] = Query(None),
    creative_id: Optional[str] = Query(None)
):
    query = {}
    if campaign_id:
        query["campaign_id"] = campaign_id
    if creative_id:
        query["creative_id"] = creative_id

    count = collection.count_documents(query)
    return JSONResponse(content={"count": count})

@app.get("/creative-impressions")
def get_creative_impressions(
    campaign_id: str = None
):
    query = {}
    if campaign_id:
        query["campaign_id"] = campaign_id

    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$creative_id",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]

    results = list(collection.aggregate(pipeline))
    return results

