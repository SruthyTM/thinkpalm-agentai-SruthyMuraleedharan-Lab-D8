"""
Critic Agent: The first line of defense.
Reviews code using static tools and provides a narrative review.
"""
from __future__ import annotations
from langchain_core.messages import SystemMessage, HumanMessage
from src.state import ReviewState
from src.llm import get_llm
from src.tools import CRITIC_TOOLS

# System prompt for the Critic
CRITIC_PROMPT = """You are an Elite Python Security Architect and Quality Auditor.
Your mandate is to perform an exhaustive evaluation of the submitted source code.

Audit Parameters:
1. SECURITY: Identify vulnerabilities, secret leakage, or dangerous execution patterns.
2. EFFICIENCY: Detect algorithmic inefficiencies, deep nesting, or high cyclomatic complexity.
3. QUALITY: Evaluate adherence to PEP 8, presence of type hints, and documentation sufficiency.
4. DEPENDENCIES: Flag deprecated modules or risky external imports.

PROTOCOL:
- MANDATORY: Execute ALL your tools (`python_linter`, `complexity_checker`, `security_scanner`, `dependency_check`) before providing a verdict.
- EVIDENCE-BASED: Cite specific line numbers from the tool outputs.
- CONSTRUCTIVE: Provide actionable advice for every issue identified.
- SUMMARY: Conclude with a clear perspective on whether the code is production-ready.
"""

def critic_node(state: ReviewState):
    """
    Node that runs the Critic agent.
    1. Prepares the history.
    2. Calls tools (via the LLM logic + LangGraph ToolNode later, or directly here simplified).
    
    In a standard LangGraph React pattern, the agent just decides what tools to call.
    To keep this project straightforward, we'll use a functional approach:
    The LLM is called with tools bound.
    """
    llm = get_llm(tools=tuple(CRITIC_TOOLS))
    
    # Construct prompt
    messages = [
        SystemMessage(content=CRITIC_PROMPT),
        HumanMessage(content=f"Please review this code:\n\n{state['code']}")
    ]
    
    # We call the LLM. It may return ToolCalls.
    # To handle the loop nicely, we'll let LangGraph's standard tool-calling pattern handle it 
    # OR we can execute tools here for one-shot. 
    # Let's use the one-shot simplified pattern for this starter-friendly project 
    # but still use real tool-calling logic.
    
    response = llm.invoke(messages)
    
    # If the LLM wants to call tools, we handle them.
    tool_results = []
    if response.tool_calls:
        for tool_call in response.tool_calls:
            # Map name to tool function
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Simple dispatcher
            from src.tools import python_linter, complexity_checker, security_scanner, dependency_check
            if tool_name == "python_linter":
                res = python_linter.invoke(tool_args)
                state["lint_output"] = res
            elif tool_name == "complexity_checker":
                res = complexity_checker.invoke(tool_args)
                state["complexity_report"] = res
            elif tool_name == "security_scanner":
                res = security_scanner.invoke(tool_args)
            elif tool_name == "dependency_check":
                res = dependency_check.invoke(tool_args)
            
            tool_results.append(f"Tool {tool_name} outcome: {res}")
            
        # Re-invoke LLM with tool outputs to get final text review
        messages.append(response)
        for tc in response.tool_calls:
            # We add ToolMessages here usually, but keeping it simple for now:
            from langchain_core.messages import ToolMessage
            # Find the result we just computed
            # (Just mapping to 'res' from the loop above for simplicity)
            messages.append(ToolMessage(content=str(res), tool_call_id=tc["id"]))
            
        final_response = llm.invoke(messages)
        state["review"] = final_response.content
    else:
        state["review"] = response.content

    state["steps_completed"].append("critic")
    return state
