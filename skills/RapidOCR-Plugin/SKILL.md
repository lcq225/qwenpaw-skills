---
name: RapidOCR
description: Use when the user needs to extract text from an image, PDF, screenshot, or picture, or parse a document into structured Markdown/HTML tables — OCR / 图片文字识别 / 扫描件转文字 / 截图识字 / 抠图文字 / 文档解析 / PDF转Markdown / 表格还原 / 版面理解. Auto-routes by input type: images→RapidOCR(纯文字), PDF/Office→RapidDoc(版面+表格). Chinese-first, offline, no API key.
version: 1.1.0
---

# RapidOCR — 图片文字识别

## Overview

识别图片/截图/扫描件中的文字，或解析 PDF/Office 文档为结构化 Markdown（表格转 HTML）。**按输入类型自动路由**：图片→RapidOCR（纯文字，轻量≈15MB），PDF/Office→RapidDoc（版面+表格+阅读顺序）。中文优先、离线、无 API Key。

> 通用 OCR 后端（不依赖 tesseract），适用于扫描 PDF 文字抢救、桌面自动化截图识字、图片转文字等场景。

## When to Use

统一入口 `parse()` 会按文件后缀自动选引擎：

| 输入类型 | 自动引擎 | 产出 |
|------|------|------|
| 图片/截图（png/jpg/bmp…） | RapidOCR | 纯文本 + bbox/置信度 |
| PDF（扫描版/电子版） | RapidDoc | Markdown + HTML 表格 |
| Office（docx/xlsx/pptx） | RapidDoc | Markdown（原生解析） |

- 用户给出**图片/截图/扫描件**，要提取其中的文字
- PDF 要**还原版面/表格结构**（不只是抠文字）
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
| `parse(path)` | **统一入口**：按后缀自动选 RapidOCR/RapidDoc |
| `parse(path, force='ocr')` | 强制走纯文字 OCR |
| `parse(path, force='doc')` | 强制走文档解析 RapidDoc |

OCR 返回：`{success, full_text, text_count, texts:[{text,confidence,bbox}], source:'rapidocr', elapse}`

Doc 返回：`{success, full_text, markdown, has_table, source:'rapiddoc'}`（表格已转 HTML）

## Dependencies

- `rapidocr_onnxruntime`（必需，OCR 文字识别；首次使用自动安装）
- `rapid-doc[cpu]`（可选，文档解析/PDF/Office 场景；`parse()` 遇文档懒加载，未装则提示 `pip install "rapid-doc[cpu]"`）
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
- **不要装 tesseract**：本技能已覆盖全部 OCR 需求。

---

## 如何验证它工作

```bash
python -E -c "from rapidocr import RapidOCR; print('import OK')"
```
准备一张含中文的图片，跑一次识别，确认能输出文字。
