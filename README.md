# QwenPaw Skills

QwenPaw 技能发布集（skills collection）。每个技能是一个 `SKILL.md` + 附属脚本，可通过 `qwenpaw skills install <URL>` 分发。

> **QwenPaw**: https://github.com/agentscope-ai/QwenPaw · Docs: https://qwenpaw.agentscope.io/

## 技能列表

| 技能 | 版本 | 说明 | 安装 |
|------|:----:|------|------|
| [RapidOCR](skills/RapidOCR-Plugin/README.md) | 1.0.1 | 中文优先的本地 OCR：图片/截图/扫描件转文字，离线可用、无 API Key | `qwenpaw skills install <release-url>/RapidOCR-Plugin-v1.0.1.zip` |

## 安装方式

### 方式一：从 Release 直接安装（推荐）

```bash
qwenpaw skills install https://github.com/lcq225/qwenpaw-skills/releases/download/v1.0.1/RapidOCR-Plugin-v1.0.1.zip
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
