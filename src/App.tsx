import { useMemo, useState } from "react";
import { AgentTrace } from "./components/AgentTrace";
import { ActionPanel } from "./components/ActionPanel";
import { BrandHeader } from "./components/BrandHeader";
import { InputPanel } from "./components/InputPanel";
import { RiskGauge } from "./components/RiskGauge";
import { defaultCase, demoCases } from "./data/cases";
import { analyzeRisk } from "./lib/analyzer";
import { analyzeWithBackend } from "./lib/api";
import type { DemoCase, FeatureMap } from "./lib/types";

function amountFromText(text: string) {
  const match = text.match(/(\d+(?:\.\d+)?)\s*元?/);
  return match?.[1] ?? "";
}

export default function App() {
  const [selectedCaseId, setSelectedCaseId] = useState(defaultCase.id);
  const [inputText, setInputText] = useState(defaultCase.inputText);
  const [receiver, setReceiver] = useState(defaultCase.receiver);
  const [claimedEntity, setClaimedEntity] = useState(defaultCase.claimedEntity);
  const [channel, setChannel] = useState(defaultCase.channel);
  const [amount, setAmount] = useState(amountFromText(defaultCase.inputText));
  const [isStudent, setIsStudent] = useState(defaultCase.profile.userType === "student");
  const [firstTimeTrade, setFirstTimeTrade] = useState(defaultCase.profile.firstTimeTrade);
  const [caseFeatures, setCaseFeatures] = useState<FeatureMap | undefined>(defaultCase.features);
  const [analyzing, setAnalyzing] = useState(false);
  const [activeStep, setActiveStep] = useState(3);
  const [result, setResult] = useState(() =>
    analyzeRisk({
      inputText: defaultCase.inputText,
      amount: amountFromText(defaultCase.inputText),
      receiver: defaultCase.receiver,
      claimedEntity: defaultCase.claimedEntity,
      channel: defaultCase.channel,
      scene: defaultCase.scene,
      isStudent: true,
      firstTimeTrade: defaultCase.profile.firstTimeTrade,
      features: defaultCase.features
    })
  );

  const currentScene = useMemo(() => {
    return selectedCaseId === "custom"
      ? undefined
      : demoCases.find((demoCase) => demoCase.id === selectedCaseId)?.scene;
  }, [selectedCaseId]);

  function markCustom() {
    setSelectedCaseId("custom");
    setCaseFeatures(undefined);
  }

  function selectCase(demoCase: DemoCase) {
    setSelectedCaseId(demoCase.id);
    setInputText(demoCase.inputText);
    setReceiver(demoCase.receiver);
    setClaimedEntity(demoCase.claimedEntity);
    setChannel(demoCase.channel);
    setAmount(amountFromText(demoCase.inputText));
    setIsStudent(demoCase.profile.userType === "student");
    setFirstTimeTrade(demoCase.profile.firstTimeTrade);
    setCaseFeatures(demoCase.features);
    setResult(
      analyzeRisk({
        inputText: demoCase.inputText,
        amount: amountFromText(demoCase.inputText),
        receiver: demoCase.receiver,
        claimedEntity: demoCase.claimedEntity,
        channel: demoCase.channel,
        scene: demoCase.scene,
        isStudent: demoCase.profile.userType === "student",
        firstTimeTrade: demoCase.profile.firstTimeTrade,
        features: demoCase.features
      })
    );
  }

  function resetToDefault() {
    selectCase(defaultCase);
  }

  async function analyzeCurrentInput() {
    const payload = {
      inputText,
      amount,
      receiver,
      claimedEntity,
      channel,
      scene: currentScene,
      isStudent,
      firstTimeTrade,
      features: caseFeatures
    };

    setAnalyzing(true);
    setActiveStep(0);

    const checkpoints = [1, 2, 3];
    checkpoints.forEach((step, index) => {
      window.setTimeout(() => setActiveStep(step), 280 * (index + 1));
    });

    try {
      const remoteResult = await analyzeWithBackend(payload);
      setResult(remoteResult);
    } catch {
      const fallbackResult = analyzeRisk(payload);
      setResult({
        ...fallbackResult,
        backendStatus: "fallback",
        redTeamNotes: [
          "后端 Agent 服务暂不可用，已自动回退到浏览器本地规则分析。",
          ...fallbackResult.redTeamNotes
        ]
      });
    } finally {
      setAnalyzing(false);
      setActiveStep(3);
    }
  }

  return (
    <main className="app-shell">
      <div className="ambient-number" aria-hidden="true">
        2026
      </div>
      <BrandHeader totalCases={demoCases.length} />

      <div className="workspace">
        <InputPanel
          cases={demoCases}
          selectedCaseId={selectedCaseId}
          inputText={inputText}
          receiver={receiver}
          claimedEntity={claimedEntity}
          channel={channel}
          amount={amount}
          isStudent={isStudent}
          firstTimeTrade={firstTimeTrade}
          analyzing={analyzing}
          onSelectCase={selectCase}
          onInputTextChange={(value) => {
            markCustom();
            setInputText(value);
          }}
          onReceiverChange={(value) => {
            markCustom();
            setReceiver(value);
          }}
          onClaimedEntityChange={(value) => {
            markCustom();
            setClaimedEntity(value);
          }}
          onChannelChange={(value) => {
            markCustom();
            setChannel(value);
          }}
          onAmountChange={(value) => {
            markCustom();
            setAmount(value);
          }}
          onStudentChange={(value) => {
            markCustom();
            setIsStudent(value);
          }}
          onFirstTimeTradeChange={(value) => {
            markCustom();
            setFirstTimeTrade(value);
          }}
          onAnalyze={analyzeCurrentInput}
          onReset={resetToDefault}
        />

        <RiskGauge result={result} analyzing={analyzing} />
        <ActionPanel result={result} />
      </div>

      <AgentTrace result={result} activeStep={activeStep} analyzing={analyzing} />
    </main>
  );
}
