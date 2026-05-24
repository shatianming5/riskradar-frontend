from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["低风险", "中风险", "高风险", "极高风险"]
RuleTag = Literal["规则命中", "核验状态", "硬规则", "红队推演", "合规检查"]


class AnalyzeRequest(BaseModel):
    input_text: str = Field(min_length=1)
    amount: str | None = None
    receiver: str | None = None
    claimed_entity: str | None = None
    channel: str | None = None
    is_student: bool = True
    first_time_trade: bool = False
    conversation_id: str | None = None


class MatchedRule(BaseModel):
    key: str
    points: int = 0
    reason: str
    tag: RuleTag = "规则命中"
    evidence: list[str] = Field(default_factory=list)


class AgentTraceItem(BaseModel):
    agent: str
    action: str
    summary: str
    tool_calls: list[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    risk_level: RiskLevel
    risk_score: int
    scenario: str
    reasoning_basis: list[str]
    evidence_or_gaps: list[str]
    calm_questions: list[str]
    next_actions: list[str]
    safe_reply_template: str
    agent_trace: list[AgentTraceItem]
    matched_rules: list[MatchedRule] = Field(default_factory=list)
    features: dict[str, bool] = Field(default_factory=dict)
    summary: str = ""
    needs_follow_up: bool = False
    follow_up_questions: list[str] = Field(default_factory=list)


class InvestigationResult(BaseModel):
    scene: str | None = None
    amount: str | None = None
    receiver: str | None = None
    claimed_entity: str | None = None
    channel: str | None = None
    product_name: str | None = None
    relationship: str | None = None
    features: dict[str, bool] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


class RedTeamResult(BaseModel):
    notes: list[str] = Field(default_factory=list, min_length=0, max_length=5)
    manipulation_signals: list[str] = Field(default_factory=list)


class CoachResult(BaseModel):
    calm_questions: list[str] = Field(default_factory=list, min_length=0, max_length=3)
    next_actions: list[str] = Field(default_factory=list, min_length=0, max_length=5)
    safe_reply_template: str = ""


class ComplianceResult(BaseModel):
    reasoning_basis: list[str]
    evidence_or_gaps: list[str]
    calm_questions: list[str]
    next_actions: list[str]
    safe_reply_template: str
    notes: list[str] = Field(default_factory=list)


class GraphState(BaseModel):
    request: AnalyzeRequest
    skill_summary: str = ""
    selected_references: dict[str, str] = Field(default_factory=dict)
    investigation: InvestigationResult | None = None
    rule_result: dict[str, Any] = Field(default_factory=dict)
    red_team: RedTeamResult | None = None
    coach: CoachResult | None = None
    final_response: AnalyzeResponse | None = None
    agent_trace: list[AgentTraceItem] = Field(default_factory=list)
    needs_follow_up: bool = False
    follow_up_questions: list[str] = Field(default_factory=list)
