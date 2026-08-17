# RapidOCR 插件包

> **中文图片文字识别** · 基于 RapidOCR (ONNX Runtime) · 离线可用 · 无 API Key

一个开箱即用的 OCR 插件：识别图片/截图/扫描件中的文字，输出纯文本。
中文优先，轻量（≈15MB），比传统引擎快 3–5 倍，首次使用自动安装依赖。

---

## 目录结构

```
RapidOCR-Plugin/
├── SKILL.md       # 技能定义（QwenPaw Skill 标准，frontmatter: name+description）
├── recognize.py   # 命令行 OCR 工具（可直接 `python recognize.py 图片.png`）
├── requirements.txt
├── README.md
└── RapidOCR/      # Python 包（核心模块）
    └── __init__.py  # API：recognize() / extract_text() / screenshot()
```

## 快速开始

### 方式一：命令行

```bash
python recognize.py 照片.png              # 打印识别文本
python recognize.py 照片.png -o out.txt   # 输出到文件
python recognize.py --screenshot          # 截全屏识别
```

### 方式二：Python API

```python
import sys; sys.path.insert(0, "RapidOCR-Plugin")
from RapidOCR import recognize, extract_text

r = recognize("照片.png")
print(r["full_text"])      # 全部文字
text = extract_text("照片.png")  # 纯文本
```

### 方式三：作为 QwenPaw Skill

把 `RapidOCR` 目录（或本包内 `__init__.py` 同级）放进 workspace 的 `skills/` 或全局 `skill_pool/`，
并在 `skill_pool/skill.json` 的 `skills` 字典登记同名入口。

## 返回结构（API）

```python
{
    "success": True,       # 是否成功
    "full_text": "文字",   # 全部文字（换行分隔）
    "text_count": 5,
    "texts": [{"text","confidence","bbox"}],
    "source": "file|base64|screenshot",
    "elapse": [...]
}
```

## 依赖

| 包 | 用途 | 首次自动安装 |
|----|------|:----:|
| `rapidocr_onnxruntime` | OCR 引擎（ONNX Runtime）| ✅ |
| `Pillow` | 截图识别（可选）| 需要时 |

安装方式：
```bash
pip install -r requirements.txt
```

## 常见问题

| 问题 | 解决 |
|------|------|
| 首次运行慢 | 首次自动下载 ONNX 模型，稍等；之后秒级 |
| 中文路径乱码 | `__init__.py` / `recognize.py` 已将 `stdout` 强制 UTF-8 |
| 截图功能报错 | 需 `Pillow`（`pip install Pillow`）|

---

**版本**: 1.0.1
**协议**: 随 QwenPaw 技能生态（Apache-2.0）
