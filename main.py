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

 
