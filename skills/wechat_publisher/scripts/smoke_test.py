"""WeChat Publisher 技能冒烟验证"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    import publisher
    html = publisher.markdown_to_wechat_html("> [!point] 冒烟", theme="default")
    assert "background:#fff7e6" in html, "渲染器未输出 point 卡片样式"
    print("OK: wechat_publisher.publisher importable + renderer works")
    print("SMOKE_PASS: wechat_publisher v1.0.0")
except Exception as e:
    print(f"SMOKE_FAIL: {type(e).__name__}: {e}")