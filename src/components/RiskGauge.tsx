import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle2, Gauge, ShieldAlert } from "lucide-react";
import type { CSSProperties } from "react";
import { getLevelClass } from "../lib/analyzer";
import type { AnalysisResult } from "../lib/types";

interface RiskGaugeProps {
  result: AnalysisResult;
  analyzing: boolean;
}

const levelIcon = {
  低风险: CheckCircle2,
  中风险: Gauge,
  高风险: AlertTriangle,
  极高风险: ShieldAlert
};

export function RiskGauge({ result, analyzing }: RiskGaugeProps) {
  const LevelIcon = levelIcon[result.level];
  const levelClass = getLevelClass(result.level);
  const angle = Math.round((result.score / 100) * 360);
  const visibleRules = result.matchedRules.slice(0, 6);

  return (
    <section className="panel result-panel" aria-labelledby="risk-title">
      <div className="panel-title-row">
        <div>
          <span className="panel-eyebrow">
            <Gauge size={15} />
            风险雷达
          </span>
          <h2 id="risk-title">分析结果</h2>
        </div>
        <span className={`level-badge ${levelClass}`}>
          <LevelIcon size={16} />
          {result.level}
        </span>
      </div>

      <div className="risk-hero">
        <motion.div
          className={`score-orbit ${levelClass}`}
          animate={{ rotate: analyzing ? [0, 8, -8, 0] : 0 }}
          transition={{ repeat: analyzing ? Infinity : 0, duration: 1.2 }}
          style={{ "--score-angle": `${angle}deg` } as CSSProperties}
        >
          <div className="score-core">
            <strong>{result.score}</strong>
            <span>/100</span>
          </div>
        </motion.div>

        <div className="risk-meta">
          <div>
            <span>场景判断</span>
            <strong>{result.scene}</strong>
          </div>
          <div>
            <span>控制目标</span>
            <strong>决策前风险控制</strong>
          </div>
          <div className="relation-tags">
            {result.paymentRelated && <em>支付</em>}
            {result.creditRelated && <em>借贷</em>}
            {result.investmentRelated && <em>理财</em>}
          </div>
        </div>
      </div>

      <p className="summary-copy">{result.summary}</p>

      <div className="evidence-block">
        <h3>可疑证据 / 信息缺口</h3>
        <div className="evidence-list">
          {result.evidence.length > 0 ? (
            result.evidence.slice(0, 4).map((item) => <p key={item}>{item}</p>)
          ) : (
            <p>暂未发现明显高危原文，建议继续补充主体、渠道、费用和核验信息。</p>
          )}
        </div>
      </div>

      <div className="rule-stack">
        <h3>判断依据</h3>
        {visibleRules.length > 0 ? (
          visibleRules.map((rule) => (
            <div className="rule-item" key={`${rule.key}-${rule.points}`}>
              <span className={rule.tag === "核验状态" ? "safe-points" : "risk-points"}>
                {rule.points > 0 ? `+${rule.points}` : rule.points}
              </span>
              <div>
                <strong>[{rule.tag}] {rule.reason}</strong>
                <small>{rule.key}</small>
              </div>
            </div>
          ))
        ) : (
          <div className="rule-item quiet">
            <span>0</span>
            <div>
              <strong>[核验状态] 目前没有命中高危规则</strong>
              <small>仍需以官方凭证为准</small>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
