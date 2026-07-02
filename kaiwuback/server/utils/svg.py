"""SVG Logo 生成与 Logo Prompt 提取 —— 纯函数，零副作用"""
import re


def generate_logo_svg(params: dict) -> str:
    """Generate a clean SVG logo from structured parameters."""
    shape = params.get("shape", "circle")
    main = params.get("mainColor", "#1a1a2e")
    accent = params.get("accentColor", "#e8b86d")
    text = params.get("text", "")[:4]
    element = params.get("element", "")

    cx, cy = 200, 200
    svg_parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">',
        '<rect width="400" height="400" fill="#FFFFFF"/>',
    ]

    shapes = {
        "circle": f'<circle cx="{cx}" cy="{cy}" r="110" fill="none" stroke="{main}" stroke-width="4"/>',
        "diamond": f'<polygon points="200,70 330,200 200,330 70,200" fill="none" stroke="{main}" stroke-width="4"/>',
        "hexagon": f'<polygon points="200,80 295,140 295,260 200,320 105,260 105,140" fill="none" stroke="{main}" stroke-width="4"/>',
        "shield": f'<path d="M200,70 L290,120 L290,240 C290,300 200,340 200,340 C200,340 110,300 110,240 L110,120 Z" fill="none" stroke="{main}" stroke-width="4"/>',
        "roundrect": f'<rect x="90" y="90" width="220" height="220" rx="30" fill="none" stroke="{main}" stroke-width="4"/>',
        "triangle": f'<polygon points="200,60 340,340 60,340" fill="none" stroke="{main}" stroke-width="4"/>',
    }

    elements = {
        "star": f'<polygon points="200,100 210,140 250,140 218,160 228,200 200,178 172,200 182,160 150,140 190,140" fill="{accent}"/>',
        "heart": f'<path d="M200,230 C200,230 140,180 140,140 C140,115 165,100 185,110 C195,115 200,125 200,130 C200,125 205,115 215,110 C235,100 260,115 260,140 C260,180 200,230 200,230Z" fill="{accent}" opacity="0.8"/>',
        "leaf": f'<path d="M200,230 C200,230 170,180 180,140 C190,120 210,140 200,170 C190,140 210,120 220,140 C230,180 200,230 200,230Z" fill="{accent}" opacity="0.7"/>',
        "crown": f'<path d="M130,150 L150,100 L170,130 L200,90 L230,130 L250,100 L270,150 Z" fill="none" stroke="{accent}" stroke-width="3"/>',
        "paw": f'<ellipse cx="170" cy="180" rx="25" ry="30" fill="{accent}" opacity="0.6"/><ellipse cx="230" cy="180" rx="25" ry="30" fill="{accent}" opacity="0.6"/><ellipse cx="200" cy="150" rx="35" ry="28" fill="{accent}" opacity="0.8"/>',
        "moon": f'<path d="M230,110 A80,80 0 1,0 260,190 A90,90 0 1,1 230,110Z" fill="{accent}" opacity="0.8"/>',
        "gem": f'<polygon points="200,110 250,150 200,260 150,150" fill="none" stroke="{accent}" stroke-width="3"/><line x1="200" y1="150" x2="200" y2="200" stroke="{accent}" stroke-width="2"/>',
    }

    svg_parts.append(shapes.get(shape, shapes["circle"]))

    if shape in ("circle", "roundrect", "hexagon"):
        svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="85" fill="none" stroke="{accent}" stroke-width="1.5" stroke-dasharray="8,6" opacity="0.5"/>')

    el_key = element.lower() if element else "star"
    for key, svg_code in elements.items():
        if key in el_key or (el_key in key):
            svg_parts.append(svg_code)
            break
    else:
        svg_parts.append(elements["star"])

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def extract_logo_prompts(ai_text: str, node_id: str) -> list:
    """Extract logo prompts from AI response. Returns [(style, prompt), ...]"""
    prompts = []
    if node_id == "node3.1":
        m = re.search(r'图片生成Prompt[：:]\s*(.+?)(?:\n|$)', ai_text)
        if m:
            prompt = m.group(1).strip()
            if prompt and len(prompt) > 10:
                prompts.append(("用户图片", prompt))
        return prompts[:3]
    for match in re.finditer(r'###\s*风格\d+[：:]\s*(.+?)\n.*?图片生成Prompt[：:]\s*(.+?)(?:\n|---|$)', ai_text, re.DOTALL):
        style = match.group(1).strip()
        prompt = match.group(2).strip()
        clean_prompt = prompt.replace('--ar 1:1', '').strip()
        if clean_prompt and len(clean_prompt) > 10:
            prompts.append((style, clean_prompt + ' --ar 1:1'))
    if not prompts:
        for match in re.finditer(r'\*\*风格\d+[：:]\s*(.+?)\*\*.*?中文Prompt[：:]\s*(.+?)(?:\n|$)', ai_text, re.DOTALL):
            prompts.append((match.group(1).strip(), match.group(2).strip()))
    return prompts[:3]
