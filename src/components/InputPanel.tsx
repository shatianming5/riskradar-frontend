import { motion } from "framer-motion";
import { FileText, Play, RotateCcw, Send, Sparkles, UserRoundCheck } from "lucide-react";
import type { DemoCase } from "../lib/types";

interface InputPanelProps {
  cases: DemoCase[];
  selectedCaseId: string;
  inputText: string;
  receiver: string;
  claimedEntity: string;
  channel: string;
  amount: string;
  isStudent: boolean;
  firstTimeTrade: boolean;
  analyzing: boolean;
  onSelectCase: (demoCase: DemoCase) => void;
  onInputTextChange: (value: string) => void;
  onReceiverChange: (value: string) => void;
  onClaimedEntityChange: (value: string) => void;
  onChannelChange: (value: string) => void;
  onAmountChange: (value: string) => void;
  onStudentChange: (value: boolean) => void;
  onFirstTimeTradeChange: (value: boolean) => void;
  onAnalyze: () => void;
  onReset: () => void;
}

export function InputPanel({
  cases,
  selectedCaseId,
  inputText,
  receiver,
  claimedEntity,
  channel,
  amount,
  isStudent,
  firstTimeTrade,
  analyzing,
  onSelectCase,
  onInputTextChange,
  onReceiverChange,
  onClaimedEntityChange,
  onChannelChange,
  onAmountChange,
  onStudentChange,
  onFirstTimeTradeChange,
  onAnalyze,
  onReset
}: InputPanelProps) {
  return (
    <section className="panel input-panel" aria-labelledby="input-title">
      <div className="panel-title-row">
        <div>
          <span className="panel-eyebrow">
            <FileText size={15} />
            输入
          </span>
          <h2 id="input-title">待评估内容</h2>
        </div>
        <button className="icon-button" type="button" onClick={onReset} aria-label="重置输入">
          <RotateCcw size={18} />
        </button>
      </div>

      <div className="case-grid" aria-label="演示案例">
        {cases.map((demoCase) => (
          <button
            className={`case-chip ${selectedCaseId === demoCase.id ? "active" : ""}`}
            key={demoCase.id}
            type="button"
            onClick={() => onSelectCase(demoCase)}
          >
            <span>{demoCase.title}</span>
            <small>{demoCase.group}</small>
          </button>
        ))}
      </div>

      <label className="field textarea-field">
        <span>聊天记录 / 交易描述 / 理财想法</span>
        <textarea value={inputText} onChange={(event) => onInputTextChange(event.target.value)} />
      </label>

      <div className="field-grid">
        <label className="field">
          <span>金额</span>
          <input value={amount} inputMode="decimal" onChange={(event) => onAmountChange(event.target.value)} />
        </label>
        <label className="field">
          <span>收款方</span>
          <input value={receiver} onChange={(event) => onReceiverChange(event.target.value)} />
        </label>
        <label className="field">
          <span>声称主体</span>
          <input value={claimedEntity} onChange={(event) => onClaimedEntityChange(event.target.value)} />
        </label>
        <label className="field">
          <span>渠道</span>
          <input value={channel} onChange={(event) => onChannelChange(event.target.value)} />
        </label>
      </div>

      <div className="toggle-row">
        <label className="toggle">
          <input checked={isStudent} type="checkbox" onChange={(event) => onStudentChange(event.target.checked)} />
          <span>
            <UserRoundCheck size={16} />
            学生用户
          </span>
        </label>
        <label className="toggle">
          <input
            checked={firstTimeTrade}
            type="checkbox"
            onChange={(event) => onFirstTimeTradeChange(event.target.checked)}
          />
          <span>
            <Sparkles size={16} />
            首次交易
          </span>
        </label>
      </div>

      <motion.button
        whileTap={{ scale: 0.985 }}
        className="analyze-button"
        type="button"
        onClick={onAnalyze}
        disabled={analyzing || inputText.trim().length === 0}
      >
        {analyzing ? <Play className="spin-soft" size={20} /> : <Send size={20} />}
        {analyzing ? "Agent Teams 推理中" : "开始冷静 30 秒"}
      </motion.button>
    </section>
  );
}
