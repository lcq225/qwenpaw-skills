# -*- coding: utf-8 -*-
"""
tech-diagram - 技术架构图生成技能
Generate SVG technical diagrams and export to PNG
"""
import subprocess
import os
import sys
from pathlib import Path

def generate_diagram(
    diagram_type: str,
    structure: dict,
    style: str = "flat-icon",
    output_path: str = None,
    width: int = 1920
) -> dict:
    """
    Generate a technical diagram
    
    Args:
        diagram_type: Type of diagram (architecture, dataflow, flowchart, sequence, agent, memory)
        structure: Diagram structure (layers, nodes, edges)
        style: Style preset (flat-icon, dark-terminal, blueprint, notion-clean, gradient, hand-drawn, tech-neon)
        output_path: Output file path (default: current directory)
        width: PNG width in pixels (default: 1920)
    
    Returns:
        dict with svg_path, png_path, and status
    """
    # Default output path
    if output_path is None:
        output_path = os.getcwd()
    
    # Generate SVG content based on structure
    svg_content = _generate_svg(diagram_type, structure, style)
    
    # Write SVG file
    filename = structure.get("name", "diagram")
    svg_path = Path(output_path) / f"{filename}.svg"
    png_path = Path(output_path) / f"{filename}.png"
    
    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    # Convert to PNG
    result = subprocess.run(
        ['rsvg-convert', '-w', str(width), str(svg_path), '-o', str(png_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return {
            "success": False,
            "error": result.stderr,
            "svg_path": str(svg_path)
        }
    
    return {
        "success": True,
        "svg_path": str(svg_path),
        "png_path": str(png_path),
        "diagram_type": diagram_type,
        "style": style
    }

def _generate_svg(diagram_type: str, structure: dict, style: str) -> str:
    """Generate SVG content based on diagram type and structure"""
    
    # Color schemes by style
    colors = _get_colors(style)
    
    # Base SVG template
    svg_template = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {viewbox}" width="{width}" height="{height}">
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="{arrow_color}"/>
    </marker>
  </defs>
  {content}
</svg>"""
    
    # Generate content based on type
    if diagram_type == "architecture":
        content = _generate_architecture(structure, colors)
        viewbox = "960 600"
    elif diagram_type == "flowchart":
        content = _generate_flowchart(structure, colors)
        viewbox = "960 800"
    elif diagram_type == "agent":
        content = _generate_agent(structure, colors)
        viewbox = "960 700"
    elif diagram_type == "memory":
        content = _generate_memory(structure, colors)
        viewbox = "960 600"
    else:
        content = _generate_generic(structure, colors)
        viewbox = "960 600"
    
    return svg_template.format(
        viewbox=viewbox,
        width=960,
        height=int(viewbox.split()[1]),
        arrow_color=colors.get("arrow", "#3498db"),
        content=content
    )

def _get_colors(style: str) -> dict:
    """Get color scheme by style"""
    styles = {
        "flat-icon": {
            "primary": "#3498db",
            "secondary": "#2ecc71",
            "tertiary": "#e67e22",
            "danger": "#e74c3c",
            "neutral": "#95a5a6",
            "arrow": "#3498db",
            "text": "#2c3e50",
            "bg": "#ffffff"
        },
        "dark-terminal": {
            "primary": "#00d4ff",
            "secondary": "#00ff88",
            "tertiary": "#ff6b35",
            "danger": "#ff3b30",
            "neutral": "#666666",
            "arrow": "#00d4ff",
            "text": "#ffffff",
            "bg": "#1a1a2e"
        },
        "blueprint": {
            "primary": "#0a84ff",
            "secondary": "#34c759",
            "tertiary": "#ff9500",
            "danger": "#ff3b30",
            "neutral": "#8e8e93",
            "arrow": "#ffffff",
            "text": "#ffffff",
            "bg": "#0a192f"
        },
        "notion-clean": {
            "primary": "#000000",
            "secondary": "#2eaadc",
            "tertiary": "#e67e22",
            "danger": "#e74c3c",
            "neutral": "#666666",
            "arrow": "#000000",
            "text": "#000000",
            "bg": "#f7f7f7"
        }
    }
    return styles.get(style, styles["flat-icon"])

def _generate_architecture(structure: dict, colors: dict) -> str:
    """Generate architecture diagram content"""
    layers = structure.get("layers", [])
    nodes = structure.get("nodes", [])
    
    content_parts = []
    
    # Background
    content_parts.append(f'<rect width="960" height="600" fill="{colors["bg"]}"/>')
    
    # Generate layers
    y_offset = 50
    layer_height = 120
    
    for i, layer in enumerate(layers):
        layer_name = layer.get("name", f"Layer {i+1}")
        layer_items = layer.get("items", [])
        
        # Layer container
        content_parts.append(f'''
        <g transform="translate(80, {y_offset})">
          <rect x="0" y="0" width="800" height="{layer_height}" 
                fill="none" stroke="{colors["neutral"]}" stroke-dasharray="4" rx="8"/>
          <text x="10" y="20" font-family="Inter, system-ui" font-size="14" 
                fill="{colors["neutral"]}">{layer_name}</text>
        </g>''')
        
        # Items in layer
        x_offset = 120
        for j, item in enumerate(layer_items):
            item_name = item.get("name", f"Item {j+1}")
            item_type = item.get("type", "service")
            color = colors.get(item_type, colors["primary"])
            
            content_parts.append(f'''
            <g transform="translate({x_offset}, {y_offset + 40})">
              <rect x="0" y="0" width="120" height="60" fill="{color}" rx="8"/>
              <text x="60" y="35" font-family="Inter, system-ui" font-size="12" 
                    fill="white" text-anchor="middle">{item_name}</text>
            </g>''')
            x_offset += 160
        
        y_offset += layer_height + 20
    
    return "\n".join(content_parts)

def _generate_flowchart(structure: dict, colors: dict) -> str:
    """Generate flowchart content"""
    steps = structure.get("steps", [])
    
    content_parts = []
    
    # Background
    content_parts.append(f'<rect width="960" height="800" fill="{colors["bg"]}"/>')
    
    # Generate steps
    y_offset = 80
    x_center = 480
    
    for i, step in enumerate(steps):
        step_name = step.get("name", f"Step {i+1}")
        step_type = step.get("type", "process")
        
        if step_type == "decision":
            # Diamond shape
            content_parts.append(f'''
            <g transform="translate({x_center - 60}, {y_offset})">
              <polygon points="60,0 120,40 60,80 0,40" fill="{colors["secondary"]}" 
                       stroke="{colors["text"]}" stroke-width="1.5"/>
              <text x="60" y="45" font-family="Inter, system-ui" font-size="12" 
                    fill="white" text-anchor="middle">{step_name}</text>
            </g>''')
        else:
            # Rounded rectangle
            content_parts.append(f'''
            <g transform="translate({x_center - 100}, {y_offset})">
              <rect x="0" y="0" width="200" height="50" fill="{colors["primary"]}" rx="8"
                    stroke="{colors["text"]}" stroke-width="1.5"/>
              <text x="100" y="30" font-family="Inter, system-ui" font-size="14" 
                    fill="white" text-anchor="middle">{step_name}</text>
            </g>''')
        
        # Arrow to next step
        if i < len(steps) - 1:
            content_parts.append(f'''
            <line x1="{x_center}" y1="{y_offset + 50}" x2="{x_center}" y2="{y_offset + 100}"
                  stroke="{colors["arrow"]}" stroke-width="2" marker-end="url(#arrow)"/>''')
        
        y_offset += 100
    
    return "\n".join(content_parts)

def _generate_agent(structure: dict, colors: dict) -> str:
    """Generate agent architecture diagram"""
    content_parts = []
    
    # Background
    content_parts.append(f'<rect width="960" height="700" fill="{colors["bg"]}"/>')
    
    # Standard agent layers
    layers = [
        {"name": "Input Layer", "items": [{"name": "User Query", "type": "primary"}]},
        {"name": "Agent Core", "items": [{"name": "LLM", "type": "primary"}, {"name": "Reasoning", "type": "secondary"}]},
        {"name": "Memory Layer", "items": [{"name": "Context", "type": "tertiary"}, {"name": "Vector DB", "type": "tertiary"}]},
        {"name": "Tool Layer", "items": [{"name": "APIs", "type": "secondary"}, {"name": "Search", "type": "secondary"}]},
        {"name": "Output Layer", "items": [{"name": "Response", "type": "primary"}]}
    ]
    
    # Override with custom structure if provided
    if structure.get("layers"):
        layers = structure["layers"]
    
    y_offset = 30
    layer_height = 100
    
    for i, layer in enumerate(layers):
        layer_name = layer.get("name", f"Layer {i+1}")
        items = layer.get("items", [])
        
        # Layer label
        content_parts.append(f'''
        <text x="50" y="{y_offset + 15}" font-family="Inter, system-ui" font-size="14" 
              fill="{colors["neutral"]}">{layer_name}</text>''')
        
        # Items
        x_offset = 180
        for j, item in enumerate(items):
            item_name = item.get("name", f"Item {j+1}")
            item_type = item.get("type", "primary")
            color = colors.get(item_type, colors["primary"])
            
            content_parts.append(f'''
            <g transform="translate({x_offset}, {y_offset})">
              <rect x="0" y="0" width="140" height="60" fill="{color}" rx="8"
                    stroke="{colors["text"]}" stroke-width="1"/>
              <text x="70" y="35" font-family="Inter, system-ui" font-size="12" 
                    fill="white" text-anchor="middle">{item_name}</text>
            </g>''')
            x_offset += 180
        
        # Arrow to next layer
        if i < len(layers) - 1:
            content_parts.append(f'''
            <line x1="480" y1="{y_offset + 60}" x2="480" y2="{y_offset + 100}"
                  stroke="{colors["arrow"]}" stroke-width="2" marker-end="url(#arrow)"/>''')
        
        y_offset += layer_height + 30
    
    return "\n".join(content_parts)

def _generate_memory(structure: dict, colors: dict) -> str:
    """Generate memory architecture diagram"""
    content_parts = []
    
    # Background
    content_parts.append(f'<rect width="960" height="600" fill="{colors["bg"]}"/>')
    
    # Memory components
    components = [
        {"name": "Short-term", "desc": "Context Window", "x": 100, "y": 150, "color": colors["primary"]},
        {"name": "Long-term", "desc": "Vector DB", "x": 400, "y": 150, "color": colors["secondary"]},
        {"name": "Episodic", "desc": "Experiences", "x": 700, "y": 150, "color": colors["tertiary"]}
    ]
    
    # Override with custom structure
    if structure.get("components"):
        components = structure["components"]
    
    for comp in components:
        content_parts.append(f'''
        <g transform="translate({comp["x"]}, {comp["y"]})">
          <rect x="0" y="0" width="160" height="80" fill="{comp["color"]}" rx="12"
                stroke="{colors["text"]}" stroke-width="1.5"/>
          <text x="80" y="30" font-family="Inter, system-ui" font-size="14" 
                fill="white" text-anchor="middle" font-weight="bold">{comp["name"]}</text>
          <text x="80" y="55" font-family="Inter, system-ui" font-size="11" 
                fill="white" text-anchor="middle">{comp["desc"]}</text>
        </g>''')
    
    return "\n".join(content_parts)

def _generate_generic(structure: dict, colors: dict) -> str:
    """Generate generic diagram"""
    nodes = structure.get("nodes", [])
    edges = structure.get("edges", [])
    
    content_parts = []
    
    # Background
    content_parts.append(f'<rect width="960" height="600" fill="{colors["bg"]}"/>')
    
    # Nodes
    for i, node in enumerate(nodes):
        x = node.get("x", 100 + i * 150)
        y = node.get("y", 200)
        name = node.get("name", f"Node {i+1}")
        color = node.get("color", colors["primary"])
        
        content_parts.append(f'''
        <g transform="translate({x}, {y})">
          <rect x="0" y="0" width="120" height="50" fill="{color}" rx="8"/>
          <text x="60" y="30" font-family="Inter, system-ui" font-size="12" 
                fill="white" text-anchor="middle">{name}</text>
        </g>''')
    
    # Edges
    for edge in edges:
        from_x = edge.get("from_x", 100)
        from_y = edge.get("from_y", 225)
        to_x = edge.get("to_x", 250)
        to_y = edge.get("to_y", 225)
        
        content_parts.append(f'''
        <line x1="{from_x + 120}" y1="{from_y}" x2="{to_x}" y2="{to_y}"
              stroke="{colors["arrow"]}" stroke-width="2" marker-end="url(#arrow)"/>''')
    
    return "\n".join(content_parts)


# ========== Convenience Functions ==========

def quick_architecture(name: str, layers: list, output_path: str = None) -> dict:
    """Quick generate architecture diagram"""
    return generate_diagram(
        diagram_type="architecture",
        structure={"name": name, "layers": layers}
    )

def quick_flowchart(name: str, steps: list, output_path: str = None) -> dict:
    """Quick generate flowchart"""
    return generate_diagram(
        diagram_type="flowchart",
        structure={"name": name, "steps": steps}
    )

def quick_agent(name: str = "agent_architecture") -> dict:
    """Quick generate agent architecture diagram"""
    return generate_diagram(
        diagram_type="agent",
        structure={"name": name}
    )

def quick_memory(name: str = "memory_architecture") -> dict:
    """Quick generate memory architecture diagram"""
    return generate_diagram(
        diagram_type="memory",
        structure={"name": name}
    )


if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    # Test
    print("Testing tech-diagram...")
    
    # Test architecture diagram
    result = quick_architecture(
        name="test_arch",
        layers=[
            {"name": "Client", "items": [{"name": "Web", "type": "primary"}]},
            {"name": "Services", "items": [{"name": "API", "type": "secondary"}, {"name": "Auth", "type": "secondary"}]},
            {"name": "Data", "items": [{"name": "DB", "type": "tertiary"}]}
        ]
    )
    
    if result["success"]:
        print(f"[OK] SVG: {result['svg_path']}")
        print(f"[OK] PNG: {result['png_path']}")
    else:
        print(f"[ERR] Error: {result['error']}")