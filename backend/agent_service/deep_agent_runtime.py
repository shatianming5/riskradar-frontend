from __future__ import annotations

from functools import lru_cache
import json
from typing import Any

from .config import get_settings
from .paths import REPO_ROOT
from .tools import load_reference_doc, run_rule_engine, validate_output_contract


SKILL_SOURCE_PATH = "/backend"
SKILL_NAME = "risk-radar-finance-control"


@lru_cache(maxsize=1)
def get_deep_agent_supervisor():
    """Create a Deep Agents supervisor harness for production LLM execution.

    The LangGraph pipeline in graph.py owns the deterministic state machine.
    This harness provides the Deep Agents planning/subagent layer when
    OPENAI_API_KEY is configured. Tests and offline demos can run without it.
    """

    settings = get_settings()
    if not settings.llm_enabled:
        return None
    try:
        from deepagents.backends import FilesystemBackend
        from deepagents import create_deep_agent
        from deepagents.middleware.filesystem import FilesystemPermission
    except Exception:
        return None

    skill_sources = [SKILL_SOURCE_PATH]
    permissions = [
        FilesystemPermission(
            operations=["read"],
            paths=["/backend/risk-radar-finance-control/**"],
            mode="allow",
        ),
        FilesystemPermission(operations=["read"], paths=["/**"], mode="deny"),
        FilesystemPermission(operations=["write"], paths=["/**"], mode="deny"),
    ]
    backend = FilesystemBackend(root_dir=REPO_ROOT, virtual_mode=True)

    subagents = [
        {
            "name": "investigator-agent",
            "description": "Extracts structured risk signals from user financial text.",
            "system_prompt": (
                "You are RiskRadar's Investigator Agent. Use the "
                f"{SKILL_NAME} skill before analyzing. Extract only evidence grounded in user text."
            ),
            "tools": [load_reference_doc],
            "skills": skill_sources,
            "permissions": permissions,
        },
        {
            "name": "risk-officer-agent",
            "description": "Runs the deterministic scoring engine and explains matched rules.",
            "system_prompt": (
                "You are RiskRadar's Risk Officer. Use the "
                f"{SKILL_NAME} skill and always use run_rule_engine for score and level."
            ),
            "tools": [run_rule_engine, load_reference_doc],
            "skills": skill_sources,
            "permissions": permissions,
        },
        {
            "name": "red-team-agent",
            "description": "Anticipates manipulation, pressure, and follow-up scam paths.",
            "system_prompt": (
                "You are RiskRadar's Red Team Agent. Use the "
                f"{SKILL_NAME} skill. Do not create new facts."
            ),
            "tools": [load_reference_doc],
            "skills": skill_sources,
            "permissions": permissions,
        },
        {
            "name": "coach-agent",
            "description": "Creates calm questions, safe actions, and a copy-ready reply template.",
            "system_prompt": (
                "You are RiskRadar's Coach Agent. Use the "
                f"{SKILL_NAME} skill. Keep advice concrete and non-investment-specific."
            ),
            "tools": [load_reference_doc],
            "skills": skill_sources,
            "permissions": permissions,
        },
        {
            "name": "compliance-agent",
            "description": "Checks output contract and safety boundaries.",
            "system_prompt": (
                "You are RiskRadar's Compliance Agent. Use the "
                f"{SKILL_NAME} skill. Rewrite absolute and unsafe language."
            ),
            "tools": [validate_output_contract, load_reference_doc],
            "skills": skill_sources,
            "permissions": permissions,
        },
    ]

    return create_deep_agent(
        model=settings.openai_model,
        tools=[run_rule_engine, load_reference_doc, validate_output_contract],
        subagents=subagents,
        skills=skill_sources,
        backend=backend,
        permissions=permissions,
        system_prompt=(
            f"You are the RiskRadar Orchestrator Agent. Use the {SKILL_NAME} skill "
            "through the Deep Agents Skills System before delegating. Delegate to "
            "specialized subagents and never invent risk scores. Risk score and "
            "level must come from run_rule_engine."
        ),
        name="riskradar-orchestrator",
    )


def run_deep_agent_handoff(request_payload: dict[str, Any]) -> dict[str, Any]:
    """Run a lightweight Deep Agents handoff so skill-aware planning is real.

    The response is only used for traceability. The deterministic LangGraph
    pipeline still owns all API output, and run_rule_engine remains the only
    source of score and level.
    """

    supervisor = get_deep_agent_supervisor()
    if supervisor is None:
        return {
            "enabled": False,
            "summary": "OPENAI_API_KEY 未配置或 Deep Agents 依赖不可用，跳过 Deep Agents LLM handoff。",
        }

    instruction = {
        "task": (
            "作为 RiskRadar Orchestrator 做一次调度 handoff。必须使用 Skills System 中的 "
            f"{SKILL_NAME} skill；只返回调度计划，不要输出最终分数，不要替代 run_rule_engine。"
        ),
        "expected_agents": [
            "investigator-agent",
            "risk-officer-agent",
            "red-team-agent",
            "coach-agent",
            "compliance-agent",
        ],
        "request": request_payload,
    }
    result = supervisor.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": json.dumps(instruction, ensure_ascii=False, indent=2),
                }
            ]
        }
    )
    messages = result.get("messages", []) if isinstance(result, dict) else []
    summary = ""
    for message in reversed(messages):
        content = getattr(message, "content", "")
        if isinstance(content, str) and content.strip():
            summary = content.strip()
            break
    return {
        "enabled": True,
        "summary": summary[:500] if summary else f"Deep Agents 已加载 {SKILL_NAME} skill 并完成调度 handoff。",
    }
