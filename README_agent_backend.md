# RiskRadar Agent Backend

This backend adds a real multi-agent service layer to RiskRadar without replacing the existing deterministic rule engine.

## Architecture

- **FastAPI** exposes `GET /api/health` and `POST /api/analyze`.
- **LangGraph** orchestrates the workflow as explicit nodes: Orchestrator -> Investigator -> Risk Officer -> Red Team -> Coach -> Compliance.
- **LangChain Deep Agents** provides the production LLM harness, subagent definitions, and Skills System integration when `OPENAI_API_KEY` is configured.
- **Skill-aware prompting** loads `backend/risk-radar-finance-control/SKILL.md` first, then progressively loads only the reference docs needed for the current case.
- **Existing rule engine** remains the source of truth for risk score and level through `backend/risk-radar-finance-control/scripts/risk_score.py`.

The LLM is responsible for language understanding, evidence extraction, red-team reasoning, coaching, and compliance polish. It is not allowed to invent or override the risk score.

## LLM and Skill Mode

With `OPENAI_API_KEY` configured, the Orchestrator performs a lightweight Deep Agents handoff before the deterministic LangGraph pipeline continues. The Deep Agents supervisor and subagents are configured with:

- `skills=["/backend"]`, exposing the `risk-radar-finance-control` skill directory.
- A filesystem backend rooted at the repository with read permission limited to `backend/risk-radar-finance-control/**`.
- Subagents for Investigator, Risk Officer, Red Team, Coach, and Compliance.
- The same rule-engine tools used by the service, so score and level still come only from `run_rule_engine`.

The service still works without a model key. In that mode, `agent_trace` records that Deep Agents was skipped, and the local deterministic fallback keeps the demo stable.

## Install

Use Python 3.11+.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Set:

```text
OPENAI_API_KEY=...
OPENAI_MODEL=openai:gpt-4.1-mini
```

If `OPENAI_API_KEY` is not set, the service still runs in deterministic fallback mode using the rule engine and local templates.

## Start

```bash
uvicorn backend.agent_service.app:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/api/health
```

## Analyze API

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "同学你好，我们这边有校园兼职，日结300。需要先交99元资料保证金，明天入职后返还。名额有限，10分钟内付款。不要走平台，直接微信转账。",
    "receiver": "个人微信收款码",
    "claimed_entity": "校园兼职官方渠道",
    "channel": "微信群兼职",
    "is_student": true,
    "first_time_trade": true
  }'
```

Response fields are frontend-compatible:

```json
{
  "risk_level": "极高风险",
  "risk_score": 100,
  "scenario": "兼职押金",
  "reasoning_basis": [],
  "evidence_or_gaps": [],
  "calm_questions": [],
  "next_actions": [],
  "safe_reply_template": "...",
  "agent_trace": []
}
```

Additional fields include `matched_rules`, `features`, `summary`, `needs_follow_up`, and `follow_up_questions`.

## Tests

Run backend API tests:

```bash
pytest backend/agent_service/tests
```

Run original rule-engine regression:

```bash
python3 backend/risk-radar-finance-control/scripts/run_eval.py
```

Expected rule-engine output:

```text
Evaluation: 24/24 checks passed
All regression checks passed.
```

## Safety Guarantees

- Risk score and risk level come only from `run_rule_engine`.
- Deep Agents and direct LLM nodes must follow `SKILL.md`; reference docs are loaded progressively instead of being pasted wholesale on every call.
- The model must not provide buy/sell recommendations for stocks, funds, gold, or ETFs.
- The service must not request verification codes, full bank card numbers, payment passwords, or ID photos.
- High-risk wording uses restrained phrasing such as “高度疑似风险，建议暂停并核验”.
- Information gaps trigger at most 3 follow-up questions.
