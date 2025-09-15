from langgraph.graph import StateGraph, END
from nodes.ingest import ingest_node
from nodes.vad_diar_role import vad_diar_role_node
from nodes.score_analyst import  score_analyst_node
from nodes.sink import sink_node
from models import GlobalState

def build_graph():
    g = StateGraph(GlobalState)
    g.add_node("ingest", ingest_node)
    g.add_node("vad_diar", vad_diar_role_node)
    g.add_node("score", score_analyst_node)
    g.add_edge("ingest", "vad_diar")
    g.add_edge("vad_diar", "score")
    g.add_node("sink", sink_node)
    g.add_edge("score", "sink")
    g.add_edge("sink", END)
  
    g.set_entry_point("ingest")
    return g.compile()

app = build_graph()