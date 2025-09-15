import json, os
from langchain_google_genai import ChatGoogleGenerativeAI
from models import GlobalState, ScoreResult, Insight
API_KEY = "AIzaSyBdw7cBELrnqL5ydoHwXd0XjWjV_Nfi_w0"
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=API_KEY, temperature=0)


PROMPT = """
You receive a call-center conversation with timestamps.
1. Score agent 0-100 (politeness, solution, empathy).
2. Client satisfied ? bool.
3. 20-word summary.
4. 3 actionable insights (with timestamps).
5. Topics (max 3).
6. Sentiment curve (1 point every 30 s).

Output JSON only:
{
  "score": 87,
  "client_satisfied": true,
  "summary": "...",
  "insights": [{"timestamp": 45.2, "message": "reduce hold time"}],
  "topics": ["billing", "refund"],
  "sentiment_curve": [{"t": 0, "sentiment": "negative"}, ...]
}
"""

def score_analyst_node(state: GlobalState) -> GlobalState:
    print('######################')
    print("je suis ici")
    turns_json = json.dumps([t.model_dump() for t in state.turns], ensure_ascii=False)
    msg = llm.invoke([{"role": "user", "content": PROMPT + "\n\nConversation:\n" + turns_json}])
    raw = msg.content.strip()
    if raw.startswith("```json"): 
        raw = raw[7:-3].strip()
    print(raw)
    print("le row")
    result = ScoreResult(**json.loads(raw))
    return GlobalState(**{**state.model_dump(), "score_result": result})