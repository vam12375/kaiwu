"""Node2 品牌手册 HTML 构建器 —— 从 main.py 抽取"""
from datetime import datetime


def build_brand_manual_slides(sections: list, title: str) -> str:
    """构建杂志风品牌手册HTML - 4段式slides"""
    slides = ""
    ds = datetime.now().strftime("%Y-%m-%d")
    sections_clean = [s for s in sections if s.strip() and len(s.strip()) > 20]

    all_slides = []
    for sec in sections_clean:
        lines = sec.strip().split('\n')
        sec_title = lines[0].strip().lstrip('#').strip()[:20] if lines else "品牌章节"
        body_lines = lines[1:] if len(lines) > 1 else []
        body_html = ""
        char_count = 0
        for line in body_lines:
            s = line.strip()
            if s.startswith('|') and s.endswith('|'):
                cells = [c.strip() for c in s.split('|')[1:-1]]
                if cells:
                    body_html += '<div class="meta-row" data-anim>' + ' · '.join(cells[:4]) + '</div>'
                    char_count += len(s)
            elif s and not s.startswith('#'):
                s_clean = s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
                body_html += '<p class="body-zh" data-anim>' + s_clean[:400] + '</p>'
                char_count += len(s_clean)
            if char_count > 400:
                all_slides.append({"title": sec_title, "body": body_html})
                body_html = ""
                char_count = 0
        if body_html.strip():
            all_slides.append({"title": sec_title, "body": body_html})

    while len(all_slides) < 10:
        all_slides.append({"title": "品牌综合实力", "body": '<p class="body-zh" data-anim>本品牌手册基于Node2商业方案自动生成，涵盖目标用户画像、品牌定位策略、盈利模式设计与行动路径规划四大维度。所有数据来源于Node1市场调研与Node2商业分析。</p><div class="meta-row" data-anim>数据来源：曜势科技AI综合研判</div>'})

    actual_total = len(all_slides) + 1
    slides += (
        '<section class="slide hero dark">'
        '<div class="chrome"><div>品牌手册</div><div>01 / ' + str(actual_total).zfill(2) + '</div></div>'
        '<div class="frame" style="display:grid;gap:4vh;align-content:center;min-height:80vh">'
        '<div class="kicker" data-anim>BRAND MANUAL</div>'
        '<h1 class="h-hero" data-anim>品牌手册</h1>'
        '<p class="lead" style="max-width:50vw" data-anim>' + ds + ' · 曜势科技</p>'
        '</div><div class="foot"><div>品牌手册 · YaoShi Tech</div><div>— ' + ds + ' —</div></div>'
        '</section>'
    )

    for i, sl in enumerate(all_slides):
        pg = i + 2
        tc = "light" if i % 2 == 0 else "dark"
        slides += (
            '<section class="slide ' + tc + '">'
            '<div class="chrome"><div>品牌手册</div><div>' + str(pg).zfill(2) + ' / ' + str(actual_total).zfill(2) + '</div></div>'
            '<div class="frame" style="gap:3vh;padding-bottom:2vh;display:flex;flex-direction:column;justify-content:center">'
            '<h2 class="h-sub" data-anim style="font-size:3.8vw">' + sl["title"].replace('&','&amp;') + '</h2>'
            + sl["body"] +
            '</div>'
            '<div class="foot"><div>曜势科技 · AI生成</div><div>' + str(pg).zfill(2) + '</div></div>'
            '</section>'
        )

    return slides
