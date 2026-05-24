# RiskRadar 提交材料说明

本压缩包用于比赛初赛材料整理与演示准备，默认围绕“金融 / 风控”主题组织。

## 文件清单

- `01-项目说明书.docx`
- `01-项目说明书-源稿.md`
- `02-Coze-Workflow-文案.md`
- `03-提交材料说明.md`
- `04-risk-radar-finance-control/`
- `04-risk-radar-finance-control.zip`
- `tools/build_project_doc.py`

## 使用建议

### 1. ArkClaw 提交

- 将 `04-risk-radar-finance-control` 作为 Skill 包基础目录使用
- 或直接上传 `04-risk-radar-finance-control.zip`
- 优先使用 `assets/arkclaw_test_prompts.md` 中的 4 组提示词做跑通截图
- 使用 `assets/sample_inputs.json` 做稳定样例
- 使用 `references/output_contract.md` 保持输出字段稳定
- 使用 `assets/expected_outputs.json` 和 `scripts/run_eval.py` 做回归测试，证明 Skill 在结构化输入和纯文本输入下都稳定

### 2. 项目说明书

- `01-项目说明书.docx` 可直接作为初赛 Word 版说明书提交
- 若需快速改字，请先改 `01-项目说明书-源稿.md`，再重新生成 docx

### 3. Coze 体验链接制作

- `02-Coze-Workflow-文案.md` 包含节点设计、Prompt 草案、评分代码和展示布局建议
- 建议在 Coze 中按“信息抽取 -> 知识库检索 -> 代码评分 -> 解释生成 -> 展示页”的顺序搭建

### 4. Demo 录屏与海报

- `04-risk-radar-finance-control/assets/demo_script.md` 可直接用作录屏讲稿
- `04-risk-radar-finance-control/assets/poster_copy.md` 可直接用于路演海报文案

## 建议的最终提交组合

1. Word 版项目说明书
2. ArkClaw 跑通的 Skill 包
3. Coze 体验链接
4. Demo 录屏视频
5. 路演海报
