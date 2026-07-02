"""Markdown → HTML 渲染引擎 —— 纯函数，零副作用"""
import re


def markdown_to_html(text: str) -> str:
    """Convert markdown to proper HTML"""
    lines = text.split('\n')
    result = []
    in_table = False
    in_list = False
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped == '':
            if in_list:
                result.append('</ul>')
                in_list = False
            if in_table:
                result.append('</tbody></table>')
                in_table = False
            i += 1
            continue

        if stripped.startswith('#### '):
            result.append(f'<h4>{_escape_html(stripped[5:])}</h4>')
        elif stripped.startswith('### '):
            result.append(f'<h3>{_escape_html(stripped[4:])}</h3>')
        elif stripped.startswith('## '):
            result.append(f'<h2>{_escape_html(stripped[3:])}</h2>')
        elif stripped.startswith('# '):
            result.append(f'<h1>{_escape_html(stripped[2:])}</h1>')
        elif stripped == '---' or stripped == '---':
            result.append('<hr>')
        elif stripped.startswith('> '):
            result.append(f'<blockquote>{_render_inline(stripped[2:])}</blockquote>')
        elif stripped.startswith('|') and stripped.endswith('|'):
            if not in_table:
                result.append('<table><thead>')
                in_table = True
                is_header = True
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            if all(re.match(r'^[-:\s]+$', c) for c in cells):
                result.append('</thead><tbody>')
                is_header = False
            else:
                tag = 'th' if (in_table and result[-1] == '<table><thead>') else 'td'
                result.append('<tr>' + ''.join(f'<{tag}>{_render_inline(c)}</{tag}>' for c in cells) + '</tr>')
                if tag == 'th' and i + 1 < len(lines) and not (lines[i+1].strip().startswith('|') and all(re.match(r'^[-:\s]+$', c) for c in lines[i+1].strip().split('|')[1:-1])):
                    result.append('</thead><tbody>')
        elif stripped.startswith('- '):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append(f'<li>{_render_inline(stripped[2:])}</li>')
        elif re.match(r'^\d+[、.)] ', stripped):
            if not in_list:
                result.append('<ol>')
                in_list = True
            content = re.sub(r'^\d+[、.)] ', '', stripped)
            result.append(f'<li>{_render_inline(content)}</li>')
        else:
            if in_list:
                result.append('</ul>' if not (result and result[-1].startswith('<ol')) else '</ol>')
                in_list = False
            result.append(f'<p>{_render_inline(stripped)}</p>')
        i += 1

    if in_list:
        result.append('</ul>')
    if in_table:
        result.append('</tbody></table>')

    return '\n'.join(result)


def _escape_html(text: str) -> str:
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _render_inline(text: str) -> str:
    text = _escape_html(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    return text
