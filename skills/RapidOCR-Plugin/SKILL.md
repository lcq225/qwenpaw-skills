---
name: RapidOCR
description: Use when the user needs to extract text from an image, PDF-scan, screenshot, or picture — OCR / 图片文字识别 / 扫描件转文字 / 截图识字 / 抠图文字. Triggered on tasks like 识别图片文字、把图片转成文本、截图里的字抄出来、扫描件PDF抢救。Chinese-first OCR powered by RapidOCR (ONNX Runtime); no API key needed, works offline, auto-installs dependencies on first use.
version: 1.0.1
---

# RapidOCR — 图片文字识别

## Overview

识别图片/截图/扫描件中的文字，返回纯文本。基于 **RapidOCR（ONNX Runtime）**，中文优先、离线可用、无 API Key、轻量（≈15MB）、比传统引擎快 3–5 倍。

> 通用 OCR 后端（不依赖 tesseract），适用于扫描 PDF 文字抢救、桌面自动化截图识字、图片转文字等场景。

## When to Use

- 用户给出**图片/截图/扫描件**，要提取其中的文字
- PDF 是扫描版（无文字层）需 OCR 转可搜索
- 桌面自动化中识别屏幕/窗口上的文字位置
- 图片转 Markdown / 复制截图里的字

## Quick Start

```python
from RapidOCR import recognize

r = recognize("图片.png")
print(r["full_text"])      # 全部文字（换行分隔）
print(r["text_count"])     # 文本块数
```

## CLI 用法（用户也可能直接命令行调用）

```bash
python recognize.py 图片.png            # 打印识别文本
python recognize.py 图片.png -o out.txt # 输出到文件
python recognize.py --screenshot         # 截全屏识别
```

## API

| 函数 | 说明 |
|------|------|
| `recognize(path)` | 识别图片文件 → dict |
| `extract_text(path)` | 只返回纯文本字符串 |
| `screenshot()` | 截屏识别（需 PIL）|
| `RapidOCRSkill().recognize_base64(b64)` | 从 Base64 识别 |

返回结构：`{success, full_text, text_count, texts:[{text,confidence,bbox}], source, elapse}`

## Dependencies

- `rapidocr_onnxruntime`（首次使用自动 pip 安装）
- `PIL`（仅截图识别需要，可选）

## Install to a workspace / global pool

```bash
# workspace 局部（优先）— 整体拷入 skills/
copy /y RapidOCR-Plugin <你的workspace>\skills\RapidOCR-Plugin

# 或只拷子包到现成技能目录
copy /y RapidOCR-Plugin\RapidOCR <你的workspace>\skills\RapidOCR\
copy /y RapidOCR-Plugin\SKILL.md <你的workspace>\skills\RapidOCR\
# 全局 skill_pool 同理，并在 skill_pool/skill.json 的 skills 字典登记同名入口
```

## Common Mistakes

- **路径乱码**：中文路径需确保脚本 `sys.stdout` 走 UTF-8（见 `recognize.py` 头部）。
- **首次慢**：首次运行自动下载 ONNX 模型，稍等；之后秒级。
- **不依赖 tesseract**：RapidOCR 已覆盖常见 OCR 需求，无需再装额外引擎。
