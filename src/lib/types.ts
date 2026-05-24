export type RiskLevel = "低风险" | "中风险" | "高风险" | "极高风险";

export type RuleTag = "规则命中" | "核验状态" | "硬规则";

export type FeatureMap = Record<string, boolean>;

export interface DemoCase {
  id: string;
  title: string;
  group: string;
  scene: string;
  inputText: string;
  receiver: string;
  claimedEntity: string;
  channel: string;
  profile: {
    userType: "student" | "young_user";
    firstTimeTrade: boolean;
  };
  features: FeatureMap;
}

export interface AnalyzePayload {
  inputText: string;
  amount?: string;
  receiver?: string;
  claimedEntity?: string;
  channel?: string;
  scene?: string;
  isStudent?: boolean;
  firstTimeTrade?: boolean;
  features?: FeatureMap;
  conversationId?: string;
}

export interface MatchedRule {
  key: string;
  points: number;
  reason: string;
  tag: RuleTag;
  evidence: string[];
}

export interface AnalysisResult {
  scene: string;
  score: number;
  level: RiskLevel;
  matchedRules: MatchedRule[];
  evidence: string[];
  features: FeatureMap;
  paymentRelated: boolean;
  creditRelated: boolean;
  investmentRelated: boolean;
  summary: string;
  calmQuestions: string[];
  nextActions: string[];
  replyTemplate: string;
  redTeamNotes: string[];
  agentTrace?: Array<{
    agent: string;
    action: string;
    summary: string;
    toolCalls?: string[];
  }>;
  backendStatus?: "remote" | "fallback";
}
