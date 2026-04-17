"""
LLM factory – returns a ChatOpenAI or ChatAnthropic instance
depending on the LLM_PROVIDER env variable.
"""
from __future__ import annotations
import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


def get_llm(tools: tuple = ()):
    """
    Build and return the configured chat model.
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    base_url = os.getenv("OPENROUTER_BASE_URL")

    if provider in ("openai", "openrouter"):
        from langchain_openai import ChatOpenAI
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # If openrouter is used, we often need the base_url
        kwargs = {"model": model_name, "temperature": 0}
        if base_url:
            kwargs["base_url"] = base_url
            
        llm = ChatOpenAI(**kwargs)
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        model_name = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
        llm = ChatAnthropic(model=model_name, temperature=0)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}. Use 'openai' or 'anthropic'.")

    if tools:
        llm = llm.bind_tools(list(tools))

    return llm


def get_llm_plain() -> object:
    """Return an LLM with no tools bound (used by Scribe and Labeler)."""
    return get_llm(tools=())
