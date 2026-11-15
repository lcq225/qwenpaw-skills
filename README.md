# QwenPaw Skills

QwenPaw 技能发布集（skills collection）。每个技能是一个 `SKILL.md` + 附属脚本，可通过 `qwenpaw skills install <URL>` 分发。

> **QwenPaw**: https://github.com/agentscope-ai/QwenPaw · Docs: https://qwenpaw.agentscope.io/

## 技能列表

| 技能 | 版本 | 说明 | 安装 |
|------|:----:|------|------|
| [wechat_publisher](skills/wechat_publisher/SKILL.md) | 1.0.0 | 公众号排版+草稿箱推送：Markdown→微信富排版 HTML（卡片/强调/表格）、12 套主题、图片与封面上传、草稿创建与回读验证 | `qwenpaw skills install <release-url>/WeChat-Publisher-v1.0.0.zip` |
| [tech-diagram](skills/tech-diagram/SKILL.md) | 1.0.0 | 技术架构图：6 类图型 + 7 套配色 → SVG + PNG + 可在 app.diagrams.net 编辑的 .drawio 活文件 | `qwenpaw skills install <release-url>/Tech-Diagram-v1.0.0.zip` |
| [data-analysis](skills/data-analysis/README.md) | 1.0.1 | 通用数据分析：文件/数据库/粘贴→诊断+EDA+多维下钻+同环比→Markdown/HTML报告 | `qwenpaw skills install <release-url>/Data-Analysis-v1.0.1.zip` |
| [web-extractor](skills/web-extractor/README.md) | 1.0.1 | 网页正文抓取+摘要：URL→干净正文 md/txt，可批量、可 LLM 摘要 | `qwenpaw skills install <release-url>/Web-Extractor-v1.0.1.zip` |
| [RapidOCR](skills/RapidOCR-Plugin/README.md) | 1.1.0 | 中文优先的本地 OCR + 文档解析：图片→纯文字，PDF/Office→版面+表格(HTML)，按类型自动路由，离线可用、无 API Key | `qwenpaw skills install <release-url>/RapidOCR-Plugin-v1.1.0.zip` |
| [evidence-ledger](skills/evidence-ledger/README.md) | 0.1.0 | 证据台账：把「主张—证据—来源—状态」结构化登记，冲突并置不选边，导出可追溯附表 | `qwenpaw skills install <release-url>/Evidence-Ledger-v0.1.0.zip` |
| [skill-publish-auditor](skills/skill-publish-auditor/README.md) | 0.1.0 | 技能公开发布前审计：来源/许可/隐私/frontmatter/依赖/zip 扁平结构，阻断冒充原创 | `qwenpaw skills install <release-url>/Skill-Publish-Auditor-v0.1.0.zip` |
| [connector-kit](skills/connector-kit/README.md) | 0.1.0 | 统一只读连接器底座：list/search/fetch 三接口，内置本地文档库适配器，凭据只走环境变量 | `qwenpaw skills install <release-url>/Connector-Kit-v0.1.0.zip` |

## 安装方式

### 方式一：从 Release 直接安装（推荐）

```bash
qwenpaw skills install https://github.com/lcq225/qwenpaw-skills/releases/download/v1.1.0/RapidOCR-Plugin-v1.1.0.zip
```

- 不带 `--agent-id` → 导入全局 skill_pool
- 带 `--agent-id <agent>` → 直接导入指定 agent workspace

### 方式二：本地目录安装

```bash
qwenpaw skills test <path>      # 校验技能
qwenpaw skills install <path>   # 从本地路径安装
```

## 目录结构

```
qwenpaw-skills/
├── README.md
├── LICENSE
├── skills/            # 技能源码（每个一个子目录）
│   └── RapidOCR-Plugin/
└── releases/          # 每次发布的 zip 包（对应 GitHub Release asset）
```

## 协议

本项目内容随 QwenPaw 技能生态发布，采用 [Apache-2.0](LICENSE)。
