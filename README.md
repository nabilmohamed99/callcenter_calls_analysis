# 📞 Call Center QA - Gemini Edition

> **One-shot seed → GridFS → Gemini 1.5 Pro → Streamlit GUI • CPU only • Zero config**

---

## 🎯 What You Get

* Upload any WAV file for **automatic transcription** (agent vs. client)
* Receive a **quality score**, **summary**, **insights**, and a **sentiment curve**
* **Fully containerized**—one command gets everything running
* **100% CPU**—no GPU, no quotas, and no cloud key required

---

## 🧠 Tech Stack (CPU 6 GB RAM)

| Layer | Tool | Purpose |
| :--- | :--- | :--- |
| **VAD** | Whisper-base | Segment speech |
| **Transcription** | Gemini 1.5 Pro | Transcribe + diarize |
| **Evaluation** | Gemini 1.5 Pro | Score, summary, insights |
| **GUI** | Streamlit | Sync player + waveform |
| **Storage** | MongoDB GridFS | Audio + metadata |

---

## 🚀 Quick Start (CPU only)

```bash
# 1. Clone repo
git clone [https://github.com/YOU/callcenter-gemini-cpu.git](https://github.com/YOU/callcenter-gemini-cpu.git)
cd callcenter-gemini-cpu

# 2. Start Mongo + app
docker compose up --build -d

# 3. Seed 20 calls (one time only)
python 01_seed_callhome.py --limit 20

# 4. Launch the interface
streamlit run app_final_safe.py
Browse → http://localhost:8501
