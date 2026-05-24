import { useState } from "react";
import { Check, ClipboardCheck, Copy, MessageCircleQuestion, ShieldCheck } from "lucide-react";
import type { AnalysisResult } from "../lib/types";

interface ActionPanelProps {
  result: AnalysisResult;
}

export function ActionPanel({ result }: ActionPanelProps) {
  const [copied, setCopied] = useState(false);

  async function copyReply() {
    await navigator.clipboard.writeText(result.replyTemplate);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return (
    <section className="panel action-panel" aria-labelledby="action-title">
      <div className="panel-title-row">
        <div>
          <span className="panel-eyebrow">
            <ShieldCheck size={15} />
            行动
          </span>
          <h2 id="action-title">冷静卡</h2>
        </div>
      </div>

      <div className="action-section questions">
        <h3>
          <MessageCircleQuestion size={17} />
          三问冷静卡
        </h3>
        <ol>
          {result.calmQuestions.map((question) => (
            <li key={question}>{question}</li>
          ))}
        </ol>
      </div>

      <div className="action-section">
        <h3>
          <ClipboardCheck size={17} />
          下一步行动
        </h3>
        <ul>
          {result.nextActions.map((action) => (
            <li key={action}>{action}</li>
          ))}
        </ul>
      </div>

      <div className="reply-card">
        <div>
          <h3>安全回复模板</h3>
          <p>{result.replyTemplate}</p>
        </div>
        <button type="button" onClick={copyReply}>
          {copied ? <Check size={17} /> : <Copy size={17} />}
          {copied ? "已复制" : "复制"}
        </button>
      </div>
    </section>
  );
}
