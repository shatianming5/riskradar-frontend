from __future__ import annotations

from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from .deep_agent_runtime import get_deep_agent_supervisor
from .fallbacks import fallback_coach, fallback_investigation, fallback_red_team
from .llm import LLMUnavailable, invoke_structured
from .prompts import COACH_PROMPT, COMPLIANCE_PROMPT, INVESTIGATOR_PROMPT, RED_TEAM_PROMPT
from .schemas import (
    AgentTraceItem,
    AnalyzeResponse,
    CoachResult,
    ComplianceResult,
    GraphState,
    InvestigationResult,
    RedTeamResult,
)
from .tools import load_reference_doc, run_rule_engine, select_reference_names, validate_output_contract


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("investigator", investigator_node)
    graph.add_node("risk_officer", risk_officer_node)
    graph.add_node("red_team", red_team_node)
    graph.add_node("coach", coach_node)
    graph.add_node("compliance", compliance_node)

    graph.add_edge(START, "orchestrator")
    graph.add_conditional_edges(
        "orchestrator",
        should_continue_after_orchestrator,
        {"investigator": "investigator", "compliance": "compliance"},
    )
    graph.add_edge("investigator", "risk_officer")
    graph.add_edge("risk_officer", "red_team")
    graph.add_edge("red_team", "coach")
    graph.add_edge("coach", "compliance")
    graph.add_edge("compliance", END)
    return graph.compile()


def orchestrator_node(state: GraphState) -> dict[str, Any]:
    request = state.request
    skill = load_reference_doc("SKILL")
    questions = _follow_up_questions(request.model_dump())
    needs_follow_up = len(questions) > 0
    trace = [
        *state.agent_trace,
        AgentTraceItem(
            agent="Orchestrator Agent",
            action="调度分析流程",
            summary="已读取 SKILL.md；决定是否需要追问，并准备调用 Investigator / Risk Officer / Red Team / Coach / Compliance。",
            tool_calls=["load_reference_doc(SKILL)"],
        ),
    ]

    if needs_follow_up:
        return {
            "skill_summary": skill[:1800],
            "needs_follow_up": True,
            "follow_up_questions": questions,
            "agent_trace": trace,
        }

    # Initialize the Deep Agents supervisor when available. LangGraph remains
    # the deterministic service orchestrator; Deep Agents provides the LLM
    # planning/subagent harness.
    supervisor = get_deep_agent_supervisor()
    if supervisor is not None:
        trace.append(
            AgentTraceItem(
                agent="Orchestrator Agent",
                action="初始化 Deep Agents harness",
                summary="Deep Agents supervisor 已就绪；后续节点可使用 LLM 结构化输出。",
                tool_calls=["create_deep_agent"],
            )
        )

    return {"skill_summary": skill[:1800], "agent_trace": trace}


def should_continue_after_orchestrator(state: GraphState) -> Literal["investigator", "compliance"]:
    return "compliance" if state.needs_follow_up else "investigator"


def investigator_node(state: GraphState) -> dict[str, Any]:
    request_payload = state.request.model_dump()
    try:
        investigation = invoke_structured(
            InvestigationResult,
            system_prompt=_with_skill(INVESTIGATOR_PROMPT, state.skill_summary, {}),
            user_payload=request_payload,
        )
        summary = "LLM 已提取场景、实体、渠道、证据和风险特征。"
        tool_calls = ["deepagents/investigator-agent"]
    except (LLMUnavailable, Exception):
        investigation = fallback_investigation(request_payload)
        summary = "未启用 LLM，使用规则引擎前置字段和后续确定性检测。"
        tool_calls = ["fallback_investigation"]

    merged = _merge_request_and_investigation(request_payload, investigation)
    refs = {
        name: load_reference_doc(name)
        for name in select_reference_names(investigation.scene, investigation.features, state.request.input_text)
    }
    return {
        "investigation": investigation,
        "selected_references": refs,
        "agent_trace": [
            *state.agent_trace,
            AgentTraceItem(
                agent="Investigator Agent",
                action="结构化抽取",
                summary=summary,
                tool_calls=[*tool_calls, "load_reference_doc(progressive)"],
            ),
        ],
        # Store merged payload as a private bridge field inside rule_result until
        # risk_officer_node replaces it with the actual rule result.
        "rule_result": {"_payload": merged},
    }


def risk_officer_node(state: GraphState) -> dict[str, Any]:
    payload = dict(state.rule_result.get("_payload", {}))
    result = run_rule_engine(payload)
    matched = result.get("matched_rules", [])
    return {
        "rule_result": result,
        "agent_trace": [
            *state.agent_trace,
            AgentTraceItem(
                agent="Risk Officer Agent",
                action="确定性规则评分",
                summary=f"已调用 risk_score.py；规则引擎输出 {result.get('level')} / {result.get('score')}/100，命中 {len(matched)} 条规则。",
                tool_calls=["run_rule_engine"],
            ),
        ],
    }


def red_team_node(state: GraphState) -> dict[str, Any]:
    payload = {
        "rule_result": state.rule_result,
        "selected_references": _compact_refs(state.selected_references),
    }
    try:
        red_team = invoke_structured(RedTeamResult, system_prompt=RED_TEAM_PROMPT, user_payload=payload)
        summary = "LLM 已推演后续诱导路径和操控信号。"
        tool_calls = ["deepagents/red-team-agent"]
    except (LLMUnavailable, Exception):
        red_team = fallback_red_team(state.rule_result)
        summary = "未启用 LLM，使用规则命中生成红队推演。"
        tool_calls = ["fallback_red_team"]

    return {
        "red_team": red_team,
        "agent_trace": [
            *state.agent_trace,
            AgentTraceItem(
                agent="Red Team Agent",
                action="诱导路径推演",
                summary=summary,
                tool_calls=tool_calls,
            ),
        ],
    }


def coach_node(state: GraphState) -> dict[str, Any]:
    payload = {
        "rule_result": state.rule_result,
        "red_team": state.red_team.model_dump() if state.red_team else {},
        "selected_references": _compact_refs(state.selected_references),
    }
    try:
        coach = invoke_structured(CoachResult, system_prompt=COACH_PROMPT, user_payload=payload)
        summary = "LLM 已生成三问冷静卡、行动建议和安全回复模板。"
        tool_calls = ["deepagents/coach-agent"]
    except (LLMUnavailable, Exception):
        coach = fallback_coach(state.rule_result)
        summary = "未启用 LLM，使用规则场景生成行动建议。"
        tool_calls = ["fallback_coach"]

    coach.calm_questions = _ensure_three(coach.calm_questions, fallback_coach(state.rule_result).calm_questions)
    coach.next_actions = _ensure_range(coach.next_actions, fallback_coach(state.rule_result).next_actions, 3, 5)
    if not coach.safe_reply_template:
        coach.safe_reply_template = fallback_coach(state.rule_result).safe_reply_template

    return {
        "coach": coach,
        "agent_trace": [
            *state.agent_trace,
            AgentTraceItem(
                agent="Coach Agent",
                action="行动建议生成",
                summary=summary,
                tool_calls=tool_calls,
            ),
        ],
    }


def compliance_node(state: GraphState) -> dict[str, Any]:
    if state.needs_follow_up:
        response = AnalyzeResponse(
            risk_level="低风险",
            risk_score=0,
            scenario="信息不足",
            reasoning_basis=["[核验状态] 当前信息不足，先追问最多 3 个关键问题。"],
            evidence_or_gaps=state.follow_up_questions,
            calm_questions=state.follow_up_questions[:3],
            next_actions=["先补充关键信息，不要在信息不足时付款、借贷或下单。"],
            safe_reply_template="我需要先核验关键信息，暂时不会付款、下单或提供任何敏感资料。",
            agent_trace=state.agent_trace,
            needs_follow_up=True,
            follow_up_questions=state.follow_up_questions,
        )
        return {"final_response": validate_output_contract(response)}

    rule = state.rule_result
    coach = state.coach or fallback_coach(rule)
    red_team = state.red_team or fallback_red_team(rule)
    reasoning = _reasoning_basis(rule, red_team)
    evidence_or_gaps = _evidence_or_gaps(rule)

    payload = {
        "risk_level": rule.get("level"),
        "risk_score": rule.get("score"),
        "scenario": rule.get("scene"),
        "reasoning_basis": reasoning,
        "evidence_or_gaps": evidence_or_gaps,
        "calm_questions": coach.calm_questions,
        "next_actions": coach.next_actions,
        "safe_reply_template": coach.safe_reply_template,
        "red_team": red_team.model_dump(),
        "selected_references": _compact_refs(state.selected_references),
    }

    try:
        compliance = invoke_structured(ComplianceResult, system_prompt=COMPLIANCE_PROMPT, user_payload=payload)
        reasoning = compliance.reasoning_basis
        evidence_or_gaps = compliance.evidence_or_gaps
        coach = CoachResult(
            calm_questions=compliance.calm_questions,
            next_actions=compliance.next_actions,
            safe_reply_template=compliance.safe_reply_template,
        )
        summary = "Compliance Agent 已检查输出契约、安全边界和克制表述。"
        tool_calls = ["deepagents/compliance-agent", "validate_output_contract"]
    except (LLMUnavailable, Exception):
        summary = "未启用 LLM，使用本地合规规则清洗输出。"
        tool_calls = ["validate_output_contract"]

    trace = [
        *state.agent_trace,
        AgentTraceItem(
            agent="Compliance Agent",
            action="合规与输出契约检查",
            summary=summary,
            tool_calls=tool_calls,
        ),
    ]

    response = AnalyzeResponse(
        risk_level=rule.get("level", "低风险"),
        risk_score=int(rule.get("score", 0)),
        scenario=rule.get("scene", "转账付款"),
        reasoning_basis=reasoning,
        evidence_or_gaps=evidence_or_gaps,
        calm_questions=coach.calm_questions,
        next_actions=coach.next_actions,
        safe_reply_template=coach.safe_reply_template,
        agent_trace=trace,
        matched_rules=rule.get("matched_rules", []),
        features=rule.get("features", {}),
        summary=_summary(rule),
    )
    return {"final_response": validate_output_contract(response)}


def analyze(request) -> AnalyzeResponse:
    graph = build_graph()
    initial = GraphState(request=request)
    result = graph.invoke(initial)
    final = result.get("final_response") if isinstance(result, dict) else result.final_response
    if isinstance(final, AnalyzeResponse):
        return final
    return AnalyzeResponse.model_validate(final)


def _follow_up_questions(payload: dict[str, Any]) -> list[str]:
    text = (payload.get("input_text") or "").strip()
    if len(text) >= 10:
        return []
    questions = [
        "对方是谁，收款主体或产品主体是什么？",
        "是否要求先交钱、跳出官方平台、发送验证码或开启屏幕共享？",
        "这笔钱的用途、金额、渠道和是否必须立刻操作分别是什么？",
    ]
    return questions[:3]


def _with_skill(prompt: str, skill_summary: str, references: dict[str, str]) -> str:
    refs = "\n\n".join(f"## {name}\n{content[:1800]}" for name, content in references.items())
    return f"{prompt}\n\n## SKILL.md 摘要\n{skill_summary[:1800]}\n\n{refs}".strip()


def _merge_request_and_investigation(request_payload: dict[str, Any], investigation: InvestigationResult) -> dict[str, Any]:
    profile = {
        "user_type": "student" if request_payload.get("is_student", True) else "young_user",
        "first_time_trade": bool(request_payload.get("first_time_trade", False)),
    }
    return {
        "input_text": request_payload.get("input_text"),
        "amount": investigation.amount or request_payload.get("amount"),
        "receiver": investigation.receiver or request_payload.get("receiver"),
        "claimed_entity": investigation.claimed_entity or request_payload.get("claimed_entity"),
        "channel": investigation.channel or request_payload.get("channel"),
        "scene": investigation.scene or None,
        "profile": profile,
        "features": investigation.features,
        "evidence": investigation.evidence,
    }


def _compact_refs(references: dict[str, str]) -> dict[str, str]:
    return {name: content[:1600] for name, content in references.items()}


def _ensure_three(items: list[str], fallback: list[str]) -> list[str]:
    merged = [item for item in [*items, *fallback] if item]
    deduped = list(dict.fromkeys(merged))
    return deduped[:3]


def _ensure_range(items: list[str], fallback: list[str], minimum: int, maximum: int) -> list[str]:
    merged = [item for item in [*items, *fallback] if item]
    deduped = list(dict.fromkeys(merged))
    while len(deduped) < minimum:
        deduped.append("先暂停操作，并通过官方渠道补充核验。")
    return deduped[:maximum]


def _reasoning_basis(rule: dict[str, Any], red_team: RedTeamResult) -> list[str]:
    matched = rule.get("matched_rules", [])
    basis = [
        f"[{item.get('tag', '规则命中')}] {item.get('reason', item.get('key', '命中风险规则'))}"
        for item in matched[:4]
    ]
    for note in red_team.notes[:1]:
        basis.append(f"[红队推演] {note}")
    if not basis:
        basis.append("[核验状态] 未命中明显高危规则，但仍需保持官方渠道核验。")
    return basis[:5]


def _evidence_or_gaps(rule: dict[str, Any]) -> list[str]:
    evidence = [str(item) for item in rule.get("evidence", []) if str(item).strip()]
    if evidence:
        return evidence[:5]
    features = rule.get("features", {})
    gaps = []
    if features.get("unknown_product"):
        gaps.append("信息缺口：尚未说清产品类型、底层资产或风险等级。")
    if features.get("unknown_fee_or_redemption"):
        gaps.append("信息缺口：费率、锁定期、赎回规则或到账时间不清楚。")
    if not gaps:
        gaps.append("当前缺少更多可疑原文，建议补充主体、渠道、费用和核验路径。")
    return gaps[:5]


def _summary(rule: dict[str, Any]) -> str:
    level = rule.get("level", "低风险")
    score = rule.get("score", 0)
    scene = rule.get("scene", "转账付款")
    if level == "低风险":
        return f"当前更像是可核验的 {scene} 场景，风险分数 {score}/100。仍建议保留凭证并确认主体一致。"
    return f"当前 {scene} 场景触发 {level}，风险分数 {score}/100。建议暂停操作并通过官方渠道核验。"
