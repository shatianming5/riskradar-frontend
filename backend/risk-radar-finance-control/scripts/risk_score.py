#!/usr/bin/env python3
"""Deterministic scoring helper for college-student personal finance risk control."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

NEGATION_PREFIXES = ["没有", "未", "不需要", "不要求", "不用", "无需", "不是", "并未", "别", "并没有"]

RISK_RULES: List[Tuple[str, int, str]] = [
    ("upfront_fee", 25, "存在前置收费，如保证金、押金、解冻费或手续费"),
    ("off_platform", 20, "要求脱离官方平台交易"),
    ("personal_receiver_claims_official", 20, "个人账户冒充官方、学校、企业或平台主体"),
    ("asks_for_sensitive_credentials", 40, "要求验证码、支付密码、银行卡完整信息或身份证照片"),
    ("asks_for_screen_share", 40, "要求屏幕共享、远程控制或下载不明 App"),
    ("high_return", 20, "承诺高返利、稳赚不赔、肯定上涨或轻松赚钱"),
    ("urgency_pressure", 15, "制造紧迫感或施压，压缩核验时间"),
    ("entity_mismatch", 20, "沟通主体、交易主体和收款主体不一致"),
    ("cannot_verify", 15, "无法通过官方渠道核验"),
    ("student_or_first_time", 10, "用户是学生、新手或首次交易"),
    ("emotion_manipulation", 15, "使用保密、同情、恐吓或内疚等情绪操控"),
    ("identity_impersonation", 25, "冒充熟人、客服、老师、官方人员或机构"),
    ("third_party_receiver", 15, "要求向第三方收款人转账或代付"),
    ("unknown_product", 15, "不了解产品是什么、投什么或风险等级如何"),
    ("social_hype_only", 15, "主要根据群聊、老师带单、主播或同学推荐做决定"),
    ("leverage_or_borrowed_money", 25, "打算用借来的钱或分期去投资"),
    ("cashflow_mismatch", 20, "打算把房租、学费、生活费或短期必用资金投入存在波动或锁定期的产品"),
    ("all_in_or_high_concentration", 15, "打算重仓、满仓或把大部分生活费压进去"),
    ("unknown_fee_or_redemption", 10, "不清楚费率、手续费、赎回规则或锁定期"),
]

SAFE_RULES: List[Tuple[str, int, str]] = [
    ("official_platform", -15, "可以在学校、平台、商家或官方流程内完成操作"),
    ("verified_receiver", -10, "收款主体已核验"),
    ("has_order_or_contract", -10, "提供了可验证订单、合同或平台记录"),
    ("official_double_check", -15, "已通过官方渠道二次核验"),
    ("official_licensed_platform", -10, "通过银行、券商、持牌基金销售或官方平台开户"),
    ("understands_product", -10, "能说清产品类型、底层资产和风险等级"),
    ("understands_fee_and_liquidity", -10, "已了解费率、赎回规则或到账时间"),
    ("spare_money_investment", -15, "使用闲钱、小额资金，不影响生活和学业"),
    ("small_position_or_diversified", -10, "小额试投、分散配置或明确不重仓"),
]

COMBO_RULES: List[Tuple[Tuple[str, ...], int, str]] = [
    (("off_platform", "upfront_fee"), 15, "脱离平台后先付费用，平台保障失效"),
    (("identity_impersonation", "urgency_pressure", "third_party_receiver"), 15, "身份未核验且要求紧急代付给第三方"),
    (("unknown_product", "social_hype_only", "high_return"), 20, "不了解产品却因群体跟风和收益承诺准备下单"),
    (("leverage_or_borrowed_money", "all_in_or_high_concentration"), 15, "借钱投资且仓位过重，抗风险能力明显不足"),
    (("cashflow_mismatch", "unknown_fee_or_redemption"), 15, "短期必用资金还对应锁定期或赎回规则不清，流动性风险明显"),
]

HARD_FLOORS: List[Tuple[Tuple[str, ...], int, str]] = [
    (("asks_for_sensitive_credentials",), 80, "涉及验证码、支付密码或完整敏感凭证，最低极高风险"),
    (("asks_for_screen_share",), 80, "涉及屏幕共享或远程控制，最低极高风险"),
    (("off_platform", "upfront_fee"), 60, "脱离平台并要求先付款，最低高风险"),
    (("identity_impersonation", "third_party_receiver"), 70, "身份冒充并要求向第三方付款，最低高风险"),
    (("leverage_or_borrowed_money", "high_return"), 70, "借钱参与高收益或强上涨预期投资，最低高风险"),
]

SCENE_PATTERNS: Dict[str, List[str]] = {
    "兼职押金": [r"兼职", r"保证金", r"资料费", r"培训费", r"入职"],
    "二手交易": [r"二手", r"卖家", r"定金", r"闲置", r"相机", r"平台手续费"],
    "网购退款": [r"退款", r"客服", r"退赔", r"账户异常", r"订单异常"],
    "校园缴费": [r"学校", r"学院", r"报名费", r"统一支付平台", r"辅导员"],
    "借款/校园贷": [r"借钱", r"校园贷", r"征信", r"放款", r"分期", r"秒批"],
    "理财决策": [r"基金", r"股票", r"黄金", r"ETF", r"货币基金", r"宽基", r"指数基金", r"理财产品", r"费率", r"赎回", r"锁定期", r"T\+1", r"T\+2"],
    "社群荐投": [r"基金交流群", r"群老师", r"带单", r"喊单", r"博主推荐", r"主播推荐", r"内幕消息", r"同学都在买", r"开户链接", r"直播间", r"短线群"],
    "熟人借钱": [r"同学", r"朋友", r"先帮忙转", r"晚上还我", r"手机坏了"],
    "账号租借": [r"租号", r"代实名", r"刷流水", r"账号"],
    "验证码/屏幕共享": [r"验证码", r"共享屏幕", r"远程", r"下载软件", r"会议软件"],
    "转账付款": [r"转账", r"付款", r"付款码", r"打钱"],
}

FEATURE_PATTERNS: Dict[str, List[str]] = {
    "upfront_fee": [r"保证金", r"押金", r"认证费", r"解冻费", r"资料费", r"先交", r"先付", r"定金", r"先交.*手续费", r"手续费.*先交"],
    "off_platform": [r"不要走平台", r"加微信", r"私下转账", r"线下交易", r"跳出平台", r"平台手续费太高", r"平台外交易", r"私聊", r"不要去官方券商App搜", r"群里链接", r"开户链接", r"非官方链接", r"私发链接"],
    "personal_receiver_claims_official": [r"官方.*微信", r"学校.*微信", r"客服.*个人收款", r"公司.*个人收款", r"企业.*个人收款"],
    "asks_for_sensitive_credentials": [r"验证码", r"支付密码", r"银行卡密码", r"银行卡完整信息", r"身份证照片", r"CVV", r"短信码"],
    "asks_for_screen_share": [r"屏幕共享", r"共享屏幕", r"远程控制", r"远程协助", r"下载.*软件", r"会议软件"],
    "high_return": [r"高返利", r"稳赚", r"稳赚不赔", r"轻松赚钱", r"刷单", r"返还\d+", r"日结\d+", r"肯定还会涨", r"必涨", r"翻倍", r"保本保收益", r"三天至少涨\d+", r"一周回本", r"连续涨停", r"短期翻倍"],
    "urgency_pressure": [r"马上", r"立刻", r"十分钟内", r"名额有限", r"尽快", r"超时失效", r"不转后果", r"急需", r"很急", r"账户会被冻结", r"错过机会", r"现在不上车", r"今晚开盘前", r"收盘前", r"名额只剩", r"才有名额"],
    "entity_mismatch": [r"官方.*个人收款", r"学校.*个人收款", r"平台.*私人", r"收款主体不一致", r"转给.*朋友"],
    "cannot_verify": [r"不要核验", r"不能走平台", r"没有订单", r"先转再说", r"手机坏了", r"不方便视频", r"不方便电话", r"无法核验", r"自称", r"没有官方页面", r"找不到产品说明", r"搜不到产品代码", r"不让看详情", r"只给链接", r"不要去官方券商App搜"],
    "student_or_first_time": [r"学生", r"第一次交易", r"新手"],
    "emotion_manipulation": [r"不要告诉别人", r"保密", r"帮帮我", r"不然就", r"求你了", r"否则"],
    "identity_impersonation": [r"我是你.*同学", r"自称.*同学", r"自称.*朋友", r"我是客服", r"自称.*客服", r"冒充.*客服", r"自称.*老师", r"自称.*辅导员", r"官方工作人员", r"平台客服"],
    "official_platform": [r"统一支付平台", r"平台内下单", r"平台内交易", r"平台担保", r"官方小程序", r"官方公众号", r"订单一致", r"平台内完成"],
    "verified_receiver": [r"收款主体显示为", r"实名认证", r"官方主体一致", r"收款主体一致"],
    "has_order_or_contract": [r"订单号", r"合同", r"工单", r"平台记录"],
    "official_double_check": [r"官方客服确认", r"辅导员群", r"学校通知", r"平台客服确认", r"辅导员转发", r"二次确认"],
    "third_party_receiver": [r"转给.*朋友", r"转到.*朋友", r"第三方收款", r"代付", r"帮.*垫"],
    "unknown_product": [r"不了解", r"不清楚", r"看不懂", r"不知道这是什么", r"不知道.*投什么", r"不懂这个项目", r"没看过详情", r"没看说明", r"不清楚风险等级", r"没太看明白", r"不知道跟踪什么", r"没看基金招募说明书", r"不懂净值"],
    "social_hype_only": [r"群老师", r"老师带单", r"喊单", r"群友都在买", r"同学都在买", r"博主推荐", r"主播推荐", r"短视频看到", r"跟单", r"内幕消息", r"基金交流群", r"直播间", r"群里都在冲", r"短线群", r"热榜"],
    "leverage_or_borrowed_money": [r"借钱买", r"借钱炒股", r"借钱理财", r"花呗", r"借呗", r"校园分期", r"贷款买", r"生活费补仓", r"借来的钱", r"慢慢还", r"信用卡套现"],
    "cashflow_mismatch": [r"下个月房租", r"房租和生活费", r"学费先拿去买", r"生活费先买", r"一个月内要用的钱", r"短期要用的钱", r"马上要交房租", r"到时候应该能取出来", r"30天锁定期理财"],
    "all_in_or_high_concentration": [r"all in", r"梭哈", r"满仓", r"全仓", r"全部压上", r"重仓", r"把生活费都投进去"],
    "unknown_fee_or_redemption": [r"不知道手续费", r"不知道费率", r"不知道多久能赎回", r"不知道锁定期", r"不清楚申赎规则", r"不清楚费用", r"手续费多少", r"没看提前赎回规则", r"没有细看提前赎回规则", r"不知道T\+\d", r"不知道多久到账"],
    "official_licensed_platform": [r"官方银行App", r"银行官方App", r"官方券商App", r"券商官方App", r"持牌基金销售", r"银行官方渠道", r"券商官方渠道", r"银行理财专区", r"券商App里", r"官网开户"],
    "understands_product": [r"知道它投什么", r"知道它主要做", r"了解底层资产", r"看过产品详情", r"看过基金详情", r"看过招募说明", r"看过产品说明", r"了解风险等级", r"主要做短期现金管理", r"知道跟踪什么指数", r"知道它跟踪", r"知道是宽基指数", r"知道会有波动", r"知道它不是保本"],
    "understands_fee_and_liquidity": [r"看过费率", r"看过手续费", r"看过申赎规则", r"知道可以随时赎回", r"知道锁定期", r"知道到账时间", r"知道T\+\d", r"看过提前赎回规则", r"知道赎回到账"],
    "spare_money_investment": [r"闲钱", r"剩余生活费", r"不影响下月开销", r"可承受亏损", r"不是借钱买", r"每月拿\d+元闲钱", r"不动房租", r"不动学费"],
    "small_position_or_diversified": [r"先买少量", r"小额试投", r"分散", r"不重仓", r"不满仓", r"一小部分", r"定投", r"每月少量", r"先从\d+元开始"],
}


def normalize_text(*parts: object) -> str:
    return "\n".join(str(part) for part in parts if part).strip()


def split_sentences(text: str) -> List[str]:
    raw = re.split(r"[。！？\n]+", text)
    return [item.strip(" \t\r,，；;") for item in raw if item.strip()]


def infer_scene(text: str, explicit_scene: str | None = None) -> str:
    if explicit_scene:
        return explicit_scene
    for scene, patterns in SCENE_PATTERNS.items():
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
            return scene
    return "转账付款"


def is_negated(sentence: str, start: int) -> bool:
    window = sentence[max(0, start - 8) : start]
    return any(token in window for token in NEGATION_PREFIXES)


def extract_pattern_evidence(text: str, patterns: Iterable[str]) -> List[str]:
    evidence: List[str] = []
    for sentence in split_sentences(text):
        for pattern in patterns:
            found = False
            for result in re.finditer(pattern, sentence, re.IGNORECASE):
                if is_negated(sentence, result.start()):
                    continue
                found = True
                break
            if found:
                evidence.append(sentence)
                break
    return evidence


def dedupe(items: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        clean = str(item).strip()
        if clean and clean not in seen:
            seen.add(clean)
            result.append(clean)
    return result


def detect_features(payload: Dict[str, object]) -> Tuple[Dict[str, bool], List[str], str, Dict[str, List[str]]]:
    text = normalize_text(
        payload.get("input_text"),
        payload.get("text"),
        payload.get("description"),
        "\n".join(payload.get("evidence", []) or []),
    )
    profile = payload.get("profile", {}) or {}
    receiver = str(payload.get("receiver", "") or "")
    claimed_entity = str(payload.get("claimed_entity", "") or "")
    channel = str(payload.get("channel", "") or "")
    combined_text = normalize_text(text, receiver, claimed_entity, channel, json.dumps(profile, ensure_ascii=False))

    feature_keys = {key for key, _, _ in RISK_RULES + SAFE_RULES}
    features: Dict[str, bool] = {key: False for key in feature_keys}
    evidence_map: Dict[str, List[str]] = {key: [] for key in feature_keys}
    evidence: List[str] = list(payload.get("evidence", []) or [])

    for key, patterns in FEATURE_PATTERNS.items():
        matched_evidence = extract_pattern_evidence(text or combined_text, patterns)
        if matched_evidence:
            features[key] = True
            evidence.extend(matched_evidence)
            evidence_map[key].extend(matched_evidence)

    if isinstance(profile, dict):
        if profile.get("user_type") == "student" or profile.get("first_time_trade"):
            features["student_or_first_time"] = True
            evidence_map["student_or_first_time"].append("用户画像显示为学生、新手或首次交易")

    if receiver and claimed_entity:
        if any(token in receiver for token in ["微信", "支付宝", "个人"]) and any(
            token in claimed_entity for token in ["官方", "学校", "公司", "企业", "客服", "机构"]
        ):
            features["personal_receiver_claims_official"] = True
            features["entity_mismatch"] = True
            marker = f"收款方为“{receiver}”，但声称主体为“{claimed_entity}”"
            evidence_map["personal_receiver_claims_official"].append(marker)
            evidence_map["entity_mismatch"].append(marker)

    if receiver and any(token in receiver for token in ["朋友", "第三方", "代付", "他人"]):
        features["third_party_receiver"] = True
        evidence_map["third_party_receiver"].append(f"收款方显示为“{receiver}”")

    explicit_features = payload.get("features", {}) or {}
    if isinstance(explicit_features, dict):
        for key, value in explicit_features.items():
            if key in features and isinstance(value, bool):
                features[key] = value
                if value and not evidence_map[key]:
                    evidence_map[key].append("结构化特征已明确标注为命中")
                if not value:
                    evidence_map[key] = []

    deduped_evidence = dedupe(evidence)
    for key, items in evidence_map.items():
        evidence_map[key] = dedupe(items)

    scene = infer_scene(combined_text, str(payload.get("scene") or "") or None)
    return features, deduped_evidence, scene, evidence_map


def score_risk(features: Dict[str, bool], evidence_map: Dict[str, List[str]] | None = None) -> Dict[str, object]:
    evidence_map = evidence_map or {}
    score = 0
    matched_rules: List[Dict[str, object]] = []

    for key, points, reason in RISK_RULES:
        if features.get(key, False):
            score += points
            matched_rules.append(
                {"key": key, "points": points, "reason": reason, "tag": "规则命中", "evidence": evidence_map.get(key, [])}
            )

    for key, points, reason in SAFE_RULES:
        if features.get(key, False):
            score += points
            matched_rules.append(
                {"key": key, "points": points, "reason": reason, "tag": "核验状态", "evidence": evidence_map.get(key, [])}
            )

    for keys, points, reason in COMBO_RULES:
        if all(features.get(key, False) for key in keys):
            score += points
            combo_evidence: List[str] = []
            for key in keys:
                combo_evidence.extend(evidence_map.get(key, []))
            matched_rules.append(
                {
                    "key": "+".join(keys),
                    "points": points,
                    "reason": reason,
                    "tag": "规则命中",
                    "evidence": dedupe(combo_evidence),
                }
            )

    hard_rule_notes: List[Dict[str, object]] = []
    for keys, min_score, reason in HARD_FLOORS:
        if all(features.get(key, False) for key in keys) and score < min_score:
            combo_evidence: List[str] = []
            for key in keys:
                combo_evidence.extend(evidence_map.get(key, []))
            score = max(score, min_score)
            hard_rule_notes.append(
                {
                    "key": "+".join(keys),
                    "points": 0,
                    "reason": reason,
                    "tag": "硬规则",
                    "evidence": dedupe(combo_evidence),
                }
            )

    if not features.get("asks_for_sensitive_credentials") and not features.get("asks_for_screen_share"):
        score = min(score, 94)

    matched_rules.extend(hard_rule_notes)
    score = max(0, min(100, score))

    if score >= 80:
        level = "极高风险"
    elif score >= 60:
        level = "高风险"
    elif score >= 30:
        level = "中风险"
    else:
        level = "低风险"

    return {"score": score, "level": level, "matched_rules": matched_rules}


def analyze(payload: Dict[str, object]) -> Dict[str, object]:
    features, evidence, scene, evidence_map = detect_features(payload)
    result = score_risk(features, evidence_map)
    return {
        "scene": scene,
        "payment_related": scene in {"转账付款", "二手交易", "兼职押金", "校园缴费", "熟人借钱", "网购退款"},
        "credit_related": scene == "借款/校园贷" or features.get("leverage_or_borrowed_money", False),
        "investment_related": scene in {"理财决策", "社群荐投"},
        "risk_control_target": "大学生个人金融决策前风险控制",
        "score": result["score"],
        "level": result["level"],
        "matched_rules": result["matched_rules"],
        "evidence": evidence[:6],
        "features": features,
    }


def load_payload(input_path: str | None, inline_json: str | None) -> object:
    if inline_json:
        return json.loads(inline_json)
    if input_path:
        return json.loads(Path(input_path).read_text(encoding="utf-8"))
    raise ValueError("Provide --input or --json.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Score college-student personal finance risk.")
    parser.add_argument("--input", help="Path to a JSON file containing one case or a {\"cases\": [...]} object.")
    parser.add_argument("--json", help="Inline JSON for one case.")
    parser.add_argument("--case", help="Case id to run when the input file contains a cases array.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    payload = load_payload(args.input, args.json)

    if isinstance(payload, dict) and "cases" in payload:
        cases = payload.get("cases", [])
        if args.case:
            selected = next((case for case in cases if case.get("id") == args.case), None)
            if selected is None:
                raise SystemExit(f"Case not found: {args.case}")
            output = analyze(selected)
        else:
            output = {case.get("id", f"case-{index}"): analyze(case) for index, case in enumerate(cases, 1)}
    elif isinstance(payload, dict):
        output = analyze(payload)
    else:
        raise SystemExit("Input JSON must be an object.")

    if args.pretty:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
