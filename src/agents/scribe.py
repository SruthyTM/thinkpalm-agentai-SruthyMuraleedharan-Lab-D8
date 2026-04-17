"""
Scribe Agent: Documentation Specialist.
Generates Markdown documentation using tool output and code analysis.
"""
from __future__ import annotations
from langchain_core.messages import SystemMessage, HumanMessage
from src.state import ReviewState
from src.llm import get_llm
from src.tools import SCRIBE_TOOLS

SCRIBE_PROMPT = """You are a Technical Writer.
Your task is to generate comprehensive, professional Markdown documentation for the provided code.
Use the `generate_markdown_skeleton` tool to get the structure.

Then, enhance it by:
1. Adding a 'Review Summary' section based on the Critic's feedback.
2. Explaining HOW to use the code.
3. Adding a 'Security & Performance' section based on the complexity and security scan.

Write in a clean, GitHub-friendly Markdown style.
"""

def scribe_node(state: ReviewState):
    llm = get_llm(tools=tuple(SCRIBE_TOOLS))
    
    context = (
        f"CODE:\n{state['code']}\n\n"
        f"CRITIC REVIEW:\n{state['review']}\n\n"
        f"LINT OUTPUT:\n{state.get('lint_output', 'N/A')}\n\n"
        f"COMPLEXITY:\n{state.get('complexity_report', 'N/A')}"
    )
    
    messages = [
        SystemMessage(content=SCRIBE_PROMPT),
        HumanMessage(content=context)
    ]
    
    response = llm.invoke(messages)
    
    # Handle documentation skeleton tool
    if response.tool_calls:
        from src.tools import generate_markdown_skeleton
        from langchain_core.messages import ToolMessage
        
        tc = response.tool_calls[0]
        skeleton = generate_markdown_skeleton.invoke(tc["args"])
        
        messages.append(response)
        messages.append(ToolMessage(content=skeleton, tool_call_id=tc["id"]))
        
        final_doc = llm.invoke(messages)
        state["docs"] = final_doc.content
    else:
        state["docs"] = response.content
        
    state["steps_completed"].append("scribe")
    return state
