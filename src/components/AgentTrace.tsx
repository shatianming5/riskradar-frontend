import { BrainCircuit, CheckCircle2, Radar, ScanSearch, ShieldAlert } from "lucide-react";
import type { AnalysisResult } from "../lib/types";

interface AgentTraceProps {
  result: AnalysisResult;
  activeStep: number;
  analyzing: boolean;
}

const agents = [
  {
    name: "侦探 Agent",
    role: "实体与证据抽取",
    icon: ScanSearch
  },
  {
    name: "风控 Agent",
    role: "规则评分",
    icon: Radar
  },
  {
    name: "红队 Agent",
    role: "诱导路径推演",
    icon: ShieldAlert
  },
  {
    name: "教练 Agent",
    role: "行动建议",
    icon: BrainCircuit
  }
];

export function AgentTrace({ result, activeStep, analyzing }: AgentTraceProps) {
  return (
    <section className="agent-band" aria-label="Agent Teams 推理轨迹">
      <div className="agent-band-title">
        <strong>Agent Teams</strong>
        <span>{analyzing ? "协同推理中" : `${result.matchedRules.length} 条规则证据已归档`}</span>
      </div>

      <div className="agent-grid">
        {agents.map((agent, index) => {
          const AgentIcon = agent.icon;
          const active = analyzing ? index <= activeStep : true;
          return (
            <div className={`agent-card ${active ? "active" : ""}`} key={agent.name}>
              <div className="agent-icon">
                {active && !analyzing ? <CheckCircle2 size={19} /> : <AgentIcon size={19} />}
              </div>
              <div>
                <strong>{agent.name}</strong>
                <span>{agent.role}</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="redteam-notes">
        {result.redTeamNotes.map((note) => (
          <p key={note}>{note}</p>
        ))}
      </div>
    </section>
  );
}
