import json
from pymongo import MongoClient
from models import GlobalState
import os
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

def sink_node(state: GlobalState) -> GlobalState:
    client = MongoClient(MONGO_URI)
    client.callcenter.results.replace_one(
        {"_id": state.uid},
        state.model_dump(),
        upsert=True
    )
    print(state.model_dump())
    print("hello")
    # Écriture JSON dans result.txt
    with open("result.txt", "w", encoding="utf-8") as f:
        f.write(json.dumps(state.model_dump(), indent=2, ensure_ascii=False))
    return state