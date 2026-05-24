import { Activity, Radar, ShieldCheck } from "lucide-react";

interface BrandHeaderProps {
  totalCases: number;
}

export function BrandHeader({ totalCases }: BrandHeaderProps) {
  return (
    <header className="brand-header">
      <div className="brand-lockup">
        <div className="brand-mark" aria-hidden="true">
          <ShieldCheck size={30} strokeWidth={2.3} />
        </div>
        <div>
          <div className="brand-kicker">
            <Radar size={15} />
            大学生个人金融风险控制 Agent
          </div>
          <h1>RiskRadar</h1>
        </div>
      </div>

      <div className="header-metrics" aria-label="演示状态">
        <div className="metric-pill">
          <span>{totalCases}</span>
          <small>Demo Cases</small>
        </div>
        <div className="metric-pill strong">
          <Activity size={16} />
          <small>30 秒冷静</small>
        </div>
      </div>
    </header>
  );
}
