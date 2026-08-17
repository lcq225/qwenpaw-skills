"""
RapidOCR Skill - 基于 RapidOCR 的智能 OCR 识别工具

核心特性：
- 基于 ONNX Runtime，速度快 3-5 倍
- 轻量级，仅 14.9MB
- 支持文件路径、Base64、截图识别
- 智能路由，自动识别输入类型
"""

import base64
import io
import sys
from pathlib import Path
from typing import Union, Dict, Any, Optional

# 尝试导入 RapidOCR
try:
    from rapidocr_onnxruntime import RapidOCR
    RAPIDOCR_AVAILABLE = True
except ImportError:
    RAPIDOCR_AVAILABLE = False
    # 自动安装
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "rapidocr_onnxruntime", "-q"])
    from rapidocr_onnxruntime import RapidOCR
    RAPIDOCR_AVAILABLE = True

# 尝试导入截图功能
try:
    from PIL import ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def _visual_order(texts):
    """按 bbox 视觉坐标重排：行内从左到右、行间从上到下。

    用 y 中心分组成"行"，行之间按 y 排序、行内按 x 排序，
    使`full_text`贴近人类阅读顺序（界面/文档视觉布局）。
    """
    if not texts:
        return texts
    # y 中心排序，然后用行高差做聚合
    items = sorted(texts, key=lambda t: (t["y"], t["x"]))
    rows = []
    current_row = [items[0]]
    for it in items[1:]:
        # 与当前行首块的 y 中心差在 12px 内 → 视为同一行
        if abs(it["y"] - current_row[0]["y"]) <= 12:
            current_row.append(it)
        else:
            rows.append(current_row)
            current_row = [it]
    rows.append(current_row)

    ordered = []
    for row in rows:
        row = sorted(row, key=lambda t: t["x"])  # 行内从左到右
        ordered.extend(row)
    return ordered


class RapidOCRSkill:
    """
    RapidOCR Skill 类
    """

    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu
        self._ocr = None
        self._initialized = False

    def initialize(self) -> None:
        """延迟初始化"""
        if self._initialized:
            return

        try:
            self._ocr = RapidOCR()
            self._initialized = True
        except Exception as e:
            raise RuntimeError(f"OCR初始化失败: {e}")

    def recognize(self, image_path: Union[str, Path]) -> Dict[str, Any]:
        """
        识别图片文件

        Args:
            image_path: 图片文件路径

        Returns:
            识别结果字典
        """
        image_path = Path(image_path)
        if not image_path.exists():
            return {"success": False, "error": f"文件不存在: {image_path}"}

        try:
            self.initialize()
            result = self._ocr(str(image_path))
            return self._format_result(result, "file")
        except Exception as e:
            return {"success": False, "error": f"识别失败: {e}"}

    def recognize_base64(self, base64_data: str) -> Dict[str, Any]:
        """从 Base64 识别"""
        try:
            self.initialize()
            image_data = base64.b64decode(base64_data)
            result = self._ocr(image_data)
            return self._format_result(result, "base64")
        except Exception as e:
            return {"success": False, "error": f"识别失败: {e}"}

    def recognize_screenshot(self) -> Dict[str, Any]:
        """截图识别"""
        if not PIL_AVAILABLE:
            return {"success": False, "error": "PIL不可用"}

        try:
            screenshot = ImageGrab.grab()
            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            self.initialize()
            result = self._ocr(img_byte_arr)
            return self._format_result(result, "screenshot")
        except Exception as e:
            return {"success": False, "error": f"截图失败: {e}"}

    def _format_result(self, result: tuple, source: str) -> Dict[str, Any]:
        """格式化结果（已按 bbox 视觉坐标重排：行内从左到右、行间从上到下）"""
        # RapidOCR 返回: (texts_list, elapse_list)
        if not result or len(result) == 0:
            return {
                "success": True,
                "text_count": 0,
                "full_text": "",
                "texts": [],
                "source": source
            }

        texts_list = result[0] if isinstance(result, tuple) else result
        elapse = result[1] if isinstance(result, tuple) and len(result) > 1 else []

        if not texts_list:
            return {
                "success": True,
                "text_count": 0,
                "full_text": "",
                "texts": [],
                "source": source
            }

        texts = []

        for item in texts_list:
            # 格式: [bbox, text, confidence]
            if len(item) >= 3:
                bbox, text, confidence = item[0], item[1], item[2]
                # bbox = [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                y_center = (bbox[0][1] + bbox[2][1]) / 2.0 if bbox else 0.0
                x_center = (bbox[0][0] + bbox[2][0]) / 2.0 if bbox else 0.0
                texts.append({
                    "text": text,
                    "confidence": float(confidence),
                    "bbox": bbox,
                    "x": x_center,
                    "y": y_center
                })

        # 按行分组的视觉排序：先按 y（行中心）聚合，行内按 x 从左到右
        texts = _visual_order(texts)

        full_text = "\n".join(t["text"] for t in texts)

        return {
            "success": True,
            "text_count": len(texts),
            "full_text": full_text,
            "texts": texts,
            "source": source,
            "elapse": elapse
        }


# ============================================================
# 便捷函数（推荐使用）
# ============================================================

def recognize(image_path: str) -> Dict[str, Any]:
    """
    识别图片文件（便捷函数）

    Args:
        image_path: 图片文件路径

    Returns:
        识别结果字典

    示例:
        from RapidOCR import recognize
        result = recognize("image.png")
        print(result['full_text'])
    """
    skill = RapidOCRSkill()
    return skill.recognize(image_path)


def extract_text(image_path: str) -> str:
    """
    提取纯文本（便捷函数）

    Args:
        image_path: 图片文件路径

    Returns:
        纯文本字符串

    示例:
        from RapidOCR import extract_text
        text = extract_text("image.png")
        print(text)
    """
    result = recognize(image_path)
    return result.get('full_text', '') if result.get('success') else ''


def screenshot() -> Dict[str, Any]:
    """
    截图识别（便捷函数）

    Returns:
        识别结果字典

    示例:
        from RapidOCR import screenshot
        result = screenshot()
        print(result['full_text'])
    """
    skill = RapidOCRSkill()
    return skill.recognize_screenshot()


# 导出
__all__ = ['RapidOCRSkill', 'recognize', 'extract_text', 'screenshot']