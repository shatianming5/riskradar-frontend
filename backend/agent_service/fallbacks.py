from __future__ import annotations

import re
from typing import Any

from .schemas import CoachResult, InvestigationResult, RedTeamResult


def fallback_investigation(request_data: dict[str, Any]) -> InvestigationResult:
    input_text = str(request_data.get("input_text") or "")
    return InvestigationResult(
        scene=_infer_priority_scene(input_text),
        amount=request_data.get("amount"),
        receiver=request_data.get("receiver"),
        claimed_entity=request_data.get("claimed_entity"),
        channel=request_data.get("channel"),
        features={},
        evidence=[],
        missing_information=[],
    )


def _infer_priority_scene(text: str) -> str | None:
    if re.search(r"群老师|基金交流群|带单|喊单|开户链接|内部消息|直播间|不上车|大家都在买", text):
        return "社群荐投"
    if re.search(r"基金|股票|黄金|ETF|理财|费率|赎回|锁定期|重仓|花呗|借呗|校园分期", text, re.IGNORECASE):
        return "理财决策"
    if re.search(r"验证码|屏幕共享|共享屏幕|会议软件|远程控制|订单异常|退款", text):
        return "网购退款"
    if re.search(r"兼职|保证金|资料费|入职|日结", text):
        return "兼职押金"
    if re.search(r"二手|卖家|定金|相机|平台手续费", text):
        return "二手交易"
    if re.search(r"统一支付平台|学院|学校|辅导员|报名费", text):
        return "校园缴费"
    if re.search(r"自称.*同学|手机坏了|转.*朋友|先帮忙", text):
        return "熟人借钱"
    return None


def fallback_red_team(rule_result: dict[str, Any]) -> RedTeamResult:
    features = rule_result.get("features", {})
    scene = rule_result.get("scene", "转账付款")
    if features.get("asks_for_sensitive_credentials") or features.get("asks_for_screen_share"):
        return RedTeamResult(
            notes=["对方可能继续用“账户冻结”“退款失败”压缩核验时间。", "下一步常见诱导是要求开启屏幕共享、远程控制或发送验证码。"],
            manipulation_signals=["账户接管风险", "紧迫施压"],
        )
    if scene in {"理财决策", "社群荐投"} or features.get("social_hype_only"):
        return RedTeamResult(
            notes=["对方或群聊可能继续制造“名额有限”“不上车就晚了”的氛围。", "非官方链接可能把开户、充值和下单绑定到同一条路径里。"],
            manipulation_signals=["群体跟风", "高收益诱导"],
        )
    if features.get("off_platform") and features.get("upfront_fee"):
        return RedTeamResult(
            notes=["对方可能先承诺返还，再追加认证费、解冻费或手续费。", "离开平台后，交易凭证和申诉链路会明显变弱。"],
            manipulation_signals=["追加费用", "脱离平台"],
        )
    return RedTeamResult(
        notes=["后续应重点观察是否追加付款、改收款方或要求保密。", "任何要求跳出官方渠道的变化都应重新评估。"],
        manipulation_signals=["核验不足"],
    )


def fallback_coach(rule_result: dict[str, Any]) -> CoachResult:
    level = rule_result.get("level", "低风险")
    scene = rule_result.get("scene", "转账付款")
    features = rule_result.get("features", {})
    investment = scene in {"理财决策", "社群荐投"} or features.get("unknown_product") or features.get("social_hype_only")
    account_takeover = features.get("asks_for_sensitive_credentials") or features.get("asks_for_screen_share")

    if level == "低风险":
        return CoachResult(
            calm_questions=[
                "收款主体、通知来源和官方页面是否一致？",
                "付款或下单是否仍然留在官方平台内完成？",
                "我是否已保存订单、通知和付款凭证？",
            ],
            next_actions=[
                "继续通过官方入口操作，不要改走私聊或个人收款码。",
                "保存订单、通知、付款凭证和主体核验截图。",
                "付款或下单前再次确认金额、收款主体和产品信息一致。",
            ],
            safe_reply_template="我会继续通过官方平台完成，并保留订单、通知和付款凭证。如果后续需要改到私下转账或补充敏感信息，我会重新核验。",
        )

    if investment:
        return CoachResult(
            calm_questions=[
                "我能不能用自己的话说清楚这是什么产品、底层投什么、最坏会亏什么？",
                "这笔钱如果一个月内要用，或者亏损 10%-20%，我还能接受吗？",
                "我现在想买，是因为我看懂了，还是因为别人说“再不上车就晚了”？",
            ],
            next_actions=[
                "建议暂停下单，先补齐产品类型、底层资产、风险等级、费率和赎回规则。",
                "不要使用花呗、借呗、校园分期、房租、学费或短期要用的钱投资。",
                "回到银行、券商或持牌基金销售的官方渠道独立核验产品。",
                "拒绝群聊带单和非官方开户链接。",
            ],
            safe_reply_template="我先不跟单也不下单。我要先看清产品说明、风险等级、费率和赎回规则，并且只会通过官方持牌渠道、用不影响生活的闲钱再决定。",
        )

    if account_takeover:
        return CoachResult(
            calm_questions=[
                "对方身份能否通过平台 App、官网客服或订单页独立核验？",
                "对方为什么需要验证码、屏幕共享、远程控制或完整银行卡信息？",
                "如果我现在断开联系，是否还能通过官方入口完成同一件事？",
            ],
            next_actions=[
                "立即停止发送验证码、支付密码、身份证照片或银行卡完整信息。",
                "立刻关闭屏幕共享、远程控制和不明会议软件。",
                "通过平台 App 或官网客服重新核验订单和退款状态。",
                "若已经泄露信息，尽快冻结支付账户并保留聊天证据。",
            ],
            safe_reply_template="我不会提供验证码、支付密码或屏幕共享。请通过平台官方 App 或官网客服工单处理，我会自行从官方入口核验。",
        )

    return CoachResult(
        calm_questions=[
            "收款方、沟通方和声称的官方主体是否完全一致？",
            "这笔交易能否留在官方平台、学校平台或有担保的渠道内完成？",
            "对方是否用限时、名额、先交钱等方式压缩我的核验时间？",
        ],
        next_actions=[
            "建议暂停付款，不要先交保证金、定金、资料费或解冻费。",
            "拒绝脱离平台、私下转账和个人收款码。",
            "通过学校、平台、官方客服或熟人本人电话做二次核验。",
            "保留聊天记录、收款码、链接和对方账号信息。",
        ],
        safe_reply_template="我暂时不付款。请提供可在官方平台核验的订单、主体信息和收款方式，我只会在平台内或官方渠道完成交易。",
    )
