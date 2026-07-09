"""Markdown → HTML 渲染引擎 —— 纯函数，零副作用"""
import re


STORY_GROUP_BY_PREFIX = {
    "A": "痛点故事",
    "B": "品牌故事",
    "C": "客户故事",
    "D": "用户证言",
    "E": "愿景故事",
    "F": "创始人故事",
    "P": "产品故事",
}


def markdown_to_html(text: str) -> str:
    """Convert markdown to proper HTML"""
    lines = text.split('\n')
    result = []
    in_table = False
    list_type = None
    i = 0

    def close_list():
        nonlocal list_type
        if list_type:
            result.append(f'</{list_type}>')
            list_type = None

    def close_table():
        nonlocal in_table
        if in_table:
            result.append('</tbody></table>')
            in_table = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped == '':
            close_list()
            close_table()
            i += 1
            continue

        if stripped.startswith('#### '):
            close_list()
            close_table()
            result.append(f'<h4>{_escape_html(stripped[5:])}</h4>')
        elif stripped.startswith('### '):
            close_list()
            close_table()
            result.append(f'<h3>{_escape_html(stripped[4:])}</h3>')
        elif stripped.startswith('## '):
            close_list()
            close_table()
            result.append(f'<h2>{_escape_html(stripped[3:])}</h2>')
        elif stripped.startswith('# '):
            close_list()
            close_table()
            result.append(f'<h1>{_escape_html(stripped[2:])}</h1>')
        elif stripped == '---':
            close_list()
            close_table()
            result.append('<hr>')
        elif stripped.startswith('> '):
            close_list()
            close_table()
            result.append(f'<blockquote>{_render_inline(stripped[2:])}</blockquote>')
        elif stripped.startswith('|') and stripped.endswith('|'):
            close_list()
            close_table()
            table_lines = []
            while i < len(lines) and _is_table_line(lines[i].strip()):
                table_lines.append(lines[i].strip())
                i += 1
            result.append(_render_table_block(table_lines))
            continue
        elif stripped.startswith('- '):
            close_table()
            if list_type != 'ul':
                close_list()
                result.append('<ul>')
                list_type = 'ul'
            result.append(f'<li>{_render_inline(stripped[2:])}</li>')
        elif re.match(r'^\d+[、.)] ', stripped):
            close_table()
            if list_type != 'ol':
                close_list()
                result.append('<ol>')
                list_type = 'ol'
            content = re.sub(r'^\d+[、.)] ', '', stripped)
            result.append(f'<li>{_render_inline(content)}</li>')
        else:
            close_list()
            close_table()
            if stripped == '```':
                i += 1
                continue
            class_name = ' class="lead-line"' if stripped.startswith('**') and ('：' in stripped or ':' in stripped) else ''
            result.append(f'<p{class_name}>{_render_inline(stripped)}</p>')
        i += 1

    close_list()
    close_table()

    return '\n'.join(result)


def _escape_html(text: str) -> str:
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _render_inline(text: str) -> str:
    text = _escape_html(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    return text


def _is_table_line(stripped: str) -> bool:
    return stripped.startswith('|') and stripped.endswith('|')


def _split_table_row(line: str) -> list[str]:
    return [c.strip() for c in line.split('|')[1:-1]]


def _is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.match(r'^[-:\s]+$', c) for c in cells)


def _render_table_block(table_lines: list[str]) -> str:
    rows = []
    for line in table_lines:
        cells = _split_table_row(line)
        if not _is_separator_row(cells):
            rows.append(cells)
    if not rows:
        return ""

    headers = rows[0]
    body_rows = [_pad_row(row, len(headers)) for row in rows[1:]]
    if _is_story_output_table(headers, body_rows):
        return _render_story_accordion(headers, body_rows)

    html = ['<table><thead>']
    html.append('<tr>' + ''.join(f'<th>{_render_inline(c)}</th>' for c in headers) + '</tr>')
    html.append('</thead><tbody>')
    for row in body_rows:
        html.append('<tr>' + ''.join(f'<td>{_cell_html(c)}</td>' for c in row) + '</tr>')
    html.append('</tbody></table>')
    return '\n'.join(html)


def _pad_row(row: list[str], width: int) -> list[str]:
    if len(row) >= width:
        return row[:width]
    return row + [""] * (width - len(row))


def _normalize_header(header: str) -> str:
    header = re.sub(r'[\s*`：:]+', '', header)
    return header.lower()


def _header_index(headers: list[str]) -> dict[str, int]:
    return {_normalize_header(header): idx for idx, header in enumerate(headers)}


def _first_index(index: dict[str, int], names: list[str]) -> int | None:
    for name in names:
        key = _normalize_header(name)
        for header_key, idx in index.items():
            if header_key == key or header_key.startswith(key):
                return idx
    return None


def _is_story_output_table(headers: list[str], rows: list[list[str]]) -> bool:
    if not rows:
        return False
    index = _header_index(headers)
    required = ["核心金句", "短视频脚本", "图文文案", "私域文案"]
    has_required = all(_first_index(index, [name]) is not None for name in required)
    has_platform = _first_index(index, ["适用平台", "平台"]) is not None
    has_code = _first_index(index, ["序号", "内容编号", "故事编号", "故事ID"]) is not None
    has_story_context = _first_index(index, ["故事类型", "故事ID", "故事角度"]) is not None
    return has_required and has_platform and has_code and has_story_context


def _render_story_accordion(headers: list[str], rows: list[list[str]]) -> str:
    index = _header_index(headers)
    code_idx = _first_index(index, ["序号", "内容编号", "故事编号"])
    story_id_idx = _first_index(index, ["故事ID"])
    if code_idx is None:
        code_idx = story_id_idx
    type_idx = _first_index(index, ["故事类型"])
    angle_idx = _first_index(index, ["故事角度"])
    platform_idx = _first_index(index, ["适用平台", "平台"])
    quote_idx = _first_index(index, ["核心金句"])

    groups: list[dict] = []
    group_lookup: dict[str, dict] = {}
    for row in rows:
        code = _plain_cell(row[code_idx]) if code_idx is not None else ""
        group_title = _story_group_title(row, code, type_idx)
        if group_title not in group_lookup:
            group_lookup[group_title] = {"title": group_title, "rows": []}
            groups.append(group_lookup[group_title])
        group_lookup[group_title]["rows"].append(row)

    parts = ['<div class="story-accordion">']
    opened = False
    for group in groups:
        parts.append('  <section class="story-group">')
        parts.append(
            f'    <div class="story-group-title"><strong>{_escape_html(group["title"])}</strong>'
            f'<span>{len(group["rows"])}条内容</span></div>'
        )
        for row in group["rows"]:
            code = _plain_cell(row[code_idx]) if code_idx is not None else ""
            story_label = _story_summary_label(row, type_idx, story_id_idx, code_idx, group["title"])
            angle = _plain_cell(row[angle_idx]) if angle_idx is not None else ""
            summary_title = story_label if not angle or angle == story_label else f"{story_label} · {angle}"
            quote = row[quote_idx] if quote_idx is not None else ""
            platforms = _split_platforms(row[platform_idx]) if platform_idx is not None else []
            open_attr = " open" if not opened else ""
            opened = True

            parts.append(f'    <details class="story-item"{open_attr}>')
            parts.append('      <summary>')
            parts.append(f'        <span class="story-code">{_cell_html(code)}</span>')
            parts.append('        <span class="story-summary-main">')
            parts.append(f'          <span class="story-summary-title">{_cell_html(summary_title)}</span>')
            parts.append(f'          <span class="story-quote">{_cell_html(quote)}</span>')
            parts.append('        </span>')
            parts.append('        <span class="story-platforms">' + ''.join(f'<span>{_cell_html(p)}</span>' for p in platforms) + '</span>')
            parts.append('      </summary>')
            parts.append('      <div class="story-detail">')
            parts.append(_render_story_meta_field(headers, row, code_idx, story_id_idx, type_idx, angle_idx, platform_idx))
            for idx, header in enumerate(headers):
                if idx in {code_idx, story_id_idx, type_idx, angle_idx, platform_idx}:
                    continue
                value = row[idx] if idx < len(row) else ""
                css_class = " story-field quote-block" if idx == quote_idx else " story-field"
                parts.append(_render_story_field(header, value, css_class))
            parts.append('      </div>')
            parts.append('    </details>')
        parts.append('  </section>')
    parts.append('</div>')
    return '\n'.join(parts)


def _story_group_title(row: list[str], code: str, type_idx: int | None) -> str:
    if type_idx is not None and row[type_idx].strip():
        return _plain_cell(row[type_idx])
    match = re.match(r'([A-Za-z])', code.strip())
    if match:
        return STORY_GROUP_BY_PREFIX.get(match.group(1).upper(), "故事内容")
    return "故事内容"


def _story_summary_label(
    row: list[str],
    type_idx: int | None,
    story_id_idx: int | None,
    code_idx: int | None,
    fallback: str,
) -> str:
    if type_idx is not None and row[type_idx].strip():
        return _plain_cell(row[type_idx])
    if story_id_idx is not None and story_id_idx != code_idx and row[story_id_idx].strip():
        return _plain_cell(row[story_id_idx])
    return fallback


def _render_story_meta_field(
    headers: list[str],
    row: list[str],
    code_idx: int | None,
    story_id_idx: int | None,
    type_idx: int | None,
    angle_idx: int | None,
    platform_idx: int | None,
) -> str:
    meta_indexes = [code_idx, story_id_idx, type_idx, angle_idx, platform_idx]
    seen = set()
    meta_parts = []
    for idx in meta_indexes:
        if idx is None or idx in seen:
            continue
        seen.add(idx)
        if idx >= len(headers):
            continue
        label = headers[idx]
        value = row[idx] if idx < len(row) else ""
        meta_parts.append(f'<span><strong>{_cell_html(label)}：</strong>{_cell_html(value)}</span>')
    return (
        '        <div class="story-field story-meta-field"><div class="story-field-label">基础信息</div>\n'
        f'          <div class="story-field-body">{"".join(meta_parts)}</div></div>'
    )


def _render_story_field(label: str, value: str, css_class: str) -> str:
    return (
        f'        <div class="{css_class.strip()}"><div class="story-field-label">{_cell_html(label)}</div>\n'
        f'          <div class="story-field-body">{_cell_html(value)}</div></div>'
    )


def _split_platforms(value: str) -> list[str]:
    parts = [p.strip() for p in re.split(r'[、,，/+]+', _plain_cell(value)) if p.strip()]
    return parts or [_plain_cell(value)] if value.strip() else []


def _plain_cell(value: str) -> str:
    text = re.sub(r'<br\s*/?>', ' ', value, flags=re.I)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    return re.sub(r'\s+', ' ', text).strip()


def _cell_html(value: str) -> str:
    html = _render_inline(value.strip())
    html = re.sub(r'&lt;br\s*/?&gt;', '<br>', html, flags=re.I)
    return html
