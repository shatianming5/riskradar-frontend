from __future__ import annotations

import re
import sys
from functools import lru_cache
from typing import Any

from .paths import REFERENCES_DIR, SCRIPTS_DIR, SKILL_DIR
from .schemas import AnalyzeResponse

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from risk_score import analyze as analyze_with_rule_engine  # noqa: E402

REQUIRED_OUTPUT_FIELDS = [
    "risk_level",
    "risk_score",
    "scenario",
    "reasoning_basis",
    "evidence_or_gaps",
    "calm_questions",
    "next_actions",
    "safe_reply_template",
    "agent_trace",
]

REFERENCE_FILES = {
    "risk_taxonomy": "risk_taxonomy.md",
    "scoring_rules": "scoring_rules.md",
    "output_contract": "output_contract.md",
    "safety_policy": "safety_policy.md",
    "investment_checklist": "investment_checklist.md",
    "demo_cases": "demo_cases.md",
}

SENSITIVE_ASK_PATTERNS = [
    r"请.*验证码",
    r"提供.*验证码",
    r"发送.*验证码",
    r"银行卡完整",
    r"支付密码",
    r"身份证照片",
]

ABSOLUTE_FRAUD_PATTERNS = [
    (r"肯定是诈骗", "高度疑似风险"),
    (r"百分百诈骗", "高度疑似风险"),
    (r"一定是诈骗", "高度疑似风险"),
    (r"必然是诈骗", "高度疑似风险"),
]


def run_rule_engine(payload: dict[str, Any]) -> dict[str, Any]:
    """Run the existing deterministic RiskRadar scoring engine.

    The rule engine remains the source of truth for score and level.
    LLM agents may add explanations, but they must not override these fields.
    """

    return analyze_with_rule_engine(payload)


@lru_cache(maxsize=16)
def load_reference_doc(name: str) -> str:
    """Load a reference document by logical name."""

    if name == "SKILL":
        return (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    filename = REFERENCE_FILES.get(name)
    if not filename:
        allowed = ", ".join(["SKILL", *REFERENCE_FILES])
        raise ValueError(f"Unknown reference doc: {name}. Allowed: {allowed}")
    return (REFERENCES_DIR / filename).read_text(encoding="utf-8")


def select_reference_names(scene: str | None, features: dict[str, bool], input_text: str) -> list[str]:
    """Progressively select only references needed for the current case."""

    names = ["risk_taxonomy", "output_contract", "safety_policy"]
    text = f"{scene or ''}\n{input_text}"
    investment_related = scene in {"理财决策", "社群荐投"} or any(
        features.get(key)
        for key in [
            "unknown_product",
            "social_hype_only",
            "leverage_or_borrowed_money",
            "cashflow_mismatch",
            "all_in_or_high_concentration",
            "unknown_fee_or_redemption",
        ]
    )
    if investment_related or re.search(r"基金|股票|黄金|ETF|理财|赎回|费率|锁定期|带单|开户链接", text, re.IGNORECASE):
        names.append("investment_checklist")
    if any(features.values()):
        names.append("scoring_rules")
    return list(dict.fromkeys(names))


def validate_output_contract(result: AnalyzeResponse | dict[str, Any]) -> AnalyzeResponse:
    """Validate required fields and enforce safety wording."""

    response = result if isinstance(result, AnalyzeResponse) else AnalyzeResponse.model_validate(result)
    missing = [field for field in REQUIRED_OUTPUT_FIELDS if getattr(response, field, None) is None]
    if missing:
        raise ValueError(f"Missing required response fields: {missing}")

    response.calm_questions = response.calm_questions[:3]
    response.next_actions = response.next_actions[:5]
    if response.risk_level in {"高风险", "极高风险"} and not any(
        ("暂停" in action or "停止" in action) for action in response.next_actions
    ):
        response.next_actions.insert(0, "建议暂停操作，并先通过官方渠道完成核验。")

    response.safe_reply_template = _sanitize_text(response.safe_reply_template)
    response.reasoning_basis = [_sanitize_text(item) for item in response.reasoning_basis[:5]]
    response.evidence_or_gaps = [_sanitize_text(item) for item in response.evidence_or_gaps[:5]]
    response.next_actions = [_sanitize_text(item) for item in response.next_actions[:5]]
    response.calm_questions = [_sanitize_question(item) for item in response.calm_questions[:3]]
    return response


def save_feedback(conversation_id: str, user_feedback: str) -> dict[str, str]:
    """Reserved hook for future feedback persistence."""

    return {"conversation_id": conversation_id, "status": "accepted", "feedback": user_feedback}


def _sanitize_text(text: str) -> str:
    clean = text.strip()
    for pattern, replacement in ABSOLUTE_FRAUD_PATTERNS:
        clean = re.sub(pattern, replacement, clean)
    for pattern in SENSITIVE_ASK_PATTERNS:
        clean = re.sub(pattern, "不要提供验证码、密码、银行卡完整信息或身份证照片", clean)
    clean = clean.replace("保证收益", "不要相信保证收益")
    clean = clean.replace("稳赚不赔", "不要相信稳赚不赔")
    return clean


def _sanitize_question(text: str) -> str:
    clean = _sanitize_text(text)
    return clean if clean.endswith("？") or clean.endswith("?") else f"{clean}？"
