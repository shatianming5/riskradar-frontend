import type {
  AnalysisResult,
  AnalyzePayload,
  FeatureMap,
  MatchedRule,
  RiskLevel
} from "./types";

type Rule = readonly [string, number, string];
type ComboRule = readonly [readonly string[], number, string];
type HardFloor = readonly [readonly string[], number, string];

const negationPrefixes = ["没有", "未", "不需要", "不要求", "不用", "无需", "不是", "并未", "别", "并没有"];

const riskRules: Rule[] = [
  ["upfront_fee", 25, "存在前置收费，如保证金、押金、解冻费或手续费"],
  ["off_platform", 20, "要求脱离官方平台交易"],
  ["personal_receiver_claims_official", 20, "个人账户冒充官方、学校、企业或平台主体"],
  ["asks_for_sensitive_credentials", 40, "要求验证码、支付密码、银行卡完整信息或身份证照片"],
  ["asks_for_screen_share", 40, "要求屏幕共享、远程控制或下载不明 App"],
  ["high_return", 20, "承诺高返利、稳赚不赔、肯定上涨或轻松赚钱"],
  ["urgency_pressure", 15, "制造紧迫感或施压，压缩核验时间"],
  ["entity_mismatch", 20, "沟通主体、交易主体和收款主体不一致"],
  ["cannot_verify", 15, "无法通过官方渠道核验"],
  ["student_or_first_time", 10, "用户是学生、新手或首次交易"],
  ["emotion_manipulation", 15, "使用保密、同情、恐吓或内疚等情绪操控"],
  ["identity_impersonation", 25, "冒充熟人、客服、老师、官方人员或机构"],
  ["third_party_receiver", 15, "要求向第三方收款人转账或代付"],
  ["unknown_product", 15, "不了解产品是什么、投什么或风险等级如何"],
  ["social_hype_only", 15, "主要根据群聊、老师带单、主播或同学推荐做决定"],
  ["leverage_or_borrowed_money", 25, "打算用借来的钱或分期去投资"],
  ["cashflow_mismatch", 20, "短期必用资金投入存在波动或锁定期的产品"],
  ["all_in_or_high_concentration", 15, "打算重仓、满仓或把大部分生活费压进去"],
  ["unknown_fee_or_redemption", 10, "不清楚费率、手续费、赎回规则或锁定期"]
];

const safeRules: Rule[] = [
  ["official_platform", -15, "可以在学校、平台、商家或官方流程内完成操作"],
  ["verified_receiver", -10, "收款主体已核验"],
  ["has_order_or_contract", -10, "提供了可验证订单、合同或平台记录"],
  ["official_double_check", -15, "已通过官方渠道二次核验"],
  ["official_licensed_platform", -10, "通过银行、券商、持牌基金销售或官方平台开户"],
  ["understands_product", -10, "能说清产品类型、底层资产和风险等级"],
  ["understands_fee_and_liquidity", -10, "已了解费率、赎回规则或到账时间"],
  ["spare_money_investment", -15, "使用闲钱、小额资金，不影响生活和学业"],
  ["small_position_or_diversified", -10, "小额试投、分散配置或明确不重仓"]
];

const comboRules: ComboRule[] = [
  [["off_platform", "upfront_fee"], 15, "脱离平台后先付费用，平台保障失效"],
  [["identity_impersonation", "urgency_pressure", "third_party_receiver"], 15, "身份未核验且要求紧急代付给第三方"],
  [["unknown_product", "social_hype_only", "high_return"], 20, "不了解产品却因群体跟风和收益承诺准备下单"],
  [["leverage_or_borrowed_money", "all_in_or_high_concentration"], 15, "借钱投资且仓位过重，抗风险能力明显不足"],
  [["cashflow_mismatch", "unknown_fee_or_redemption"], 15, "短期必用资金对应锁定期或赎回规则不清，流动性风险明显"]
];

const hardFloors: HardFloor[] = [
  [["asks_for_sensitive_credentials"], 80, "涉及验证码、支付密码或完整敏感凭证，最低极高风险"],
  [["asks_for_screen_share"], 80, "涉及屏幕共享或远程控制，最低极高风险"],
  [["off_platform", "upfront_fee"], 60, "脱离平台并要求先付款，最低高风险"],
  [["identity_impersonation", "third_party_receiver"], 70, "身份冒充并要求向第三方付款，最低高风险"],
  [["leverage_or_borrowed_money", "high_return"], 70, "借钱参与高收益或强上涨预期投资，最低高风险"]
];

const scenePatterns: Record<string, RegExp[]> = {
  兼职押金: [/兼职/, /保证金/, /资料费/, /培训费/, /入职/],
  二手交易: [/二手/, /卖家/, /定金/, /闲置/, /相机/, /平台手续费/],
  网购退款: [/退款/, /客服/, /退赔/, /账户异常/, /订单异常/],
  校园缴费: [/学校/, /学院/, /报名费/, /统一支付平台/, /辅导员/],
  "借款/校园贷": [/借钱/, /校园贷/, /征信/, /放款/, /分期/, /秒批/],
  理财决策: [/基金/i, /股票/, /黄金/, /ETF/i, /货币基金/, /宽基/, /指数基金/, /理财/, /费率/, /赎回/, /锁定期/, /T\+\d/i],
  社群荐投: [/基金交流群/, /群老师/, /带单/, /喊单/, /博主推荐/, /主播推荐/, /内幕消息/, /开户链接/, /直播间/, /短线群/],
  熟人借钱: [/同学/, /朋友/, /先帮忙转/, /晚上还我/, /手机坏了/],
  账号租借: [/租号/, /代实名/, /刷流水/, /账号/],
  "验证码/屏幕共享": [/验证码/, /共享屏幕/, /屏幕共享/, /远程/, /会议软件/],
  转账付款: [/转账/, /付款/, /付款码/, /打钱/]
};

const featurePatterns: Record<string, RegExp[]> = {
  upfront_fee: [/保证金/, /押金/, /认证费/, /解冻费/, /资料费/, /先交/, /先付/, /定金/, /先交.*手续费/, /手续费.*先交/],
  off_platform: [/不要走平台/, /加微信/, /私下转账/, /线下交易/, /跳出平台/, /平台手续费太高/, /平台外交易/, /私聊/, /不要去官方券商App搜/i, /群里链接/, /开户链接/, /非官方链接/, /私发链接/],
  personal_receiver_claims_official: [/官方.*微信/, /学校.*微信/, /客服.*个人收款/, /公司.*个人收款/, /企业.*个人收款/],
  asks_for_sensitive_credentials: [/验证码/, /支付密码/, /银行卡密码/, /银行卡完整信息/, /身份证照片/, /CVV/i, /短信码/],
  asks_for_screen_share: [/屏幕共享/, /共享屏幕/, /远程控制/, /远程协助/, /下载.*软件/, /会议软件/],
  high_return: [/高返利/, /稳赚/, /稳赚不赔/, /轻松赚钱/, /刷单/, /日结\d+/, /肯定还会涨/, /必涨/, /翻倍/, /保本保收益/, /三天至少涨\d+/, /一周回本/, /连续涨停/, /短期翻倍/],
  urgency_pressure: [/马上/, /立刻/, /十分钟内/, /10分钟内/, /名额有限/, /尽快/, /超时失效/, /不转后果/, /急需/, /很急/, /账户会被冻结/, /错过机会/, /不上车/, /今晚开盘前/, /收盘前/, /才有名额/],
  entity_mismatch: [/官方.*个人收款/, /学校.*个人收款/, /平台.*私人/, /收款主体不一致/, /转给.*朋友/],
  cannot_verify: [/不要核验/, /不能走平台/, /没有订单/, /先转再说/, /手机坏了/, /不方便视频/, /不方便电话/, /无法核验/, /自称/, /没有官方页面/, /找不到产品说明/, /搜不到产品代码/, /不让看详情/, /只给链接/, /不要去官方券商App搜/i],
  student_or_first_time: [/学生/, /第一次交易/, /新手/],
  emotion_manipulation: [/不要告诉别人/, /保密/, /帮帮我/, /不然就/, /求你了/, /否则/],
  identity_impersonation: [/我是你.*同学/, /自称.*同学/, /自称.*朋友/, /我是客服/, /自称.*客服/, /冒充.*客服/, /自称.*老师/, /自称.*辅导员/, /官方工作人员/, /平台客服/],
  third_party_receiver: [/转给.*朋友/, /转到.*朋友/, /第三方收款/, /代付/, /帮.*垫/],
  unknown_product: [/不了解/, /不清楚/, /看不懂/, /不知道这是什么/, /不知道.*投什么/, /不懂这个项目/, /没看过详情/, /没看说明/, /不清楚风险等级/, /没太看明白/, /不知道跟踪什么/, /不懂净值/],
  social_hype_only: [/群老师/, /老师带单/, /喊单/, /群友都在买/, /同学都在买/, /博主推荐/, /主播推荐/, /短视频看到/, /跟单/, /内幕消息/, /基金交流群/, /直播间/, /群里都在冲/, /短线群/, /热榜/],
  leverage_or_borrowed_money: [/借钱买/, /借钱炒股/, /借钱理财/, /花呗/, /借呗/, /校园分期/, /贷款买/, /生活费补仓/, /借来的钱/, /慢慢还/, /信用卡套现/],
  cashflow_mismatch: [/下个月房租/, /房租和生活费/, /学费先拿去买/, /生活费先买/, /一个月内要用的钱/, /短期要用的钱/, /马上要交房租/, /到时候应该能取出来/, /30天锁定期理财/],
  all_in_or_high_concentration: [/all in/i, /梭哈/, /满仓/, /全仓/, /全部压上/, /重仓/, /把生活费都投进去/],
  unknown_fee_or_redemption: [/不知道手续费/, /不知道费率/, /不知道多久能赎回/, /不知道锁定期/, /不清楚申赎规则/, /不清楚费用/, /手续费多少/, /没看提前赎回规则/, /没有细看提前赎回规则/, /不知道T\+\d/i, /不知道多久到账/, /多久能赎回/],
  official_platform: [/统一支付平台/, /平台内下单/, /平台内交易/, /平台担保/, /官方小程序/, /官方公众号/, /订单一致/, /平台内完成/],
  verified_receiver: [/收款主体显示为/, /实名认证/, /官方主体一致/, /收款主体一致/],
  has_order_or_contract: [/订单号/, /合同/, /工单/, /平台记录/],
  official_double_check: [/官方客服确认/, /辅导员群/, /学校通知/, /平台客服确认/, /辅导员转发/, /辅导员.*转发/],
  official_licensed_platform: [/官方银行App/i, /银行官方App/i, /官方券商App/i, /券商官方App/i, /持牌基金销售/, /银行官方渠道/, /券商官方渠道/, /银行理财专区/, /官网开户/],
  understands_product: [/知道它投什么/, /知道它主要做/, /了解底层资产/, /看过产品详情/, /看过基金详情/, /看过招募说明/, /看过产品说明/, /了解风险等级/, /主要做短期现金管理/, /知道跟踪什么指数/, /知道它跟踪/, /知道是宽基指数/, /知道会有波动/, /知道它不是保本/],
  understands_fee_and_liquidity: [/看过费率/, /看过手续费/, /看过申赎规则/, /知道可以随时赎回/, /知道锁定期/, /知道到账时间/, /知道T\+\d/i, /看过提前赎回规则/, /知道赎回到账/],
  spare_money_investment: [/闲钱/, /剩余生活费/, /不影响下月开销/, /可承受亏损/, /不是借钱买/, /每月拿\d+元闲钱/, /不动房租/, /不动学费/],
  small_position_or_diversified: [/先买少量/, /小额试投/, /分散/, /不重仓/, /不满仓/, /一小部分/, /定投/, /每月少量/, /先从\d+元开始/]
};

const featureKeys = [...riskRules, ...safeRules].map(([key]) => key);

function splitSentences(text: string): string[] {
  return text
    .split(/[。！？\n]+/)
    .map((item) => item.trim().replace(/^[,，；;]+|[,，；;]+$/g, ""))
    .filter(Boolean);
}

function isNegated(sentence: string, index: number) {
  const window = sentence.slice(Math.max(0, index - 8), index);
  return negationPrefixes.some((token) => window.includes(token));
}

function dedupe(items: string[]) {
  return Array.from(new Set(items.map((item) => item.trim()).filter(Boolean)));
}

function evidenceForPatterns(text: string, patterns: RegExp[]) {
  const evidence: string[] = [];
  for (const sentence of splitSentences(text)) {
    for (const pattern of patterns) {
      pattern.lastIndex = 0;
      const match = pattern.exec(sentence);
      if (match && !isNegated(sentence, match.index)) {
        evidence.push(sentence);
        break;
      }
    }
  }
  return evidence;
}

function inferScene(text: string, explicitScene?: string) {
  if (explicitScene) return explicitScene;
  for (const [scene, patterns] of Object.entries(scenePatterns)) {
    if (patterns.some((pattern) => pattern.test(text))) return scene;
  }
  return "转账付款";
}

function detectFeatures(payload: AnalyzePayload) {
  const combinedText = [
    payload.inputText,
    payload.receiver,
    payload.claimedEntity,
    payload.channel,
    payload.amount ? `金额 ${payload.amount}` : ""
  ]
    .filter(Boolean)
    .join("\n");

  const features: FeatureMap = Object.fromEntries(featureKeys.map((key) => [key, false]));
  const evidenceMap: Record<string, string[]> = Object.fromEntries(featureKeys.map((key) => [key, []]));
  const evidence: string[] = [];

  for (const [key, patterns] of Object.entries(featurePatterns)) {
    const matchedEvidence = evidenceForPatterns(combinedText, patterns);
    if (matchedEvidence.length > 0) {
      features[key] = true;
      evidenceMap[key].push(...matchedEvidence);
      evidence.push(...matchedEvidence);
    }
  }

  if (payload.isStudent || payload.firstTimeTrade) {
    features.student_or_first_time = true;
    evidenceMap.student_or_first_time.push("用户画像显示为学生、新手或首次交易");
  }

  const receiver = payload.receiver ?? "";
  const claimedEntity = payload.claimedEntity ?? "";
  if (receiver && claimedEntity) {
    const receiverLooksPersonal = ["微信", "支付宝", "个人"].some((token) => receiver.includes(token));
    const entityLooksOfficial = ["官方", "学校", "公司", "企业", "客服", "机构"].some((token) =>
      claimedEntity.includes(token)
    );
    if (receiverLooksPersonal && entityLooksOfficial) {
      const marker = `收款方为“${receiver}”，但声称主体为“${claimedEntity}”`;
      features.personal_receiver_claims_official = true;
      features.entity_mismatch = true;
      evidenceMap.personal_receiver_claims_official.push(marker);
      evidenceMap.entity_mismatch.push(marker);
      evidence.push(marker);
    }
  }

  if (receiver && ["朋友", "第三方", "代付", "他人"].some((token) => receiver.includes(token))) {
    features.third_party_receiver = true;
    evidenceMap.third_party_receiver.push(`收款方显示为“${receiver}”`);
  }

  if (payload.features) {
    for (const [key, value] of Object.entries(payload.features)) {
      if (key in features) {
        features[key] = value;
        if (value && evidenceMap[key].length === 0) {
          evidenceMap[key].push("结构化特征已明确标注为命中");
        }
        if (!value) evidenceMap[key] = [];
      }
    }
  }

  const scene = inferScene(combinedText, payload.scene);
  for (const key of Object.keys(evidenceMap)) evidenceMap[key] = dedupe(evidenceMap[key]);

  return {
    features,
    evidence: dedupe(evidence).slice(0, 6),
    scene,
    evidenceMap
  };
}

function levelFromScore(score: number): RiskLevel {
  if (score >= 80) return "极高风险";
  if (score >= 60) return "高风险";
  if (score >= 30) return "中风险";
  return "低风险";
}

function scoreRisk(features: FeatureMap, evidenceMap: Record<string, string[]>) {
  let score = 0;
  const matchedRules: MatchedRule[] = [];

  for (const [key, points, reason] of riskRules) {
    if (features[key]) {
      score += points;
      matchedRules.push({ key, points, reason, tag: "规则命中", evidence: evidenceMap[key] ?? [] });
    }
  }

  for (const [key, points, reason] of safeRules) {
    if (features[key]) {
      score += points;
      matchedRules.push({ key, points, reason, tag: "核验状态", evidence: evidenceMap[key] ?? [] });
    }
  }

  for (const [keys, points, reason] of comboRules) {
    if (keys.every((key) => features[key])) {
      score += points;
      matchedRules.push({
        key: keys.join("+"),
        points,
        reason,
        tag: "规则命中",
        evidence: dedupe(keys.flatMap((key) => evidenceMap[key] ?? []))
      });
    }
  }

  for (const [keys, minimum, reason] of hardFloors) {
    if (keys.every((key) => features[key]) && score < minimum) {
      score = minimum;
      matchedRules.push({
        key: keys.join("+"),
        points: 0,
        reason,
        tag: "硬规则",
        evidence: dedupe(keys.flatMap((key) => evidenceMap[key] ?? []))
      });
    }
  }

  if (!features.asks_for_sensitive_credentials && !features.asks_for_screen_share) {
    score = Math.min(score, 94);
  }

  score = Math.max(0, Math.min(100, Math.round(score)));
  return { score, level: levelFromScore(score), matchedRules };
}

function buildSummary(scene: string, level: RiskLevel, score: number, features: FeatureMap) {
  if (level === "低风险") {
    return `当前更像是可核验的 ${scene} 场景，风险分数 ${score}/100。仍建议保留凭证并确认主体一致。`;
  }
  if (features.asks_for_sensitive_credentials || features.asks_for_screen_share) {
    return `该请求已触发账户接管类强风险信号，建议立即停止验证码、屏幕共享或远程协助。`;
  }
  if (features.leverage_or_borrowed_money || features.unknown_product || features.social_hype_only) {
    return `这不是简单判断“能不能买”，核心风险在于产品信息不足、跟风压力或资金来源不健康。`;
  }
  return `当前 ${scene} 决策存在明显异常信号，建议先暂停付款并回到官方渠道核验。`;
}

function buildCalmQuestions(scene: string, features: FeatureMap) {
  if (scene === "理财决策" || scene === "社群荐投" || features.unknown_product) {
    return [
      "我能不能用自己的话说清楚这是什么产品、底层投什么、最坏会亏什么？",
      "这笔钱如果一个月内要用，或者亏损 10%-20%，我还能接受吗？",
      "我现在想买，是因为我看懂了，还是因为别人说“再不上车就晚了”？"
    ];
  }
  if (features.asks_for_sensitive_credentials || features.asks_for_screen_share) {
    return [
      "对方身份能否通过平台 App、官网客服或订单页独立核验？",
      "对方为什么需要验证码、屏幕共享、远程控制或完整银行卡信息？",
      "如果我现在断开联系，是否还能通过官方入口完成同一件事？"
    ];
  }
  return [
    "收款方、沟通方和声称的官方主体是否完全一致？",
    "这笔交易能否留在官方平台、学校平台或有担保的渠道内完成？",
    "对方是否用限时、名额、先交钱等方式压缩我的核验时间？"
  ];
}

function buildActions(level: RiskLevel, scene: string, features: FeatureMap) {
  if (level === "低风险") {
    return [
      "继续通过官方入口操作，不要改走私聊或个人收款码。",
      "保存订单、通知、付款凭证和主体核验截图。",
      "付款或下单前再次确认金额、收款主体和产品信息一致。"
    ];
  }

  if (scene === "理财决策" || scene === "社群荐投" || features.unknown_product) {
    return [
      "建议暂停下单，先补齐产品类型、底层资产、风险等级、费率和赎回规则。",
      "不要使用花呗、借呗、校园分期、房租、学费或短期要用的钱投资。",
      "回到银行、券商或持牌基金销售的官方渠道独立核验产品。",
      "把仓位降到可承受的小额试投范围，拒绝群聊带单和非官方开户链接。"
    ];
  }

  if (features.asks_for_sensitive_credentials || features.asks_for_screen_share) {
    return [
      "立即停止发送验证码、支付密码、身份证照片或银行卡完整信息。",
      "立刻关闭屏幕共享、远程控制和不明会议软件。",
      "通过平台 App 或官网客服重新核验订单和退款状态。",
      "若已经泄露信息，尽快冻结支付账户并保留聊天证据。"
    ];
  }

  return [
    "建议暂停付款，不要先交保证金、定金、资料费或解冻费。",
    "拒绝脱离平台、私下转账和个人收款码。",
    "通过学校、平台、官方客服或熟人本人电话做二次核验。",
    "保留聊天记录、收款码、链接和对方账号信息。"
  ];
}

function buildReplyTemplate(level: RiskLevel, scene: string, features: FeatureMap) {
  if (level === "低风险") {
    return "我会继续通过官方平台完成，并保留订单、通知和付款凭证。如果后续需要改到私下转账或补充敏感信息，我会重新核验。";
  }
  if (scene === "理财决策" || scene === "社群荐投" || features.unknown_product) {
    return "我先不跟单也不下单。我要先看清产品说明、风险等级、费率和赎回规则，并且只会通过官方持牌渠道、用不影响生活的闲钱再决定。";
  }
  if (features.asks_for_sensitive_credentials || features.asks_for_screen_share) {
    return "我不会提供验证码、支付密码或屏幕共享。请通过平台官方 App 或官网客服工单处理，我会自行从官方入口核验。";
  }
  return "我暂时不付款。请提供可在官方平台核验的订单、主体信息和收款方式，我只会在平台内或官方渠道完成交易。";
}

function buildRedTeamNotes(scene: string, features: FeatureMap) {
  if (features.asks_for_sensitive_credentials || features.asks_for_screen_share) {
    return ["对方可能继续用“账户冻结”“退款失败”施压。", "下一步常见动作是诱导开启共享屏幕或索要验证码。"];
  }
  if (scene === "社群荐投" || features.social_hype_only) {
    return ["群聊可能继续制造“名额有限”“今晚就涨”的氛围。", "非官方链接可能把开户、充值和下单绑定在同一条路径里。"];
  }
  if (features.off_platform && features.upfront_fee) {
    return ["对方可能先承诺返还，再追加认证费、解冻费或手续费。", "离开平台后，交易凭证和申诉链路会明显变弱。"];
  }
  return ["后续应重点观察是否追加付款、改收款方或要求保密。", "任何要求跳出官方渠道的变化都应重新评估。"];
}

export function analyzeRisk(payload: AnalyzePayload): AnalysisResult {
  const { features, evidence, scene, evidenceMap } = detectFeatures(payload);
  const { score, level, matchedRules } = scoreRisk(features, evidenceMap);
  const paymentRelated = ["转账付款", "二手交易", "兼职押金", "校园缴费", "熟人借钱", "网购退款"].includes(scene);
  const creditRelated = scene === "借款/校园贷" || Boolean(features.leverage_or_borrowed_money);
  const investmentRelated = ["理财决策", "社群荐投"].includes(scene);

  return {
    scene,
    score,
    level,
    matchedRules,
    evidence,
    features,
    paymentRelated,
    creditRelated,
    investmentRelated,
    summary: buildSummary(scene, level, score, features),
    calmQuestions: buildCalmQuestions(scene, features),
    nextActions: buildActions(level, scene, features),
    replyTemplate: buildReplyTemplate(level, scene, features),
    redTeamNotes: buildRedTeamNotes(scene, features)
  };
}

export function getLevelClass(level: RiskLevel) {
  if (level === "极高风险") return "level-critical";
  if (level === "高风险") return "level-high";
  if (level === "中风险") return "level-medium";
  return "level-low";
}
