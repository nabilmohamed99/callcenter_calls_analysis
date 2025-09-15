import io
import numpy as np
import librosa
import soundfile as sf
from pymongo import MongoClient
import gridfs
import noisereduce as nr
from scipy.signal import butter, lfilter

def normalize_audio(audio, target_dBFS=-20):
    mean_amplitude = np.mean(np.abs(audio))
    scaling_factor = 10 ** (target_dBFS / 20) / mean_amplitude
    return np.clip(audio * scaling_factor, -1.0, 1.0)

def high_pass_filter(audio, sr, cutoff=100):
    nyquist = 0.5 * sr
    normal_cutoff = cutoff / nyquist
    b, a = butter(1, normal_cutoff, btype='high', analog=False)
    return lfilter(b, a, audio)

def enhance_audio_bytes(input_bytes):
    y, sr = librosa.load(io.BytesIO(input_bytes), sr=16000)
    reduced_noise = nr.reduce_noise(y=y, sr=sr, prop_decrease=0.8)
    filtered_audio = high_pass_filter(reduced_noise, sr)
    normalized_audio = normalize_audio(filtered_audio)
    boosted_audio = normalized_audio * 1.2

    output_buffer = io.BytesIO()
    sf.write(output_buffer, boosted_audio, sr, format='WAV')
    output_buffer.seek(0)
    return output_buffer

# === Connexion MongoDB ===
client = MongoClient("mongodb://localhost:27017/")

# ⚠️ ACCÈS À LA BONNE BASE : audioClientBase, car c’est elle qui contient fs.files
db_input = client["callcenter"]  # ✅ Ici
db_output = client["audioClient"]     # Base cible pour les résultats

fs_input = gridfs.GridFS(db_input, collection="audio_fs")               # Prend fs.files par défaut

print(client.admin.command("ping"))
fs_output = gridfs.GridFS(db_output, collection="audioClient")  # Résultat

# === Traitement ===
docs = list(fs_input.find())
print(f"🔍 Nombre de fichiers trouvés : {len(docs)}")

if not docs:
    print("❌ Aucun fichier trouvé.")
else:
    count = 19
    for doc in docs:
        try:
            input_data = doc.read()
            processed_wav = enhance_audio_bytes(input_data)

            output_filename = f"{count}.wav"
            if not fs_output.exists({"filename": output_filename}):
                fs_output.put(
                    processed_wav,
                    filename=output_filename,
                    metadata={
                        "original_id": str(doc._id),
                        "original_filename": doc.filename
                    }
                )
                print(f"✅ Stocké : {output_filename}")
                count += 1
            else:
                print(f"⚠️ {output_filename} déjà existant.")
        except Exception as e:
            print(f"❌ Erreur sur {doc.filename} : {e}")

    print(f"\n🎯 Total traité et stocké : {count - 1}")
