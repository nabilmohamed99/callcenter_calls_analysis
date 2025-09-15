#!/usr/bin/env python3
"""
Importation ultra-rapide et fiable du dataset CallHome (Hugging Face) vers MongoDB GridFS.
Auteur : AI Expert
Usage : python callhome_gridfs_importer.py
"""

import io
import os
import wave
import hashlib
import logging
from typing import Tuple, Optional

from datasets import load_dataset, Audio
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import gridfs

# ---------------- CONFIG ----------------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "callcenter"
BUCKET = "audio_fs"
META = "callhome_meta"
SAMPLES_TO_IMPORT = 3
LOG_LEVEL = logging.INFO
# ----------------------------------------

logging.basicConfig(level=LOG_LEVEL, format="[%(levelname)s] %(message)s")
log = logging.getLogger("callhome_importer")


# ---------- MONGO ----------
class MongoGridFS:
    def __init__(self) -> None:
        self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        self.client.admin.command("ping")
        self.db = self.client[DB_NAME]
        self.fs = gridfs.GridFS(self.db, collection=BUCKET)
        self.meta = self.db[META]
        log.info("✅ MongoDB connecté.")

    def exists(self, uid: str) -> bool:
        return self.meta.find_one({"_id": uid}) is not None

    def insert(self, uid: str, audio_bytes: bytes, duration: float) -> None:
        fid = self.fs.put(audio_bytes, filename=f"{uid}.wav", content_type="audio/wav")
        self.meta.insert_one(
            {
                "_id": uid,
                "duration": duration,
                "file_id": fid,
                "size_bytes": len(audio_bytes),
                "status": "pending",
            }
        )


# ---------- AUDIO ----------
def get_wav_duration(audio_bytes: bytes) -> float:
    try:
        with wave.open(io.BytesIO(audio_bytes)) as f:
            return f.getnframes() / f.getframerate()
    except Exception as e:
        log.warning("Durée illisible : %s", e)
        return 0.0


# ---------- CORE ----------
def import_callhome(limit: int) -> None:
    mongo = MongoGridFS()
    log.info("Chargement du dataset CallHome...")
    ds = load_dataset("talkbank/callhome", "eng", split="data", streaming=True)
    ds = ds.cast_column("audio", Audio(decode=False))

    imported = 0
    skipped = 0

    for sample in ds:
        if imported >= limit:
            break

        audio = sample.get("audio")
        if not audio or not isinstance(audio, dict) or not audio.get("bytes"):
            skipped += 1
            continue

        uid = sample.get("id") or hashlib.md5(audio["bytes"]).hexdigest()
        if mongo.exists(uid):
            skipped += 1
            continue

        duration = get_wav_duration(audio["bytes"])
        if duration == 0.0:
            skipped += 1
            continue

        try:
            mongo.insert(uid, audio["bytes"], duration)
            imported += 1
            log.info("✅ Importé : %s (%.2f s)", uid, duration)
        except PyMongoError as e:
            log.error("❌ Erreur insertion : %s", e)
            skipped += 1

    log.info("Terminé — importés : %s | ignorés : %s", imported, skipped)


# ---------- ENTRY ----------
if __name__ == "__main__":
    import_callhome(SAMPLES_TO_IMPORT)