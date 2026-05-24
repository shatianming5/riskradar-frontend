# RiskRadar Coze Workflow 文案

## 一句话定位

RiskRadar 是一个面向大学生和年轻用户的个人金融风险控制 Agent，帮助用户在转账、兼职押金、二手交易、校园缴费、借款、退款、账户安全、基金股票黄金等理财决策与社群荐投场景中，在关键决策前 30 秒完成风险识别、证据解释和冷静行动建议。

## Workflow 总目标

把用户输入的聊天记录、交易描述或理财决策信息，转成以下固定输出：

1. 风险等级
2. 风险分数
3. 场景判断
4. 判断依据
5. 可疑证据 / 信息缺口
6. 三问冷静卡
7. 下一步行动
8. 可直接复制的安全回复

## 节点总览

```text
用户输入
  ↓
信息抽取节点
  ↓
知识库检索节点
  ↓
代码评分节点
  ↓
解释生成节点
  ↓
展示页输出节点
```

## 节点 1：用户输入

### 输入方式

- 文本输入：聊天记录、短信、付款要求、链接文案、理财推荐话术
- 表单输入：金额、收款方、交易用途、付款渠道、是否要求立即付款
- 理财补充：产品名称、是否知道底层投向、是否了解费率与赎回规则、资金是否来自闲钱
- 用户画像：是否学生、是否第一次交易、是否在平台内交易

### 建议表单字段

| 字段名 | 类型 | 示例 |
| --- | --- | --- |
| `input_text` | 长文本 | 粘贴聊天记录 |
| `amount` | 数字 | 199 |
| `receiver` | 文本 | 个人微信收款码 |
| `channel` | 文本 | 微信群兼职 |
| `is_student` | 布尔 | true |
| `first_time_trade` | 布尔 | true |
| `official_platform` | 布尔 | false |
| `product_name` | 文本 | 黄金主题基金 |
| `uses_borrowed_money` | 布尔 | false |
| `understands_product` | 布尔 | false |
| `understands_fee_and_liquidity` | 布尔 | false |

## 节点 2：信息抽取节点

### 目标

从用户输入中抽取结构化字段，并识别主场景标签。

### 建议 Prompt

```text
你是大学生个人金融风控信息抽取助手。请阅读用户输入，输出 JSON，不要输出任何额外解释。

请抽取以下字段：
- scene: 从“转账付款、二手交易、兼职押金、网购退款、校园缴费、借款/校园贷、理财决策、社群荐投、熟人借钱、账号租借、验证码/屏幕共享”中选择一个最主要场景
- amount: 金额，没有则填 null
- receiver: 收款主体或收款方式
- relationship: 用户与对方关系，例如陌生人、卖家、熟人、客服
- channel: 交易或沟通渠道
- product_name: 如果是理财场景，产品名称或标的，没有则填 null
- urgency: 是否存在立刻付款、限时、催促
- off_platform: 是否要求离开官方平台交易
- upfront_fee: 是否要求先交保证金、定金、资料费、手续费
- asks_for_sensitive_credentials: 是否要求验证码、支付密码、银行卡完整信息、身份证照片
- asks_for_screen_share: 是否要求屏幕共享、远程控制、下载不明 App
- high_return: 是否承诺高返利、稳赚、轻松赚钱
- cannot_verify: 是否无法通过官方渠道核验
- unknown_product: 是否不了解产品是什么、投什么、风险等级如何
- social_hype_only: 是否主要因为群聊、博主、同学、老师带单而想下单
- uses_borrowed_money: 是否打算用花呗、借呗、校园分期、借来的钱投资
- all_in_or_high_concentration: 是否准备重仓、满仓、梭哈或把生活费压进去
- understands_fee_and_liquidity: 是否明确了解费率、赎回规则、锁定期或到账时间
- evidence: 提取 3 到 5 条最关键原文证据
```

## 节点 3：知识库检索节点

### 推荐知识库内容

- 风险类型词典
- 风控评分规则
- Demo 案例库
- 大学生理财风控检查表
- 核验建议模板
- 安全回复模板

### 检索目标

- 给解释生成节点提供案例参照
- 给用户展示更稳定的风控术语
- 确保输出更像产品而不是自由闲聊

## 节点 4：代码评分节点

### 目标

根据抽取结果计算稳定的风险分数，避免纯模型输出波动，并让理财场景中的“信息不足”也能被解释为风控信号。

### 建议代码节点逻辑

```javascript
const riskRules = [
  ["upfront_fee", 25, "存在前置收费"],
  ["off_platform", 20, "要求脱离平台交易"],
  ["personal_receiver_claims_official", 20, "个人账户冒充官方主体"],
  ["asks_for_sensitive_credentials", 40, "要求验证码或敏感支付信息"],
  ["asks_for_screen_share", 40, "要求屏幕共享或远程控制"],
  ["high_return", 20, "承诺高返利、高收益或保本保收益"],
  ["urgency", 15, "制造紧迫感"],
  ["cannot_verify", 15, "无法通过官方渠道核验"],
  ["identity_impersonation", 25, "存在身份冒充风险"],
  ["unknown_product", 15, "不了解产品投什么或风险等级"],
  ["social_hype_only", 15, "主要基于群聊、博主或带单推荐决定"],
  ["uses_borrowed_money", 25, "计划用借来的钱或分期去投资"],
  ["all_in_or_high_concentration", 15, "准备重仓或把生活费压进去"],
  ["unknown_fee_or_redemption", 10, "不清楚费率、锁定期或赎回规则"]
];

const safeRules = [
  ["official_platform", -15, "可在官方平台内完成交易"],
  ["verified_receiver", -10, "收款主体已核验"],
  ["official_double_check", -15, "已通过官方渠道二次核验"],
  ["official_licensed_platform", -10, "通过银行、券商或持牌机构官方渠道查看产品"],
  ["understands_product", -10, "能说清产品类型、底层资产和风险等级"],
  ["understands_fee_and_liquidity", -10, "已了解费率、赎回规则或到账时间"],
  ["spare_money_investment", -15, "使用闲钱、小额资金，不影响生活和学业"],
  ["small_position_or_diversified", -10, "小额试投、分散配置或明确不重仓"]
];

let score = 0;
let reasons = [];

for (const [key, points, reason] of riskRules) {
  if (input[key]) {
    score += points;
    reasons.push(`${points > 0 ? "+" : ""}${points}: ${reason}`);
  }
}

for (const [key, points, reason] of safeRules) {
  if (input[key]) {
    score += points;
    reasons.push(`${points}: ${reason}`);
  }
}

score = Math.max(0, Math.min(100, score));

let level = "低风险";
if (score >= 80) level = "极高风险";
else if (score >= 60) level = "高风险";
else if (score >= 30) level = "中风险";

return {
  score,
  level,
  reasons
};
```

## 节点 5：解释生成节点

### 目标

把结构化结果转成用户能立刻行动的自然语言输出。

### 建议 Prompt

```text
你是一个大学生个人金融风险控制 Agent。请根据输入的场景、风险分数、规则原因、证据和信息缺口，生成稳定、简洁、可执行的中文输出。

请严格按以下顺序输出：
1. 风险等级
2. 风险分数
3. 场景判断
4. 判断依据
5. 可疑证据 / 信息缺口
6. 三问冷静卡
7. 下一步行动
8. 可直接复制的安全回复

要求：
- 判断依据控制在 3 到 5 条
- 三问冷静卡必须恰好 3 条
- 下一步行动控制在 3 到 5 条
- 语气冷静、直接、保护用户
- 不要给出“百分百安全”或“百分百诈骗”的绝对结论
- 高风险时必须明确写出“建议暂停付款”“建议暂停下单”或“立即停止敏感操作”
- 如果是理财场景且没有明显诈骗证据，优先指出“产品信息不足、费用不清、资金来源不合适”等问题，不要一律写成诈骗
```

## 节点 6：展示页输出节点

### 页面布局建议

- 左侧卡片：用户输入原文
- 中间卡片：风险分数、风险等级、场景判断
- 右侧卡片：三问冷静卡、下一步行动、安全回复模板

### 推荐展示元素

- 分数仪表盘：例如 `86 / 100`
- 风险等级颜色：
  - 低风险：绿色
  - 中风险：黄色
  - 高风险：橙色
  - 极高风险：红色
- 可疑证据卡片：突出原文短句

## Demo 推荐顺序

1. 先演示兼职押金案例，快速打出“极高风险”
2. 再演示虚假客服退款案例，体现账户安全硬风控
3. 再演示“理财项目不了解”案例，体现大学生理财信息缺口识别
4. 最后演示正常校园缴费或低风险理财，体现系统不会一刀切

## 评审讲解话术

- ArkClaw Skill 负责专业风控判断逻辑
- Coze Workflow 负责前端交互和可视化展示
- 规则引擎保证稳定性和可解释性
- 多 Agent 结构体现 Agent 创新性，而不是普通问答
- 项目不是只做反诈，而是覆盖支付、账户安全、借贷和理财决策的大学生个人金融风控
