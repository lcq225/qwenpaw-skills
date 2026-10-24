---
name: tech-diagram
description: "Use when the user wants to create any technical diagram — architecture, data flow, flowchart, sequence, agent/memory, or concept map — and export as SVG+PNG plus an editable draw.io file. Trigger on: 画图、帮我画、生成图、做个图、架构图、流程图、可视化一下、出图、generate diagram、draw diagram、visualize or any system/flow description the user wants illustrated."
version: 1.0.0
license: MIT
metadata:
  emoji: "🎨"
  requires:
    rsvg-convert: ">=2.40.20"
---
# Tech Diagram - 技术架构图生成技能

Generate production-quality SVG technical diagrams exported as PNG via `rsvg-convert`.

## Workflow (Always Follow This Order)

1. **Classify** the diagram type (see Diagram Types below)
2. **Extract structure** — identify layers, nodes, edges, flows, and semantic groups from user description
3. **Plan layout** — apply the layout rules for the diagram type
4. **Load style reference** — default is Flat Icon style; see Style Options below
5. **Map nodes to shapes** — use Shape Vocabulary below
6. **Write SVG** to output path (default: current working directory)
7. **Export PNG**: `rsvg-convert -w 1920 file.svg -o file.png`
8. **Export draw.io (可选但推荐)**: 用同一份图结构数据写 `file.drawio`，让非技术同事可在内网 draw.io 打开拖拽编辑（见下方「draw.io 可编辑导出」）
9. **Report** all file paths

## Diagram Types & Layout Rules

### 1. Architecture Diagram
Nodes = services/components. Group into **horizontal layers** (top→bottom or left→right).
- Typical layers: Client → Gateway/LB → Services → Data/Storage
- Use `<g>` dashed containers to group related services in the same layer
- Arrow direction follows data/request flow
- ViewBox: `0 0 960 600` standard, `0 0 960 800` for tall stacks

### 2. Data Flow Diagram
Emphasizes **what data moves where**. Focus on data transformation.
- Label every arrow with the data type (e.g., "embeddings", "query", "context")
- Use wider arrows (`stroke-width: 2.5`) for primary data paths
- Dashed arrows for control/trigger flows
- Color arrows by data category

### 3. Flowchart / Process Flow
Sequential decision/process steps.
- Top-to-bottom preferred; left-to-right for wide flows
- Diamond shapes for decisions, rounded rects for processes, parallelograms for I/O
- Keep node labels short (≤3 words); put detail in sub-labels
- Align nodes on a grid: x positions snap to 120px intervals, y to 80px

### 4. Sequence Diagram
Vertical timeline with horizontal arrows.
- Actors on top (left/right), messages flowing down
- Self-calls loop back to the same actor
- Dashed lines for async/returns
- Number messages in order

### 5. Agent Architecture Diagram
Shows how an AI agent reasons, uses tools, and manages memory.
Key conceptual layers:
- **Input layer**: User, query, trigger
- **Agent core**: LLM, reasoning loop, planner
- **Memory layer**: Short-term (context window), Long-term (vector/graph DB), Episodic
- **Tool layer**: Tool calls, APIs, search, code execution
- **Output layer**: Response, action

### 6. Memory Architecture Diagram
Shows memory systems and their relationships.
Key components:
- **Short-term memory**: Context window, conversation history
- **Long-term memory**: Vector DB, Knowledge Graph, Facts/Experiences
- **Memory operations**: Store, Retrieve, Forget, Consolidate
- **Memory triggers**: Context relevance, importance threshold

## Shape Vocabulary

| Shape | SVG Element | Use Case |
|-------|-------------|----------|
| Service/Component | `<rect rx="8">` rounded rectangle | Services, databases, APIs |
| Decision | `<polygon points="...">` diamond | If/else, branching |
| Process | `<rect rx="4">` small rounded rect | Steps, actions |
| I/O | `<polygon points="...">` parallelogram | Input/output |
| Actor | `<circle>` or `<ellipse>` | Users, external systems |
| Database | `<path>` cylinder shape | Data storage |
| Cloud | `<path>` cloud shape | External services, SaaS |
| Group/Container | `<rect rx="12" stroke-dasharray="4">` dashed border | Layer grouping |

## Arrow Semantics

| Arrow Type | SVG Style | Meaning |
|------------|-----------|---------|
| Solid arrow | `marker-end="url(#arrow)"` | Data/request flow |
| Dashed arrow | `stroke-dasharray="6"` | Control/trigger |
| Bidirectional | Two arrow markers | Sync/bidirectional |
| Wide arrow | `stroke-width="2.5"` | Primary data path |

## Style Options (7 Preset Styles)

### Style 1: Flat Icon (Default)
- Clean, modern, flat design
- Colors: Blue (#3498db), Green (#2ecc71), Orange (#e67e22), Red (#e74c3c)
- No gradients, solid fills
- Suitable for: Architecture diagrams, flowcharts

### Style 2: Dark Terminal
- Dark background (#1a1a2e), neon accents
- Colors: Cyan (#00d4ff), Magenta (#ff00ff), Green (#00ff88)
- Monospace fonts
- Suitable for: Data flow diagrams, sequence diagrams

### Style 3: Blueprint
- Blue background (#0a192f), white lines
- Grid pattern background
- Technical, engineering feel
- Suitable for: Architecture diagrams, system design

### Style 4: Notion Clean
- Minimal, black/white/gray
- Colors: Black (#000), Gray (#666), Light Gray (#f7f7f7)
- Sans-serif fonts
- Suitable for: Flowcharts, process diagrams

### Style 5: Gradient Modern
- Gradient fills, 3D shadows
- Colors: Gradient from primary to secondary
- Rounded corners, drop shadows
- Suitable for: Presentation slides, marketing materials

### Style 6: Hand-Drawn
- Sketch-like, imperfect lines
- Colors: Pencil gray (#555), highlight yellow (#ffeb3b)
- Wavy lines, rough shapes
- Suitable for: Brainstorming, early design stages

### Style 7: Tech Neon
- Glowing effects, cyberpunk style
- Colors: Electric blue (#00f0ff), Neon purple (#bf00ff)
- Glow filters, animated elements
- Suitable for: Tech presentations, AI/ML diagrams

## Color Tokens by Category

| Category | Default Color | Dark Terminal | Blueprint |
|----------|---------------|---------------|-----------|
| User/Client | #3498db | #00d4ff | #fff |
| Service/API | #2ecc71 | #00ff88 | #0a84ff |
| Database | #e67e22 | #ff6b35 | #ff9500 |
| Cache/Queue | #9b59b6 | #bf00ff | #af52de |
| External/Cloud | #95a5a6 | #666 | #666 |
| Error/Alert | #e74c3c | #ff3b30 | #ff3b30 |

## SVG Technical Rules

1. **ViewBox**: Standard `0 0 960 600` or custom based on complexity
2. **Font**: Inter, system-ui, or specified style font
3. **Text**: `<text>` with proper positioning, avoid overlapping
4. **Groups**: Use `<g>` to organize related elements
5. **Defs**: Define reusable markers, gradients, filters in `<defs>`
6. **Stroke**: Consistent stroke widths (1.5 for lines, 2 for emphasis)
7. **Fill**: Solid colors or gradients as per style
8. **Transform**: Use `transform="translate(x,y)"` for positioning

## Example Usage

### Generate Architecture Diagram

```
用户描述：画一个RAG系统架构图，包含用户、LLM、向量数据库、知识库

LLM生成SVG：
- 分类：Architecture Diagram
- 结构：User → LLM → VectorDB → KnowledgeBase
- 布局：4层架构，ViewBox 0 0 960 600
- 风格：Flat Icon（默认）
- 写SVG文件：rag_architecture.svg
- 转PNG：rsvg-convert -w 1920 rag_architecture.svg -o rag_architecture.png
- 返回路径：rag_architecture.svg, rag_architecture.png
```

### Generate Flowchart

```
用户描述：画一个API请求流程图，包含请求→验证→处理→响应

LLM生成SVG：
- 分类：Flowchart
- 结构：Request → Validate → Process → Response
- 布局：垂直流程，网格对齐
- 风格：Notion Clean
- 写SVG文件：api_flow.svg
- 转PNG：rsvg-convert -w 1920 api_flow.svg -o api_flow.png
- 返回路径
```

## Output

- **SVG文件**：矢量图，可编辑，可缩放
- **PNG文件**：1920px宽度，适合嵌入文档/PPT
- **drawio文件（可选）**：企业内网 draw.io 可打开、拖拽编辑、协作的可编辑"活文件"
- **路径报告**：返回所有产物的完整路径

## draw.io 可编辑导出（推荐）

让 AI 生成的图不只是静态 PNG/SVG，同时输出一份 **可导入 draw.io 的 `.drawio`（mxGraph XML）文件**，
非技术同事可在 <https://app.diagrams.net/>（在线版）或 draw.io 桌面版里继续拖拽调排版、加字、改连线、协作。

**为什么做这个**：SVG 一旦生成就锁死为静态图，改动要重新生成；而 `.drawio` 里的每个形状都是独立
可编辑的 `mxCell`，是"活文件"，也是唯一让不懂代码的同事能上手改 AI 出图的方式。

### 工具脚本

`skills/tech-diagram/drawio_export.py` —— 把绘图元素清单（JSON）渲染成标准 `.drawio`：

```bash
python -E drawio_export.py diagram.json -o diagram.drawio
```

**JSON 结构**（nodes / groups / edges）：
```json
{
  "meta": {"name": "页面名", "dx": 1100, "dy": 850, "pageWidth": 1800, "pageHeight": 1000},
  "groups": [{"id": "gl5", "label": "L5 · 决策分析层", "x": 30, "y": 52, "w": 900, "h": 120,
               "style": {"fillColor": "#ebf5ff", "strokeColor": "#3498db", "dashed": 1}}],
  "nodes": [{"id": "n5a", "value": "<b>数据中台</b><br>子行1<br>子行2",
              "x": 60, "y": 86, "w": 150, "h": 70, "group": {"id": "gl5"},
              "style": {"fillColor": "#ffffff", "strokeColor": "#3498db", "fontSize": 10, "rounded": 1}}],
  "edges": [{"id": "e1", "source": "n5c", "target": "n4a",
              "style": {"edgeStyle": "orthogonalEdgeStyle", "strokeColor": "#7a7a7a",
                        "strokeWidth": 2, "endArrow": "block", "endFill": 1}}]
}
```

**要点**：
- **坐标用绝对坐标**（与 SVG 相同坐标系），脚本会自动换算成相对所属 group 的坐标
- **node 的 `group`** 指定所属层（背景分组），draw.io 里该层可整体折叠/复制
- **value 支持 HTML 折行**：`<b>标题</b><br>子行`（多行标签）
- **style 键**：`fillColor/strokeColor/fontColor/fontSize/rounded/dashed/fontStyle(1=加粗)` 等，映射为 mxGraph style 字符串
- **edges** 用 `source/target` 引用 node id，自动生成正交箭头连线；`endArrow=block;endFill=1` 为实心箭头

**推荐流程**：设计好 SVG 布局后，把同一套节点几何与配色填进 JSON → 一次生成 SVG + drawio 两份产物，
保证视觉一致且同事可编辑。

## Dependencies

- **rsvg-convert**: librsvg工具，用于SVG转PNG
- 安装：`choco install rsvg-convert`（Windows）
- 验证：`rsvg-convert --version`
- **Python 3**: 运行 `drawio_export.py`（用 `python -E` 规避 PYTHONHOME 污染）

## Notes

- SVG文件可直接编辑（文本编辑器或矢量图编辑器）
- PNG文件适合嵌入Word/PPT/网页
- drawio文件可导入 draw.io（<https://app.diagrams.net/> 在线版或桌面版）继续编辑协作

### 输出位置（默认写到用户下载目录）

默认输出目录 = **当前用户的下载目录**，跨平台自动推导：

| 平台 | 默认目录 |
|:--|:--|
| Windows | `%USERPROFILE%\Downloads` |
| macOS / Linux | `~/Downloads` |

Python 取法（不写死盘符）：

```python
from pathlib import Path
out_dir = Path.home() / "Downloads"
out_dir.mkdir(parents=True, exist_ok=True)
```

- 也可用 `--out-dir` 显式指定，或用环境变量 `TECH_DIAGRAM_OUT_DIR` 覆盖
- 交付多个文件时建议在其下再建一层项目子目录，避免下载目录堆积
- 临时中间产物放系统临时目录（`tempfile.gettempdir()`），任务结束即清理
- ❌ 不要把产出图写进技能目录（会随技能一起分发，污染包体）

## Version

- **Version**: 1.0.0
- **License**: MIT（基于 fireworks-tech-graph 二次开发）
- **Source**: https://github.com/yizhiyanhua-ai/fireworks-tech-graph