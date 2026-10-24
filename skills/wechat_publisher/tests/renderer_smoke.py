# -*- coding: utf-8 -*-
"""wechat_publisher 渲染器回归自检：卡片分支 + 引用分支互不干扰。

用法（在技能目录内或任意位置）：
    python -E tests/renderer_smoke.py
判据：13 项全部 PASS。
"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# 路径自适应：tests/ 的上一级即技能根目录
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SKILL_ROOT)
import publisher

CASES = [
    # (说明, markdown, 必须出现的片段, 必须不出现的片段)
    ("lead 卡片",       "> [!lead] 引言",      "background:#f0f6f8", "1px dashed"),
    ("point 卡片",      "> [!point] 要点",     "background:#fff7e6", "1px dashed"),
    ("warn 卡片",       "> [!warn] 风险",      "background:#fff3e0", "1px dashed"),
    ("note 卡片",       "> [!note] 信息",      "background:#eef4fb", "1px dashed"),
    ("tip 卡片",        "> [!tip] 建议",       "background:#e8f5e9", "1px dashed"),
    ("ok 卡片",         "> [!ok] 能做到",      "border-left:4px solid #2e7d32", "1px dashed"),
    ("no 卡片",         "> [!no] 做不到",      "border-left:4px solid #c62828", "1px dashed"),
    ("普通引用金句",     "> 一句话金句",        "1px dashed", "background:#fff7e6"),
    ("宽松写法回退",     "[!point] 裸写法",     "background:#fff7e6", "1px dashed"),
]

fails = []
for name, md, need, forbid in CASES:
    html = publisher.markdown_to_wechat_html(md, theme="hot_media")
    ok_need = need in html
    ok_forbid = forbid not in html
    status = "PASS" if (ok_need and ok_forbid) else "FAIL"
    if status == "FAIL":
        fails.append(name)
    print(f"{status}  {name:14s} need={ok_need} forbid_ok={ok_forbid}")

# 混合场景：卡片 + 引用同文，各归各位
mixed = "> [!lead] 引言块\n\n正文\n\n> 普通引用\n\n> [!warn] 风险块"
h = publisher.markdown_to_wechat_html(mixed, theme="hot_media")
checks = {
    "lead": "background:#f0f6f8" in h,
    "warn": "background:#fff3e0" in h,
    "quote": h.count("1px dashed") == 1,
    "card_count": h.count("border-radius:0 6px 6px 0") >= 2,
}
for k, v in checks.items():
    print(("PASS  " if v else "FAIL  ") + "mixed/" + k)
    if not v:
        fails.append("mixed/" + k)

print("\nRESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL -> {fails}")
