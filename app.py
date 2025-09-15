# app_final_sync_pro_v4.py
import streamlit as st
import json
import pandas as pd
import numpy as np
from pymongo import MongoClient
import gridfs
import base64
import altair as alt
import plotly.express as px

# --- CONFIGURATION ET CONNEXION À LA BASE DE DONNÉES ---
st.set_page_config(layout="wide", page_title="CallCenter Dashboard", page_icon="📞")

MONGO_URI = "mongodb://localhost:27017/?replicaSet=rs0"

@st.cache_resource
def get_db_connections():
    """
    Établit les connexions à MongoDB et les met en cache.
    """
    try:
        client = MongoClient(MONGO_URI)
        db_res = client["callcenter"]
        db_audio = client["audioClient"]
        fs_audio = gridfs.GridFS(db_audio, collection="audioClient")
        return client, db_res, fs_audio,db_audio
    except Exception as e:
        st.error(f"Erreur de connexion à la base de données : {e}")
        st.stop()

client, db_res, fs_audio,db_audio = get_db_connections()

# --- GESTION DE L'ÉTAT DE SESSION ---
if "current_time" not in st.session_state:
    st.session_state.current_time = 0.0
if "seek_request" not in st.session_state:
    st.session_state.seek_request = None
if "selected_call_id" not in st.session_state:
    st.session_state.selected_call_id = None

def handle_seek(time_value):
    """
    Met à jour l'état de l'application et force la synchronisation audio.
    """
    st.session_state.seek_request = time_value
    st.session_state.current_time = time_value

# --- SIDEBAR ET SÉLECTION D'APPEL ---
st.sidebar.title("📞 Analyse Sentiments")
try:
    uids = [doc["_id"] for doc in db_res["results"].find({}, {"_id": 1}).sort("_id", 1)]
    if not uids:
        st.sidebar.warning("Aucun appel trouvé dans la base de données.")
        st.stop()
    selected_uid = st.sidebar.selectbox("Choisir un appel", uids, key="call_selector")
except Exception as e:
    st.sidebar.error(f"Erreur lors de la récupération des appels : {e}")
    st.stop()

# --- CHARGEMENT DES DONNÉES DE L'APPEL ---
if selected_uid != st.session_state.selected_call_id:
    st.session_state.selected_call_id = selected_uid
    st.session_state.current_time = 0.0
    st.session_state.seek_request = None
    st.rerun()

res = db_res["results"].find_one({"_id": selected_uid})
if not res:
    st.error("Aucun résultat pour cet ID")
    st.stop()

turns = res["turns"]
score = res["score_result"]["score"]
summary = res["score_result"]["summary"]
insights = res["score_result"]["insights"]
topics = res["score_result"]["topics"]
sentiment_curve = res["score_result"]["sentiment_curve"]
duration = max(t["end"] for t in turns) if turns else 1
st.session_state.duration = duration

audio_doc = db_audio.audioClient.files.find_one({"filename": f"{selected_uid}.wav"})
if not audio_doc:
    st.error(f"Audio non trouvé pour l'ID : {selected_uid}")
    st.stop()

audio_bytes = fs_audio.get(audio_doc["_id"]).read()
audio_b64 = base64.b64encode(audio_bytes).decode()

# --- PLAYER JS AMÉLIORÉ (SANS BOUTONS Streamlit) ---
html_player = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        audio {{width:100%;}}
    </style>
</head>
<body>
    <audio id="player" controls preload="metadata">
        <source src="data:audio/wav;base64,{audio_b64}" type="audio/wav">
    </audio>
    <script>
        const audio = document.getElementById("player");
        
        audio.addEventListener('timeupdate', () => {{
            window.parent.postMessage({{
                type: "streamlit:setComponentValue",
                value: {{ current_time: audio.currentTime }}
            }}, "*");
        }});

        window.addEventListener("message", (e) => {{
            if (e.data.type === "seekAudio") {{
                audio.currentTime = e.data.time;
            }}
        }});
    </script>
</body>
</html>
"""
st.components.v1.html(html_player, height=75)

# --- GESTION DE LA REQUÊTE DE SEEK ---
if st.session_state.seek_request is not None:
    st.components.v1.html(
        f'<script>window.parent.postMessage({{type:"seekAudio",time:{st.session_state.seek_request}}},"*");</script>',
        height=0,
    )
    st.session_state.seek_request = None

player_event_data = st.session_state.get("current_time", {})
if isinstance(player_event_data, dict) and "current_time" in player_event_data:
    st.session_state.current_time = player_event_data["current_time"]

# --- MISE EN PAGE DU DASHBOARD ---
st.markdown("## 📊 Analyse de l'appel")
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Synthèse et Métriques")
    st.metric("Score de l'agent", f"**{score}/100**", help="Score de performance de l'agent basé sur l'analyse de l'appel.")
    st.metric("Client satisfait", "Oui" if res["score_result"]["client_satisfied"] else "Non", help="Évaluation de la satisfaction du client.")
    
    st.markdown("---")
    st.markdown("### 💡 Insights Clés")
    for ins in insights:
        st.info(f"**{ins['timestamp']:.1f}s** – {ins['message']}")
    
    st.markdown("---")
    st.markdown("### 🏷️ Thèmes abordés")
    st.write(", ".join(topics))
    
    st.markdown("---")
    st.markdown("### 📄 Résumé")
    st.write(summary)

with col2:
    st.subheader("📈 Courbe de sentiment et de la forme d'onde")
    
    # Remplacement du graphique Altair par Plotly
    if 'sentiment_curve' in res['score_result'] and res['score_result']['sentiment_curve']:
        sentiment_df = pd.DataFrame(res['score_result']['sentiment_curve'], columns=["t", "sentiment"])
        
        # Création du graphique de la courbe de sentiment avec Plotly Express
        fig_sentiment = px.line(
            sentiment_df,
            x="t",
            y="sentiment",
            title="Courbe de sentiment au fil du temps",
            labels={"t": "Temps (s)", "sentiment": "Sentiment"},
            range_y=[-1, 1]
        )
        st.plotly_chart(fig_sentiment, use_container_width=True)
        
        # Création de l'histogramme de sentiment avec Plotly Express
        st.markdown("---")
        st.markdown("### Distribution des scores de sentiment")
        fig_hist = px.histogram(
            sentiment_df,
            x="sentiment",
            nbins=20, # Nombre de barres dans l'histogramme
            title="Distribution des scores de sentiment",
            labels={"sentiment": "Sentiment", "count": "Fréquence"}
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    else:
        st.warning("Aucune donnée de sentiment disponible pour cet appel.")

    # Création du graphique de la forme d'onde (laissé en Altair car il est parfait pour cette visualisation)
    st.markdown("---")
    samples = 400
    x = np.linspace(0, duration, samples)
    y = np.sin(2 * np.pi * x * 3) + 0.3 * np.random.randn(samples)
    wave_df = pd.DataFrame({"t": x, "amp": y})

    bar = alt.Chart(wave_df).mark_bar(size=2).encode(
        x=alt.X("t:Q", title="Temps (s)", scale=alt.Scale(domain=[0, duration])),
        y=alt.Y("amp:Q", title="Amplitude", axis=None),
        color=alt.condition(alt.datum.t <= st.session_state.current_time, alt.value("#21bf73"), alt.value("#e0e0e0")),
        tooltip=["t"]
    ).properties(height=150).interactive()

    st.altair_chart(bar, use_container_width=True)

# ... (Le reste du code reste inchangé) ...



st.markdown("---")
st.subheader("📝 Transcript en temps réel")
for t in turns:
    role = t["speaker"].capitalize()
    txt = t["text"]
    start, end = t["start"], t["end"]
    
    active = start <= st.session_state.current_time < end
    bg = "#d0ebff" if active else "transparent"
    
    col1, col2 = st.columns([1, 10])
    with col1:
        if st.button(f"**{start:.1f}s**", key=f"seek_{start}"):
            handle_seek(start)
    with col2:
        st.markdown(
            f'<div style="background:{bg};padding:4px;border-radius:4px;">'
            f'<b>{role}</b> : {txt}</div>',
            unsafe_allow_html=True
        )

st.markdown("---")
# --- EXPORTATION ---
export_data = {k: v for k, v in res.items() if k != "audio_bytes"}
st.download_button(
    label="📥 Télécharger le rapport JSON",
    data=json.dumps(export_data, indent=2, ensure_ascii=False, default=str),
    file_name=f"{selected_uid}_report.json",
    mime="application/json"
)

