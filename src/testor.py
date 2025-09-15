import os
from graph import app
from models import GlobalState

def test_one(uid: str = "1"):
    print(f"[TEST] Lancement pipeline pour uid = {uid}")
    final_state = app.invoke(GlobalState(uid=uid).dict())
    print("\n[TEST] Résultat final :")
    print(final_state)
    print("\n[TEST] Score :", final_state.get("eval", {}).get("score"))
    print("[TEST] Client satisfait :", final_state.get("eval", {}).get("client_satisfied"))

if __name__ == "__main__":
    
    test_one("17")