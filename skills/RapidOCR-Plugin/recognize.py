# -*- coding: utf-8 -*-
"""
RapidOCR Plugin — 命令行图片文字识别工具
========================================
基于 RapidOCR (ONNX Runtime) 的本地 OCR，中文优先、离线、无 API Key。

用法:
    python recognize.py <图片路径>                 # 打印识别文本
    python recognize.py <图片路径> -o out.txt      # 写到文件
    python recognize.py --screenshot              # 截全屏识别
    python recognize.py --list-models             # 查看引擎信息
"""

import argparse
import io
import sys


def _utf8():
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def _ensure_skill_importable() -> bool:
    """把本插件目录加入 sys.path，以便 import RapidOCR。"""
    from pathlib import Path
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    # 若同目录无 RapidOCR 包，尝试从相邻安装点导入
    return (here / "RapidOCR").exists() or (here / "__init__.py").exists()


def main(argv=None):
    _utf8()
    parser = argparse.ArgumentParser(description="RapidOCR 图片文字识别")
    parser.add_argument("image", nargs="?", help="图片文件路径")
    parser.add_argument("-o", "--output", help="输出到文件 (默认打印到 stdout)")
    parser.add_argument("--screenshot", action="store_true", help="截全屏识别")
    parser.add_argument("--list-models", action="store_true", help="显示引擎信息")
    args = parser.parse_args(argv)

    if args.list_models:
        try:
            from rapidocr_onnxruntime import RapidOCR as R
        except ImportError:
            print("rapidocr_onnxruntime 未安装，首次使用将自动安装…")
            return 1
        print(f"Engine: RapidOCR (ONNX Runtime)")
        print(f"Det: {getattr(R, 'DEFAULT_MODEL_DIR', 'default det/det.onnx')}")
        print(f"Rec: {getattr(R, 'DEFAULT_REC_MODEL', 'default rec/rec.onnx')}")
        return 0

    if not args.image and not args.screenshot:
        parser.error("必须提供图片路径，或使用 --screenshot")

    # 导入技能包（本目录结构下即 RapidOCR 模块）
    _ensure_skill_importable()
    try:
        from RapidOCR import recognize, screenshot
    except ImportError as e:
        print(f"[ERROR] 无法加载 RapidOCR: {e}")
        print("提示：请确认本插件目录含 RapidOCR 模块（__init__.py）。")
        return 1

    try:
        result = screenshot() if args.screenshot else recognize(args.image)
    except Exception as e:
        print(f"[ERROR] 识别过程异常: {e}")
        return 1

    if not result.get("success"):
        print(f"[ERROR] {result.get('error', '未知错误')}")
        return 1

    text = result.get("full_text", "")
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[OK] 已写入 {args.output}（{result.get('text_count', 0)} 块）")
    else:
        print(text if text else "(未识别到文字)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
