#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
drawio_export.py — 将绘图元素清单 (JSON) 渲染为标准 draw.io (.drawio / mxGraph XML) 文件。

用途：让 tech-diagram 技能生成的图，同时输出一份可在 draw.io 中
      （在线 https://app.diagrams.net/ ，或本地 draw.io 桌面版）
      打开、拖拽编辑、协作的矢量文件，成为"活文件"而不仅是静态 PNG/SVG。

输入 JSON 结构（节点 / 连线 / 分组背景）:
{
  "meta": {"name": "Page-1", "dx": 1000, "dy": 700, "pageWidth": 1600, "pageHeight": 900},
  "nodes": [
      {
        "id": "n1",
        "value": "节点标签",
        "x": 60, "y": 86, "w": 150, "h": 70,
        "style": {
            "rounded": 1, "whiteSpace": "wrap", "html": 1,
            "fillColor": "#ebf5ff", "strokeColor": "#3498db",
            "fontColor": "#16324f", "fontStyle": 1,      # 1=bold
            "verticalAlign": "middle", "align": "center",
            "dashed": 0
        },
        "group": {"label": "L5 · 决策分析层", ...}   # 可选：若给了 group，该节点归入该分组
      }
  ],
  "groups": [   # 背景容器（浅色底 + 虚线边框 + 左上角层名）
      {"id": "g1", "label": "L5 · 决策分析层",
       "x": 30, "y": 52, "w": 900, "h": 120,
       "style": {"fillColor": "#ebf5ff", "strokeColor": "#3498db", "dashed": 1}}
  ],
  "edges": [   # 连线（箭头）
      {"id": "e1", "source": "n1", "target": "n2",
       "style": {"edgeStyle": "orthogonalEdgeStyle", "rounded": 0,
                 "strokeColor": "#7a7a7a", "strokeWidth": 2,
                 "endArrow": "block", "endFill": 1}}
  ]
}

用法:
    python -E drawio_export.py input.json -o output.drawio
输出: output.drawio（标准 draw.io 可导入/打开文件）
"""
import sys, io, json, argparse, xml.sax.saxutils as sax, uuid

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


# ---------- mxGraph style 渲染 ----------
def _style_str(s):
    """把 style dict 转成 draw.io 的 style 字符串。"""
    order = [
        "rounded", "whiteSpace", "html", "verticalAlign", "align",
        "fillColor", "strokeColor", "strokeWidth", "fontColor",
        "fontSize", "fontStyle", "dashed", "dashPattern", "edgeStyle",
        "endArrow", "endFill", "startArrow", "startFill", "gradientColor",
    ]
    parts = []
    for k in order:
        if k in s and s[k] not in (None, ""):
            parts.append(f"{k}={s[k]}")
    # 其余自定义键
    for k, v in s.items():
        if k not in order and v not in (None, ""):
            parts.append(f"{k}={v}")
    return ";" .join(parts)


def _esc(v):
    if v is None:
        return ""
    # 必须同时转义双引号：value 属性用双引号包裹，
    # 若 value 内含 HTML 属性（如 <b style="font-size:15px">），
    # 未转义的 " 会直接截断 XML 属性 → not well-formed。
    return sax.escape(str(v), {'"': "&quot;", "'": "&apos;"})


def build_mxgraph(data):
    """返回 mxGraphModel 内部 XML 字符串。"""
    meta = data.get("meta", {})
    groups = data.get("groups", [])
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    cell_id = meta.get("seed", 0) * 100000 if meta.get("seed") else 1

    lines = []
    lines.append('      <root>')
    lines.append('        <mxCell id="0"/>')
    lines.append('        <mxCell id="1" parent="0"/>')

    # 统计每个节点属于哪个 group（用 group 的 id 或 label）
    node_group = {}
    for n in nodes:
        g = n.get("group")
        node_group[n["id"]] = g.get("id") if g else None

    # 渲染 groups（背景容器，可折叠分组）
    gid_map = {}
    for g in groups:
        gid = g.get("id", f"g{cell_id}"); cell_id += 1
        gid_map[g["label"]] = gid
        sty = _style_str(dict(g.get("style", {}), verticalAlign="top",
                             whiteSpace="wrap", html=1,
                             dashed=g.get("style", {}).get("dashed", 1)))
        lines.append(
            f'        <mxCell id="{_esc(gid)}" value="{_esc(g["label"])}" '
            f'style="{_esc(sty)}" vertex="1" parent="1">'
            f'<mxGeometry x="{g["x"]}" y="{g["y"]}" width="{g["w"]}" '
            f'height="{g["h"]}" as="geometry"/></mxCell>'
        )

    # 渲染节点（若所属 group 被渲染，则 parent 指向该 group，坐标用相对坐标）
    for n in nodes:
        gid = node_group.get(n["id"])
        parent = gid if gid else "1"
        # 若属于分组，需把绝对坐标换算成相对该分组左上角的坐标
        rel_x, rel_y = n["x"], n["y"]
        if gid:
            for g in groups:
                if g.get("id") == gid:
                    rel_x = n["x"] - g["x"]
                    rel_y = n["y"] - g["y"]
                    break
        sty = _style_str(dict(n.get("style", {}), whiteSpace="wrap", html=1))
        lines.append(
            f'        <mxCell id="{_esc(n["id"])}" value="{_esc(n.get("value"))}" '
            f'style="{_esc(sty)}" vertex="1" parent="{_esc(parent)}">'
            f'<mxGeometry x="{rel_x}" y="{rel_y}" width="{n["w"]}" '
            f'height="{n["h"]}" as="geometry"/></mxCell>'
        )

    # 渲染连线
    for e in edges:
        sty = _style_str(dict(e.get("style", {}), html=1,
                             endArrow="block", endFill=1))
        lines.append(
            f'        <mxCell id="{_esc(e["id"])}" style="{_esc(sty)}" '
            f'edge="1" parent="1" source="{_esc(e["source"])}" '
            f'target="{_esc(e["target"])}">'
            f'<mxGeometry relative="1" as="geometry"/></mxCell>'
        )

    lines.append('      </root>')
    return "\n".join(lines)


def build_drawio(data):
    meta = data.get("meta", {})
    diag_id = meta.get("diagram_id") or str(uuid.uuid4())
    name = _esc(meta.get("name", "Page-1"))
    dx = meta.get("dx", 1100)
    dy = meta.get("dy", 800)
    pw = meta.get("pageWidth", 1600)
    ph = meta.get("pageHeight", 900)

    inner = build_mxgraph(data)
    return (
        '<mxfile host="app.diagrams.net" modified="'
        + str(uuid.uuid4()) + '" agent="tech-diagram" version="24.0.0">\n'
        f'  <diagram id="{diag_id}" name="{name}">\n'
        f'    <mxGraphModel dx="{dx}" dy="{dy}" grid="1" gridSize="10" '
        f'guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" '
        f'pageScale="1" pageWidth="{pw}" pageHeight="{ph}" math="0" '
        f'shadow="0">\n'
        f'{inner}\n'
        '    </mxGraphModel>\n'
        '  </diagram>\n'
        '</mxfile>\n'
    )


def main():
    ap = argparse.ArgumentParser(description="渲染 draw.io (.drawio) 文件")
    ap.add_argument("input", help="绘图元素清单 JSON 文件路径")
    ap.add_argument("-o", "--output", default="output.drawio",
                    help="输出 .drawio 文件路径")
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    out = build_drawio(data)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"[OK] 已写入 {args.output}  ({len(out)} bytes)")


if __name__ == "__main__":
    main()
