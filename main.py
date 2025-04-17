from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from bson.json_util import dumps
from datetime import datetime
from collections import defaultdict
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = MongoClient(os.environ.get("MONGODB_URI"))
db = client["neuro"]
collection = db["impressions"]

@app.get("/impressions")
async def get_impressions(campaign_id: str = None, creative_id: str = None):
    query = {}
    if campaign_id:
        query["campaign_id"] = campaign_id
    if creative_id:
        query["creative_id"] = creative_id

    count = collection.count_documents(query)
    return {"count": count}

@app.get("/creative-impressions")
async def get_creative_impressions(campaign_id: str = None):
    query = {}
    if campaign_id:
        query["campaign_id"] = campaign_id

    pipeline = [
        {"$match": query},
        {"$group": {"_id": "$creative_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    results = list(collection.aggregate(pipeline))
    return results

@app.get("/latest-impression")
async def get_latest_timestamp():
    doc = collection.find().sort("timestamp", -1).limit(1)
    latest = next(doc, None)
    if latest:
        return {"timestamp": latest.get("timestamp")}
    return {"timestamp": None}

@app.get("/")
async def root():
    return {"message": "Neuro Attribution Backend Running"}
