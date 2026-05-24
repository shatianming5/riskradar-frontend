import type { DemoCase } from "../lib/types";

export const demoCases: DemoCase[] = [
  {
    id: "part_time_deposit",
    title: "兼职押金",
    group: "支付与交易",
    scene: "兼职押金",
    inputText:
      "同学你好，我们这边有校园兼职，日结300。需要先交99元资料保证金，明天入职后返还。名额有限，10分钟内付款。不要走平台，直接微信转账。",
    receiver: "个人微信收款码",
    claimedEntity: "校园兼职官方渠道",
    channel: "微信群兼职",
    profile: { userType: "student", firstTimeTrade: true },
    features: {
      upfront_fee: true,
      off_platform: true,
      high_return: true,
      urgency_pressure: true,
      student_or_first_time: true,
      cannot_verify: true,
      personal_receiver_claims_official: true,
      entity_mismatch: true
    }
  },
  {
    id: "fake_customer_service_refund",
    title: "虚假客服退款",
    group: "账户安全",
    scene: "网购退款",
    inputText:
      "我是平台客服，你的订单异常可以退款。请下载会议软件打开屏幕共享，并把短信验证码发给我，否则账户会被冻结。",
    receiver: "未知",
    claimedEntity: "平台客服",
    channel: "短信/即时聊天",
    profile: { userType: "student", firstTimeTrade: false },
    features: {
      asks_for_sensitive_credentials: true,
      asks_for_screen_share: true,
      urgency_pressure: true,
      identity_impersonation: true,
      cannot_verify: true
    }
  },
  {
    id: "investment_unknown_product",
    title: "黄金基金群荐",
    group: "理财决策",
    scene: "社群荐投",
    inputText:
      "同学拉我进了一个基金交流群，说这只黄金主题基金最近肯定还会涨。可我其实不知道它具体投什么、手续费多少、多久能赎回，只是感觉大家都在买，不上车就错过机会了。",
    receiver: "基金销售链接",
    claimedEntity: "基金交流群老师",
    channel: "群聊",
    profile: { userType: "student", firstTimeTrade: true },
    features: {
      social_hype_only: true,
      unknown_product: true,
      unknown_fee_or_redemption: true,
      high_return: true,
      urgency_pressure: true
    }
  },
  {
    id: "borrowed_money_invest",
    title: "借钱买黄金 ETF",
    group: "理财决策",
    scene: "理财决策",
    inputText:
      "我想用花呗和校园分期买黄金ETF，最近涨得快，我感觉肯定还会继续涨，准备先重仓进去，亏了以后再慢慢还。我还没太看明白它的风险和手续费。",
    receiver: "券商或基金平台",
    claimedEntity: "黄金ETF",
    channel: "理财 App",
    profile: { userType: "student", firstTimeTrade: false },
    features: {
      leverage_or_borrowed_money: true,
      all_in_or_high_concentration: true,
      unknown_product: true,
      unknown_fee_or_redemption: true,
      high_return: true
    }
  },
  {
    id: "official_campus_fee",
    title: "正常校园缴费",
    group: "低风险对照",
    scene: "校园缴费",
    inputText:
      "学院公众号发布活动报名通知，报名费20元，付款链接跳转到学校统一支付平台，收款主体显示为中山大学，辅导员群里也转发了通知。",
    receiver: "中山大学统一支付平台",
    claimedEntity: "中山大学",
    channel: "学院公众号",
    profile: { userType: "student", firstTimeTrade: false },
    features: {
      official_platform: true,
      verified_receiver: true,
      official_double_check: true
    }
  },
  {
    id: "second_hand_camera",
    title: "二手相机定金",
    group: "支付与交易",
    scene: "二手交易",
    inputText:
      "我在二手平台买相机，卖家说平台手续费太高，让我加微信聊。他说先转500定金，剩下货到付款。",
    receiver: "个人微信",
    claimedEntity: "二手平台卖家",
    channel: "二手平台转微信",
    profile: { userType: "student", firstTimeTrade: false },
    features: {
      off_platform: true,
      upfront_fee: true,
      cannot_verify: true
    }
  },
  {
    id: "teacher_stock_link",
    title: "群老师开户链接",
    group: "理财决策",
    scene: "社群荐投",
    inputText:
      "一个群老师说今晚有内部消息，让大家通过他发的开户链接开户买某只小盘股，保证三天至少涨20%。他说不要去官方券商App搜，跟着群里开户链接操作才有名额。",
    receiver: "群里开户链接",
    claimedEntity: "群老师",
    channel: "股票交流群",
    profile: { userType: "student", firstTimeTrade: true },
    features: {
      social_hype_only: true,
      off_platform: true,
      high_return: true,
      urgency_pressure: true,
      cannot_verify: true,
      unknown_product: true
    }
  },
  {
    id: "low_risk_money_fund",
    title: "低风险货币基金",
    group: "低风险对照",
    scene: "理财决策",
    inputText:
      "我准备把本月剩余生活费的一小部分放在银行官方App里的货币基金，已经看过风险等级、费率和申赎规则，知道它主要做短期现金管理，不是借钱买，也不影响下月开销。",
    receiver: "银行官方App",
    claimedEntity: "货币基金",
    channel: "银行官方渠道",
    profile: { userType: "student", firstTimeTrade: false },
    features: {
      official_licensed_platform: true,
      understands_product: true,
      understands_fee_and_liquidity: true,
      spare_money_investment: true,
      small_position_or_diversified: true
    }
  }
];

export const defaultCase = demoCases[0];
