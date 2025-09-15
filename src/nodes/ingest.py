import io
import os
from pymongo import MongoClient
import gridfs
from models import GlobalState

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

def ingest_node(state: GlobalState) -> GlobalState:
    client = MongoClient(MONGO_URI)
    db = client["audioClient"]
    fs = gridfs.GridFS(db,collection="audioClient")   # 
    doc = client.audioClient.audioClient.files.find_one({"filename": f"{state.uid}.wav"})
    #                            
    if not doc:
        raise FileNotFoundError(f"uid {state.uid} non trouvé dans audioClient.files")

    audio_bytes = fs.get(doc["_id"]).read()

    return GlobalState(**{**state.dict(), "audio_bytes": audio_bytes})

