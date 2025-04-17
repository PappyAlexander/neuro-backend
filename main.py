from fastapi.responses import Response
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

ONE_BY_ONE_GIF = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF!' \
                 b'\xF9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01' \
                 b'\x00\x00\x02\x02D\x01\x00;'


@app.get("/pixel")
async def pixel(request: Request):
    data = dict(request.query_params)
    data["timestamp"] = datetime.utcnow()
    data["ip"] = request.client.host
    data["referrer"] = request.headers.get("referer")
    data["user_agent"] = request.headers.get("user-agent")

    # Logging into Mongo
    collection.insert_one(data)

    # Return 1x1 transparent GIF with correct headers
    return Response(content=ONE_BY_ONE_GIF, media_type="image/gif")

from fastapi.responses import JSONResponse

@app.get("/count")
async def get_count():
    count = collection.count_documents({})
    return JSONResponse(content={"count": count})

