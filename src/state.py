"""
Shared State for the PR Review Pipeline.

Every agent reads from and writes to this TypedDict.
LangGraph merges partial updates via the `add_messages` / plain-dict reducer.
"""
from __future__ import annotations
from typing import Annotated, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ReviewState(TypedDict):
    """Shared clipboard that flows through every agent node."""

    # ── Input ──────────────────────────────────────────────
    code: str                          # Raw source code submitted by the user
    filename: str                      # Optional filename hint (e.g. "main.py")
    thread_id: str                     # Conversation / PR thread identifier

    # ── Agent outputs ──────────────────────────────────────
    lint_output: Optional[str]         # Raw output from the linter tool
    complexity_report: Optional[str]   # Cyclomatic-complexity report
    review: Optional[str]              # Critic agent's narrative review
    docs: Optional[str]                # Scribe agent's generated Markdown docs
    label: Optional[str]               # Labeler final verdict: "Safe" | "Needs Work"
    label_reason: Optional[str]        # Short explanation for the verdict

    # ── Conversation history (supports multi-turn follow-ups) ──
    messages: Annotated[List[BaseMessage], add_messages]

    # ── Pipeline metadata ──────────────────────────────────
    error: Optional[str]               # Any pipeline-level error message
    steps_completed: List[str]         # Audit trail of finished agent names
