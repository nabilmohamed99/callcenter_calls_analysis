#!/usr/bin/env python3
"""
Import optimisé : HuggingFace CallHome (eng) → MongoDB GridFS
Niveau : Expert
Dépendances : pip install datasets pymongo tqdm numpy
"""
import io
import os
import argparse
import wave  # Module standard Python pour les fichiers .wav
from datasets import load_dataset
from datasets.features import Audio
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import gridfs
from tqdm import tqdm


# --- Configuration ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = "callcenter"
BUCKET    = "audio_fs"
META      = "callhome_meta"
# --- Connexion robuste à la base de données ---
try:
    client = MongoClient("mongodb://localhost:27017/?replicaSet=rs0", serverSelectionTimeoutMS=5000)

    client.server_info()  # Force la connexion pour une vérification immédiate
    print("✅ Connexion à MongoDB réussie.")
except ConnectionFailure as e:
    print(f"❌ Erreur de connexion à MongoDB : {e}")
    print("   Vérifiez que le service MongoDB est bien démarré et accessible.")
    exit(1)

db = client[DB_NAME]
fs = gridfs.GridFS(db, collection=BUCKET)
meta = db[META]

def get_wav_duration(audio_bytes: bytes) -> float:
    """Calcule la durée d'un fichier WAV à partir de ses octets bruts."""
    try:
        with io.BytesIO(audio_bytes) as buffer:
            with wave.open(buffer, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                return frames / float(rate) if rate > 0 else 0.0
    except (wave.Error, EOFError):
        # Le fichier peut être corrompu ou incomplet
        return 0.0

def seed(limit: int) -> None:
    """
    Charge le dataset CallHome et insère les données de manière optimisée.
    """
    print("[*] Tentative de chargement du dataset CallHome (cela peut prendre un moment)...")
    try:
        # Étape 1 : Charger le dataset en streaming
        ds = load_dataset("talkbank/callhome", "eng", split="data", streaming=True)

        # Étape 2 (OPTIMISATION EXPERT) : Modifier la colonne audio
        # On demande à `datasets` de ne PAS décoder l'audio en tableau NumPy.
        # Il nous donnera directement les octets {'path': ..., 'bytes': ...}
        # C'est beaucoup plus rapide et économe en mémoire.
        ds = ds.cast_column("audio", Audio(decode=False))
        print("✅ Dataset chargé en mode optimisé (octets bruts).")

    except Exception as e:
        print(f"❌ Échec du chargement du dataset. Assurez-vous d'être connecté à Hugging Face.")
        print(f"   Exécutez 'pip install huggingface_hub' puis 'hf auth login'.")
        print(f"   Erreur système : {e}")
        return

    print(f"[*] Démarrage du traitement de {limit} session(s) audio...")
    cpt = 0
    for sample in tqdm(ds, total=limit, desc="Sessions importées"):
        audio_info = sample.get("audio")
        if not audio_info or not audio_info.get("path") or not audio_info.get("bytes"):
            continue

        uid = os.path.splitext(os.path.basename(audio_info["path"]))[0]

        if meta.find_one({"_id": uid}):
            continue
        
        audio_bytes = audio_info["bytes"]

        # Calculer la durée à partir des octets bruts avec le module standard `wave`
        duration = get_wav_duration(audio_bytes)
        if duration == 0.0:
            # Si la durée est nulle, le fichier est peut-être corrompu, on l'ignore.
            tqdm.write(f"   - Fichier {uid}.wav ignoré (durée nulle ou invalide).")
            continue

        # Stocker les octets directement dans GridFS
        fid = fs.put(audio_bytes, filename=f"{uid}.wav", content_type="audio/wav")
        
        meta.insert_one({
            "_id": uid,
            "language": "eng",
            "duration": duration,
            "file_id": fid,
            "status": "pending",
            "size_bytes": len(audio_bytes)
        })
        
        cpt += 1
        if cpt >= limit:
            break
            
    print(f"\n[+] Terminé. {cpt} nouvelle(s) session(s) insérée(s).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Importer les données CallHome dans MongoDB de manière optimisée.")
    parser.add_argument("--limit", type=int, default=120, help="Nombre max de sessions à importer.")
    args = parser.parse_args()
    seed(args.limit)