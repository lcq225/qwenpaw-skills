# QwenPaw Skills

一个集中托管多个可分发 **QwenPaw 技能**的开源仓库。每个技能是「SKILL.md + 附属脚本」，打包成**扁平 zip**（SKILL.md 在根）通过 GitHub Release 发布，用 `qwenpaw skills install <URL>` 一键安装到 workspace 或全局 skill_pool。

> **QwenPaw**：https://github.com/agentscope-ai/QwenPaw · **Docs**：https://qwenpaw.agentscope.io/

## 技能列表

共 **8 个技能**，按用途分三类：

### 文档与数据处理

| 技能 | 版本 | 说明 |
|------|:----:|------|
| [RapidOCR](skills/RapidOCR-Plugin/README.md) | 1.1.0 | 本地 OCR + 文档解析：图片→纯文字，PDF/Office→版面+表格(HTML)，按类型自动路由，离线无 API Key |
| [data-analysis](skills/data-analysis/README.md) | 1.0.1 | 通用数据分析：文件/数据库/粘贴→诊断 + EDA + 多维下钻 + 同环比→Markdown/HTML 报告 |
| [web-extractor](skills/web-extractor/README.md) | 1.0.1 | 网页正文抓取 + 摘要：URL→干净正文 md/txt，可批量、可 LLM 摘要 |

### 办公与可视化

| 技能 | 版本 | 说明 |
|------|:----:|------|
| [wechat_publisher](skills/wechat_publisher/SKILL.md) | 1.0.0 | 公众号排版 + 草稿箱推送：Markdown→微信富排版 HTML（卡片/强调/表格）、12 套主题、图片上传、草稿创建 |
| [tech-diagram](skills/tech-diagram/SKILL.md) | 1.0.0 | 技术架构图：6 类图型 + 7 套配色 → SVG + PNG + 可编辑 .drawio 活文件 |

### 工程支撑

| 技能 | 版本 | 说明 |
|------|:----:|------|
| [evidence-ledger](skills/evidence-ledger/README.md) | 0.1.0 | 证据台账：把「主张—证据—来源—状态」结构化登记，冲突并置不选边，导出可追溯附表 |
| [skill-publish-auditor](skills/skill-publish-auditor/README.md) | 0.1.0 | 技能公开发布前审计：来源/许可/隐私/frontmatter/依赖/zip 扁平结构，阻断冒充原创 |
| [connector-kit](skills/connector-kit/README.md) | 0.1.0 | 统一只读连接器底座：list/search/fetch 三接口，内置本地文档库适配器，凭据只走环境变量 |

## 安装

### 方式一：从 Release 直接安装（推荐）

```bash
# 通用形式（tag 见下「发布约定」）
qwenpaw skills install https://github.com/lcq225/qwenpaw-skills/releases/download/<tag>/<asset>.zip

# 示例：RapidOCR
qwenpaw skills install https://github.com/lcq225/qwenpaw-skills/releases/download/v1.1.0/RapidOCR-Plugin-v1.1.0.zip
```

- 不带 `--agent-id` → 导入全局 skill_pool
- 带 `--agent-id <agent>` → 直接导入指定 agent workspace

各技能的完整 tag 与 asset 对应见各 Release 页（[Releases](https://github.com/lcq225/qwenpaw-skills/releases)）。

### 方式二：本地目录安装

```bash
qwenpaw skills test <path>      # 校验技能
qwenpaw skills install <path>   # 从本地路径安装
```

## 目录结构

```
qwenpaw-skills/
├── README.md          # 本文件（项目总览）
├── LICENSE            # Apache-2.0
├── .gitattributes     # 跨平台强制 text eol=lf（*.py/*.md/*.sh 等）
├── skills/            # 技能源码（每个技能一个子目录）
│   ├── RapidOCR-Plugin/
│   ├── data-analysis/
│   ├── web-extractor/
│   ├── wechat_publisher/
│   ├── tech-diagram/
│   ├── evidence-ledger/
│   ├── skill-publish-auditor/
│   └── connector-kit/
└── releases/          # 发布 zip（对应 GitHub Release asset）
```

## 发布约定

- **独立 tag**：每个技能用独立 tag，格式「技能名-版本」（如 `web-extractor-v1.0.1`、`tech-diagram-v1.0.0`）。RapidOCR 历史沿用了纯版本号（`v1.0.1`、`v1.1.0`），新技能一律用带前缀格式。
- **扁平 zip**：zip 内 `SKILL.md` 必须在**根目录**（勿带 `技能名/` 包装层），否则 `skills install` 找不到 SKILL.md。
- **隐私审计**：发布前逐文件核查，无本机绝对路径、无真实身份/公司名、无 token/API key，并排除 `__pycache__`。
- **跨平台**：`.gitattributes` 强制文本文件 `eol=lf`，保证 shebang 与脚本在 Linux/macOS 可执行。

## 许可证

本项目采用 [Apache-2.0](LICENSE) 许可证。
