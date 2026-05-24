# RiskRadar Risk Engine and ArkClaw Skill

This directory contains the backend-side risk-control package used by the RiskRadar frontend and competition demo materials. It is structured as an ArkClaw Skill package with deterministic scoring scripts, reusable risk references, demo cases, and regression checks.

## Contents

```text
SKILL.md                 ArkClaw skill definition and operating workflow
agents/openai.yaml       Skill display metadata and default prompt
assets/                  Demo inputs, expected outputs, prompts, script, poster copy
references/              Risk taxonomy, scoring rules, output contract, safety policy
scripts/risk_score.py    Deterministic rule-based scoring engine
scripts/run_eval.py      Lightweight regression test runner
```

## Scoring Model

The scoring engine uses a hybrid risk-control structure:

- high-risk signals add points, such as upfront fees, off-platform transfer, credential requests, screen sharing, urgency pressure, social investment hype, borrowed-money investing, and liquidity mismatch
- safety signals subtract points, such as official platforms, verified receivers, official double checks, licensed financial channels, product understanding, and small-position spare-money investing
- combination rules raise compound patterns, such as off-platform plus upfront fee, unknown product plus social hype plus high-return promise, and borrowed-money plus heavy concentration
- hard floors prevent severe account-takeover patterns from being under-scored

Risk levels are normalized to:

| Score | Level |
| --- | --- |
| 0-29 | Low risk |
| 30-59 | Medium risk |
| 60-79 | High risk |
| 80-100 | Critical risk |

## Run Regression Checks

From this directory:

```bash
python3 scripts/run_eval.py
```

Expected result:

```text
Evaluation: 24/24 checks passed
All regression checks passed.
```

## Run a Single Case

```bash
python3 scripts/risk_score.py \
  --input assets/sample_inputs.json \
  --case part_time_deposit \
  --pretty
```

## Output Contract

The generated product output should preserve the fixed order defined in `references/output_contract.md`:

1. risk level
2. risk score
3. scenario
4. reasoning basis
5. suspicious evidence or information gaps
6. three calm-check questions
7. next action
8. safe reply template

This contract is what keeps the frontend, demo script, and ArkClaw Skill aligned.
