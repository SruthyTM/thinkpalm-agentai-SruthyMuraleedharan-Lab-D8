"""
LangGraph Orchestrator.
Defines the DAG (Directed Acyclic Graph) for the pipeline.
"""
from __future__ import annotations
import os
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from src.state import ReviewState
from src.agents.critic import critic_node
from src.agents.scribe import scribe_node
from src.agents.labeler import labeler_node


def create_pipeline():
    """Builds the multi-agent graph."""
    
    # 1. Initialize Graph
    workflow = StateGraph(ReviewState)
    
    # 2. Add Nodes
    workflow.add_node("critic", critic_node)
    workflow.add_node("scribe", scribe_node)
    workflow.add_node("labeler", labeler_node)
    
    # 3. Define Edges (The Flow)
    # Start -> Critic -> Scribe -> Labeler -> End
    workflow.add_edge(START, "critic")
    workflow.add_edge("critic", "scribe")
    workflow.add_edge("scribe", "labeler")
    workflow.add_edge("labeler", END)
    
    # 4. Persistence (Memory)
    db_path = os.getenv("SQLITE_DB_PATH", "./memory/checkpoints.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # We use a direct sqlite3 connection to keep it alive for the FastAPI logic
    import sqlite3
    conn = sqlite3.connect(db_path, check_same_thread=False)
    memory = SqliteSaver(conn)
    
    # 5. Compile
    app = workflow.compile(checkpointer=memory)
    return app

# Singleton-ish instance
pipeline = create_pipeline()
