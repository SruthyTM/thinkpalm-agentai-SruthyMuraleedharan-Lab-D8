"""
FastAPI Server – The 'Face' of the Pipeline.
"""
from __future__ import annotations
import uuid
import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from dotenv import load_dotenv

from fastapi.middleware.cors import CORSMiddleware
from src.graph import pipeline

load_dotenv()

app = FastAPI(
    title="CodeNexus PR Assistant",
    description="Multi-agent pipeline using LangGraph",
    version="2.0.0"
)

# ── CORS Middleware ────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Models ──────────────────────────────────────────

class ReviewRequest(BaseModel):
    code: str
    filename: Optional[str] = "main.py"
    thread_id: Optional[str] = None

class ReviewResponse(BaseModel):
    thread_id: str
    label: str
    reason: str
    review: str
    docs: str
    steps_completed: list[str]

# ── Endpoints ───────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "message": "GitHub PR Assistant is online.",
        "docs_url": "/docs",
        "instructions": "Send a POST request to /review with your code."
    }

@app.post("/review", response_model=ReviewResponse)
async def run_review(req: ReviewRequest):
    """
    Triggers the multi-agent pipeline for a code snippet.
    """
    # 1. Setup ID and Initial State
    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_state = {
        "code": req.code,
        "filename": req.filename,
        "thread_id": thread_id,
        "steps_completed": [],
        "messages": []
    }
    
    # 2. Execute Graph
    try:
        # We use .invoke which runs to completion
        result = pipeline.invoke(initial_state, config=config)
        
        # 3. Return aggregated results
        return ReviewResponse(
            thread_id=thread_id,
            label=result.get("label", "Unknown"),
            reason=result.get("label_reason", ""),
            review=result.get("review", ""),
            docs=result.get("docs", ""),
            steps_completed=result.get("steps_completed", [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{thread_id}")
async def get_history(thread_id: str):
    """
    Retrieve the last saved state for a specific thread.
    """
    config = {"configurable": {"thread_id": thread_id}}
    state = pipeline.get_state(config)
    
    if not state.values:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    return state.values

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
