#!/usr/bin/env python3
"""Run lightweight regression checks for the RiskRadar scoring script."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

from risk_score import analyze

LEVEL_RANK = {"低风险": 0, "中风险": 1, "高风险": 2, "极高风险": 3}


def load_cases(path: Path) -> Dict[str, Dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {case["id"]: case for case in payload["cases"]}


def validate_result(case_id: str, result: Dict[str, object], expected: Dict[str, object], mode: str) -> List[str]:
    errors: List[str] = []
    actual_level = str(result["level"])
    expected_level = str(expected["expected_level"])
    if LEVEL_RANK[actual_level] < LEVEL_RANK[expected_level]:
        errors.append(f"{mode}: 风险等级过低，期望至少 {expected_level}，实际 {actual_level}")

    actual_score = int(result["score"])
    if "min_score" in expected and actual_score < int(expected["min_score"]):
        errors.append(f"{mode}: 分数过低，期望至少 {expected['min_score']}，实际 {actual_score}")
    if "max_score" in expected and actual_score > int(expected["max_score"]):
        errors.append(f"{mode}: 分数过高，期望至多 {expected['max_score']}，实际 {actual_score}")

    actual_rule_keys = {rule["key"] for rule in result.get("matched_rules", [])}
    for key in expected.get("required_rule_keys", []):
        if key not in actual_rule_keys:
            errors.append(f"{mode}: 缺少预期规则 {key}")
    for key in expected.get("forbidden_rule_keys", []):
        if key in actual_rule_keys:
            errors.append(f"{mode}: 不应命中规则 {key}")

    evidence_text = " ".join(result.get("evidence", []))
    for keyword in expected.get("evidence_keywords", []):
        if keyword not in evidence_text:
            errors.append(f"{mode}: 证据中缺少关键词 {keyword}")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Run regression checks for RiskRadar.")
    parser.add_argument(
        "--input",
        default=str(Path(__file__).resolve().parents[1] / "assets" / "sample_inputs.json"),
        help="Path to sample input cases.",
    )
    parser.add_argument(
        "--expected",
        default=str(Path(__file__).resolve().parents[1] / "assets" / "expected_outputs.json"),
        help="Path to expected outputs.",
    )
    args = parser.parse_args()

    cases = load_cases(Path(args.input))
    expected_cases = load_cases(Path(args.expected))
    failures: List[str] = []

    for case_id, expected in expected_cases.items():
        case = cases.get(case_id)
        if not case:
            failures.append(f"{case_id}: 未在输入样例中找到")
            continue

        structured_result = analyze(case)
        text_only_result = analyze({"input_text": case.get("input_text", "")})

        failures.extend(f"{case_id} | {msg}" for msg in validate_result(case_id, structured_result, expected, "结构化"))
        failures.extend(f"{case_id} | {msg}" for msg in validate_result(case_id, text_only_result, expected, "纯文本"))

    total = len(expected_cases) * 2
    passed = total - len(failures)
    print(f"Evaluation: {passed}/{total} checks passed")
    if failures:
        print("Failures:")
        for item in failures:
            print(f"- {item}")
        raise SystemExit(1)

    print("All regression checks passed.")


if __name__ == "__main__":
    main()
