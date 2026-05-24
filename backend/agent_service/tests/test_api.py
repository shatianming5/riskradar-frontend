from __future__ import annotations

import os

from fastapi.testclient import TestClient

os.environ.pop("OPENAI_API_KEY", None)

from backend.agent_service.app import app
from backend.agent_service.deep_agent_runtime import run_deep_agent_handoff

client = TestClient(app)


def analyze(payload: dict):
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["llm_enabled"] is False


def test_deep_agents_handoff_is_safe_without_llm_key() -> None:
    result = run_deep_agent_handoff({"input_text": "帮我分析这笔转账"})
    assert result["enabled"] is False
    assert "Deep Agents" in result["summary"]


def test_trace_records_skill_and_rule_engine_usage() -> None:
    result = analyze(
        {
            "input_text": "有人说可以帮我退款，但要先把验证码发给他，还要开屏幕共享。",
            "claimed_entity": "平台客服",
            "channel": "私聊",
            "is_student": True,
        }
    )
    calls = [call for item in result["agent_trace"] for call in item["tool_calls"]]
    assert "load_reference_doc(SKILL)" in calls
    assert "load_reference_doc(risk_taxonomy)" in calls
    assert "run_rule_engine" in calls


def test_part_time_deposit_high_risk() -> None:
    result = analyze(
        {
            "input_text": "同学你好，我们这边有校园兼职，日结300。需要先交99元资料保证金，明天入职后返还。名额有限，10分钟内付款。不要走平台，直接微信转账。",
            "receiver": "个人微信收款码",
            "claimed_entity": "校园兼职官方渠道",
            "channel": "微信群兼职",
            "is_student": True,
            "first_time_trade": True,
        }
    )
    assert result["scenario"] == "兼职押金"
    assert result["risk_level"] in {"高风险", "极高风险"}
    assert result["risk_score"] >= 80
    assert len(result["calm_questions"]) == 3


def test_fake_customer_service_code_request() -> None:
    result = analyze(
        {
            "input_text": "我是平台客服，你的订单异常可以退款。请下载会议软件打开屏幕共享，并把短信验证码发给我，否则账户会被冻结。",
            "receiver": "未知",
            "claimed_entity": "平台客服",
            "channel": "短信/即时聊天",
            "is_student": True,
            "first_time_trade": False,
        }
    )
    assert result["scenario"] == "网购退款"
    assert result["risk_level"] == "极高风险"
    assert result["risk_score"] >= 80
    assert any("验证码" in item or "屏幕共享" in item for item in result["evidence_or_gaps"])


def test_social_investment_hype() -> None:
    result = analyze(
        {
            "input_text": "同学拉我进了一个基金交流群，说这只黄金主题基金最近肯定还会涨。可我其实不知道它具体投什么、手续费多少、多久能赎回，只是感觉大家都在买，不上车就错过机会了。",
            "receiver": "基金销售链接",
            "claimed_entity": "基金交流群老师",
            "channel": "群聊",
            "is_student": True,
            "first_time_trade": True,
        }
    )
    assert result["scenario"] == "社群荐投"
    assert result["risk_score"] >= 60
    assert any("暂停下单" in action for action in result["next_actions"])


def test_borrowed_money_investment() -> None:
    result = analyze(
        {
            "input_text": "我想用花呗和校园分期买黄金ETF，最近涨得快，我感觉肯定还会继续涨，准备先重仓进去，亏了以后再慢慢还。我还没太看明白它的风险和手续费。",
            "receiver": "券商或基金平台",
            "claimed_entity": "黄金ETF",
            "channel": "理财 App",
            "is_student": True,
            "first_time_trade": False,
        }
    )
    assert result["scenario"] == "理财决策"
    assert result["risk_score"] >= 70
    assert any("花呗" in evidence or "重仓" in evidence for evidence in result["evidence_or_gaps"])


def test_official_campus_fee_low_risk() -> None:
    result = analyze(
        {
            "input_text": "学院公众号发布活动报名通知，报名费20元，付款链接跳转到学校统一支付平台，收款主体显示为中山大学，辅导员群里也转发了通知。",
            "receiver": "中山大学统一支付平台",
            "claimed_entity": "中山大学",
            "channel": "学院公众号",
            "is_student": True,
            "first_time_trade": False,
        }
    )
    assert result["scenario"] == "校园缴费"
    assert result["risk_level"] == "低风险"
    assert result["risk_score"] <= 20
