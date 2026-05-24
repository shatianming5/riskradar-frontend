# RiskRadar Frontend

RiskRadar is a product-grade frontend prototype for a college-student personal finance risk-control Agent. It is designed for the decision window before a user transfers money, borrows, shares sensitive credentials, or follows an investment recommendation.

Instead of giving a vague warning, the interface turns a raw chat record or financial decision description into a structured risk assessment: scenario classification, deterministic score, explainable evidence, calm-check questions, next actions, and a copy-ready safe reply.

![RiskRadar workbench](docs/riskradar-workbench.png)

## Product Positioning

RiskRadar is not a payment tool, anti-fraud chatbot, or investment advisor. It is a pre-decision risk-control layer for young users who often face high-pressure, low-context financial decisions:

- campus part-time deposits and upfront fees
- second-hand trading and off-platform payment requests
- fake customer-service refunds, verification codes, and screen sharing
- acquaintance borrowing and third-party transfer requests
- social investment hype, group-led stock or fund recommendations
- borrowed-money investing, heavy concentration, and liquidity mismatch
- low-risk official payment and investing scenarios used as calibration cases

The core product promise is simple: before the user pays, borrows, shares credentials, or places an order, RiskRadar helps them pause for 30 seconds and check the risk.

## System Design

The frontend models a multi-agent risk-control workflow while keeping the demo deterministic and reproducible.

| Layer | Responsibility |
| --- | --- |
| Detective Agent | Extracts entities, payment channels, counterparties, urgency, and quoted evidence from user input. |
| Risk-Control Agent | Applies stable scoring rules and converts risk signals into a 0-100 score. |
| Red-Team Agent | Anticipates the next likely manipulation path, such as adding fees, forcing off-platform payment, or escalating urgency. |
| Coach Agent | Converts analysis into user-facing questions, concrete actions, and a safe reply template. |

The scoring engine is implemented locally in TypeScript so the demo works without network calls or model latency. It mirrors the rule structure used by the RiskRadar project materials: high-risk signals add points, verified official channels reduce points, combination rules raise severe patterns, and hard floors prevent under-scoring credential or screen-sharing attacks.

## Interface

The application is organized as a three-panel workbench:

- **Input Panel**: paste chat records, transaction descriptions, or investment ideas; optionally add amount, receiver, claimed entity, channel, and user profile.
- **Risk Radar Panel**: shows score, level, scenario, evidence, and matched rules with explainability tags.
- **Action Panel**: returns exactly three calm-check questions, next-step actions, and a copy-ready safe reply.

A bottom **Agent Teams** band makes the workflow visible for demos and presentations, showing the sequence from evidence extraction to coaching output.

## Demo Cases

The repository includes one-click cases covering both high-risk and low-risk situations:

- part-time deposit request with upfront payment and off-platform transfer
- fake refund flow requiring screen sharing and verification code
- gold-themed fund recommendation driven by group hype
- borrowed-money gold ETF purchase with heavy concentration
- official campus payment through verified school channels
- second-hand camera deposit outside the platform
- stock group account-opening link with guaranteed short-term return
- low-risk money-market fund purchase through a bank app

These cases are intentionally diverse so the system does not behave like an over-sensitive fraud detector. It can flag severe risk, identify financial decision gaps, and also recognize lower-risk official workflows.

## Tech Stack

- React 19
- TypeScript
- Vite
- Framer Motion
- Lucide React
- CSS design tokens with a RiskRadar visual system inspired by the project poster

## Local Development

```bash
npm install
npm run dev
```

Open:

```text
http://localhost:5173/
```

## Production Build

```bash
npm run build
```

The production build is written to `dist/`.

## Repository Structure

```text
src/
  components/       UI panels and Agent Teams trace
  data/             curated demo cases
  lib/              local scoring engine and shared types
  App.tsx           application state and orchestration
  styles.css        visual system and responsive layout
docs/
  riskradar-workbench.png
```

## Risk Boundaries

RiskRadar does not execute payments, place investment orders, request sensitive credentials, or provide guaranteed financial outcomes. Its role is to surface risk signals and help the user pause, verify official channels, preserve evidence, and make a safer next move.
