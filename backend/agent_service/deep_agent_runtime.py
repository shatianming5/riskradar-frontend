from __future__ import annotations

from functools import lru_cache

from .config import get_settings
from .tools import load_reference_doc, run_rule_engine, validate_output_contract


@lru_cache(maxsize=1)
def get_deep_agent_supervisor():
    """Create a Deep Agents supervisor harness for production LLM execution.

    The LangGraph pipeline in graph.py owns the deterministic state machine.
    This harness is initialized to provide the Deep Agents planning/subagent
    layer when OPENAI_API_KEY is configured. Tests and offline demos can run
    without it.
    """

    settings = get_settings()
    if not settings.llm_enabled:
        return None
    try:
        from deepagents import create_deep_agent
    except Exception:
        return None

    subagents = [
        {
            "name": "investigator-agent",
            "description": "Extracts structured risk signals from user financial text.",
            "system_prompt": "You are RiskRadar's Investigator Agent. Extract only evidence grounded in user text.",
            "tools": [load_reference_doc],
        },
        {
            "name": "risk-officer-agent",
            "description": "Runs the deterministic scoring engine and explains matched rules.",
            "system_prompt": "You are RiskRadar's Risk Officer. Always use run_rule_engine for score and level.",
            "tools": [run_rule_engine, load_reference_doc],
        },
        {
            "name": "red-team-agent",
            "description": "Anticipates manipulation, pressure, and follow-up scam paths.",
            "system_prompt": "You are RiskRadar's Red Team Agent. Do not create new facts.",
            "tools": [load_reference_doc],
        },
        {
            "name": "coach-agent",
            "description": "Creates calm questions, safe actions, and a copy-ready reply template.",
            "system_prompt": "You are RiskRadar's Coach Agent. Keep advice concrete and non-investment-specific.",
            "tools": [load_reference_doc],
        },
        {
            "name": "compliance-agent",
            "description": "Checks output contract and safety boundaries.",
            "system_prompt": "You are RiskRadar's Compliance Agent. Rewrite absolute and unsafe language.",
            "tools": [validate_output_contract, load_reference_doc],
        },
    ]

    return create_deep_agent(
        model=settings.openai_model,
        tools=[run_rule_engine, load_reference_doc, validate_output_contract],
        subagents=subagents,
        system_prompt=(
            "You are the RiskRadar Orchestrator Agent. Follow the local SKILL.md, "
            "delegate to specialized subagents, and never invent risk scores. "
            "Risk score and level must come from run_rule_engine."
        ),
        name="riskradar-orchestrator",
    )
