import type { AnalysisResult, AnalyzePayload, MatchedRule, RiskLevel } from "./types";

interface BackendTraceItem {
  agent: string;
  action: string;
  summary: string;
  tool_calls?: string[];
}

interface BackendResponse {
  risk_level: RiskLevel;
  risk_score: number;
  scenario: string;
  reasoning_basis: string[];
  evidence_or_gaps: string[];
  calm_questions: string[];
  next_actions: string[];
  safe_reply_template: string;
  agent_trace: BackendTraceItem[];
  matched_rules?: MatchedRule[];
  features?: Record<string, boolean>;
  summary?: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function analyzeWithBackend(payload: AnalyzePayload, signal?: AbortSignal): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      input_text: payload.inputText,
      amount: payload.amount || undefined,
      receiver: payload.receiver || undefined,
      claimed_entity: payload.claimedEntity || undefined,
      channel: payload.channel || undefined,
      is_student: payload.isStudent ?? true,
      first_time_trade: payload.firstTimeTrade ?? false,
      conversation_id: payload.conversationId
    }),
    signal
  });

  if (!response.ok) {
    throw new Error(`RiskRadar backend returned ${response.status}`);
  }

  const data = (await response.json()) as BackendResponse;
  const scenario = data.scenario || "转账付款";
  const features = data.features ?? {};
  const agentTrace = data.agent_trace ?? [];

  return {
    scene: scenario,
    score: data.risk_score,
    level: data.risk_level,
    matchedRules: normalizeMatchedRules(data),
    evidence: data.evidence_or_gaps ?? [],
    features,
    paymentRelated: ["转账付款", "二手交易", "兼职押金", "校园缴费", "熟人借钱", "网购退款"].includes(scenario),
    creditRelated: scenario === "借款/校园贷" || Boolean(features.leverage_or_borrowed_money),
    investmentRelated: ["理财决策", "社群荐投"].includes(scenario),
    summary: data.summary || `后端 Agent Teams 已完成 ${scenario} 风险分析。`,
    calmQuestions: data.calm_questions ?? [],
    nextActions: data.next_actions ?? [],
    replyTemplate: data.safe_reply_template || "",
    redTeamNotes: agentTrace.map((item) => `${item.agent}: ${item.summary}`).slice(-3),
    agentTrace: agentTrace.map((item) => ({
      agent: item.agent,
      action: item.action,
      summary: item.summary,
      toolCalls: item.tool_calls
    })),
    backendStatus: "remote"
  };
}

function normalizeMatchedRules(data: BackendResponse): MatchedRule[] {
  if (data.matched_rules?.length) return data.matched_rules;
  return (data.reasoning_basis ?? []).map((reason, index) => ({
    key: `backend_reason_${index + 1}`,
    points: 0,
    reason,
    tag: reason.includes("核验状态") ? "核验状态" : "规则命中",
    evidence: []
  }));
}
