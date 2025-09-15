import os, time
from pymongo import MongoClient
from graph import app
from models import GlobalState

client = MongoClient(os.getenv("mongodb://localhost:27017/"))
meta = client.audioClient.audioClient


def watcher():
    print("watcher")
    cs = meta.watch([{"$match": {"operationType": "insert", "fullDocument.status": "pending"}}])
    print(cs)
   
    for change in cs:
        print("ici")
        uid = change["fullDocument"]["_id"]
        
        print(uid)
        app.invoke(GlobalState(uid=uid).dict())

if __name__ == "__main__":
    print("OK")
    watcher()