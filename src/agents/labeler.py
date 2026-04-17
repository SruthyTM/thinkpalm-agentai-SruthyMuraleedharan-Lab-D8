"""
Labeler Agent: The Final Verdict.
Categorizes the code review outcome.
"""
from __future__ import annotations
from langchain_core.messages import SystemMessage, HumanMessage
from src.state import ReviewState
from src.llm import get_llm

LABELER_PROMPT = """You are the Lead Release Engineer and Quality Assurance Director.
Your role is to synthesize the findings from the Critic and Scribe agents to provide a final governance verdict.

Decision Framework:
- SAFE: The code exhibits no critical security vulnerabilities, maintains a manageable cyclomatic complexity (< 10), and has sufficient documentation and type hinting.
- NEEDS WORK: Any security risk, excessive complexity (> 10), deprecated libraries, or lack of essential documentation must trigger this status.

OUTPUT SPECIFICATION:
Your response must be structured as follows:
VERDICT: [Safe / Needs Work]
REASON: [A one-sentence summary of the primary justification for this decision]
"""

def labeler_node(state: ReviewState):
    llm = get_llm() # No tools needed
    
    context = (
        f"CRITIC REVIEW:\n{state['review']}\n\n"
        f"LINT OUTPUT:\n{state.get('lint_output', '')}\n\n"
        f"DOCS GENERATED:\n{state['docs']}"
    )
    
    messages = [
        SystemMessage(content=LABELER_PROMPT),
        HumanMessage(content=context)
    ]
    
    response = llm.invoke(messages)
    content = response.content
    
    # Extract verdict and reason
    import re
    verdict_match = re.search(r"VERDICT:\s*(Safe|Needs Work)", content, re.IGNORECASE)
    reason_match = re.search(r"REASON:\s*(.*)", content, re.IGNORECASE)
    
    state["label"] = verdict_match.group(1) if verdict_match else "Unclear"
    state["label_reason"] = reason_match.group(1).strip() if reason_match else content
    
    state["steps_completed"].append("labeler")
    return state
