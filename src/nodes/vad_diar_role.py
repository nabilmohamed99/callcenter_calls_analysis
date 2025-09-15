import json
import os
import tempfile
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from models import GlobalState, Turn

API_KEY = "AIzaSyBdw7cBELrnqL5ydoHwXd0XjWjV_Nfi_w0"
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=API_KEY, temperature=0)

SYS = """You are a call-center audio analyst.
1. Remove music, IVR, silence.
2. Split into turns (start/end in seconds, 0.1 s precision).
3. Assign role "agent" or "client".
4. Output strict JSON:
[{"start":1.2,"end":4.8,"speaker":"agent","text":"..."},...]"""

def vad_diar_role_node(state: GlobalState) -> GlobalState:
    print("vad_diar_role a commencé")
    temp_path = None
    try:
        # Écrire les bytes audio dans un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(state.audio_bytes)
            temp_path = temp_file.name

        with open("test.wav","wb") as f:
            f.write(state.audio_bytes)

        print(f"Fichier audio temporaire créé : {temp_path}")

        # Préparer le message avec l'audio
        message = HumanMessage(
            content=[
                {"type": "text", "text": SYS},
                {"type": "media", "mime_type": "audio/wav", "data": open(temp_path, "rb").read()}
            ]
        )

        # Appeler le modèle
        msg = llm.invoke([message])
        
        print("Réponse du modèle reçue")
        print(msg.content)

        # Nettoyer le JSON
        json_output = msg.content.strip()
        if json_output.startswith("```json"):
            json_output = json_output[7:-3].strip()

        turns = [Turn(**t) for t in json.loads(json_output)]
        return GlobalState(**{**state.model_dump(), "turns": turns})

    except Exception as e:
        print(f"Erreur dans vad_diar_role : {e}")
        raise

    finally:
        # Nettoyage du fichier temporaire
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
            print(f"Fichier temporaire supprimé : {temp_path}")