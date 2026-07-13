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

_DEV_NODE_TOKEN = r"node(?:0|1(?:\.5)?|2|3(?:\.1)?|4|5)"
_DEV_NODE_TOKEN_RE = re.compile(rf"(^|[^A-Za-z0-9_])({_DEV_NODE_TOKEN})(?![A-Za-z0-9_])", re.I)
_DEV_NODE_ONLY_RE = re.compile(_DEV_NODE_TOKEN, re.I)
_DEV_BRACKET_CONSTRAINT_RE = re.compile(r"[\[【]\s*(?:≥|&gt;=?|>=?)?\s*\d+\s*(?:秒|字)(?:脚本|图文|私域)?\s*[\]】]")
_DEV_PAREN_CONSTRAINT_RE = re.compile(
    r"[（(][^）)]*(?:(?:≥|&gt;=?|>=?)\s*\d+\s*字|至少\s*\d+\s*行|\d+\s*大模块|MVP原则)[^）)]*[）)]"
)
_DEV_PAREN_SUMMARY_RE = re.compile(r"[（(]\s*结语\s*[）)]")
_DEV_HINT_LINE_PATTERNS = [
    re.compile(r"^`{2,3}$"),
    re.compile(rf"^（由\s*{_DEV_NODE_TOKEN}\s*[^）]*自动生成）$", re.I),
    re.compile(rf"^现在开始执行\s*{_DEV_NODE_TOKEN}\s*.+$", re.I),
    re.compile(rf"^调取节点\s*[:：]\s*{_DEV_NODE_TOKEN}\s*$", re.I),
    re.compile(rf"^以上为\s*{_DEV_NODE_TOKEN}\s*.+(?:完整输出|已全部呈现)[。.]?$", re.I),
]


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

        if _is_developer_hint_line(stripped):
            close_list()
            close_table()
            result.append(_render_dev_ghost_line(line))
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


def _normalize_developer_hint_line(text: str) -> str:
    text = re.sub(r"^#+\s*", "", text)
    text = re.sub(r"^>\s*", "", text)
    text = re.sub(r"^\*+|\*+$", "", text)
    return text.strip()


def _is_developer_constraint_only_line(text: str) -> bool:
    cleaned = _DEV_NODE_ONLY_RE.sub("", text)
    cleaned = re.sub(r"dialogue_brief\.md", "", cleaned, flags=re.I)
    cleaned = _DEV_BRACKET_CONSTRAINT_RE.sub("", cleaned)
    cleaned = _DEV_PAREN_CONSTRAINT_RE.sub("", cleaned)
    cleaned = _DEV_PAREN_SUMMARY_RE.sub("", cleaned)
    cleaned = re.sub(r"[`*_#>\-\s+.,，。:：/|、()[\]（）【】]+", "", cleaned)
    return cleaned == "" and cleaned != text


def _is_developer_hint_line(text: str) -> bool:
    normalized = _normalize_developer_hint_line(text)
    if not normalized:
        return False
    return any(pattern.search(normalized) for pattern in _DEV_HINT_LINE_PATTERNS) or _is_developer_constraint_only_line(normalized)


def _render_dev_ghost_line(text: str) -> str:
    return f'<div class="dev-ghost-line" aria-hidden="true">{_escape_html(text)}</div>'


def _wrap_dev_ghost(value: str) -> str:
    return f'<span class="dev-ghost" aria-hidden="true">{value}</span>'


def _conceal_developer_hints(html: str) -> str:
    html = _DEV_BRACKET_CONSTRAINT_RE.sub(lambda match: _wrap_dev_ghost(match.group(0)), html)
    html = _DEV_PAREN_CONSTRAINT_RE.sub(lambda match: _wrap_dev_ghost(match.group(0)), html)
    html = _DEV_PAREN_SUMMARY_RE.sub(lambda match: _wrap_dev_ghost(match.group(0)), html)
    html = re.sub(r"dialogue_brief\.md", lambda match: _wrap_dev_ghost(match.group(0)), html, flags=re.I)
    return _DEV_NODE_TOKEN_RE.sub(lambda match: f"{match.group(1)}{_wrap_dev_ghost(match.group(2))}", html)


def _render_inline(text: str) -> str:
    text = _escape_html(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    return _conceal_developer_hints(text)


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
    body_rows = [_fit_row(row, len(headers)) for row in rows[1:]]
    if _is_story_output_table(headers, body_rows):
        return _render_story_accordion(headers, body_rows)

    table_classes = [f"table-cols-{len(headers)}"]
    if _is_key_value_table(headers):
        table_classes.append("table-kv")
    html = [f'<table class="{" ".join(table_classes)}">']
    html.append(_render_colgroup(headers, body_rows))
    html.append('<thead>')
    html.append('<tr>' + ''.join(f'<th class="{_cell_class(headers, body_rows, idx)}">{_render_inline(c)}</th>' for idx, c in enumerate(headers)) + '</tr>')
    html.append('</thead><tbody>')
    for row in body_rows:
        html.append('<tr>' + ''.join(f'<td class="{_cell_class(headers, body_rows, idx)}">{_cell_html(c)}</td>' for idx, c in enumerate(row)) + '</tr>')
    html.append('</tbody></table>')
    return '\n'.join(html)


def _fit_row(row: list[str], width: int) -> list[str]:
    if width <= 0:
        return row
    if len(row) > width:
        return row[:width - 1] + [" | ".join(row[width - 1:])]
    if len(row) == width:
        return row
    return row + [""] * (width - len(row))


def _content_length_weight(longest_value: int, average_value: float) -> float:
    score = max(longest_value * 0.72, average_value * 1.28)
    if score <= 4:
        return 0.68
    if score <= 8:
        return 0.92
    if score <= 14:
        return 1.2
    if score <= 24:
        return 1.55
    if score <= 42:
        return 2.08
    return 2.7


def _clamp_weight(weight: float, minimum: float, maximum: float) -> float:
    return min(max(weight, minimum), maximum)


def _is_key_value_table(headers: list[str]) -> bool:
    header_keys = [_normalize_header(item) for item in headers]
    return (
        len(headers) == 2
        and re.search(r"^(维度|项目|类别|平台|渠道|方式|指标|要素)$", header_keys[0] if header_keys else "")
        and re.search(r"^(内容|说明|描述|结论|优先级)$", header_keys[1] if len(header_keys) > 1 else "")
    )


def _column_weight(header: str, rows: list[list[str]], index: int, headers: list[str]) -> float:
    key = _normalize_header(header)
    table_width = len(headers)
    values = [_plain_cell(row[index]) if index < len(row) else "" for row in rows]
    longest_value = max([len(key), *[len(value) for value in values]], default=0)
    average_value = sum(len(value) for value in values) / len(values) if values else 0
    content_weight = _content_length_weight(longest_value, average_value)
    if _is_key_value_table(headers):
        return _clamp_weight(content_weight, 0.54, 0.74) if index == 0 else _clamp_weight(content_weight, 2.75, 3.55)
    if re.search(r"^(人数|人次|数量)$", key) and longest_value <= 8:
        return _clamp_weight(content_weight, 0.55, 0.82)
    if re.search(r"^(来源|依据|依据章节|轮次)$", key) and longest_value <= 12:
        return _clamp_weight(content_weight, 0.7, 1.0)
    if re.search(r"^(角色|资产类型|类型|类别|项目|维度|平台|渠道|方式|阶段|状态|固定变动)$", key) and longest_value <= 16:
        return _clamp_weight(content_weight, 0.75, 1.15)
    if table_width >= 3 and longest_value <= 12 and average_value <= 8:
        return _clamp_weight(content_weight, 0.72, 1.08)
    if table_width == 3:
        if index == 0 and re.search(r"^(月|月份|阶段|方式|媒介|渠道|平台|类型|类目)$", key):
            return _clamp_weight(content_weight, 0.78, 1.05)
        if index == 1 and re.search(r"^(目标|内容形式|故事类型|维度|说明)$", key):
            return _clamp_weight(content_weight, 1.35, 2.35)
        if index == 2 and re.search(r"^(内容|内容产出|输出内容|频率|发布频率|节奏|发布节奏|说明|优先级)$", key):
            return _clamp_weight(content_weight, 1.9, 2.85)
    if key in {"序号", "编号", "排名", "id", "no", "痛点编号"}:
        return _clamp_weight(content_weight, 0.55, 0.82)
    if re.search(r"^(年份|年度)$", key):
        return _clamp_weight(content_weight, 0.82, 1.28)
    if re.search(r"^(月|月份|阶段|方式|媒介|渠道|平台|故事类型|内容形式|目标|类型|类目|竞品名|品牌名|竞争者)$", key):
        return _clamp_weight(content_weight, 0.88, 1.35)
    if re.search(r"^(频率|发布频率|节奏|发布节奏)$", key):
        return _clamp_weight(content_weight, 1.7, 2.65)
    if re.search(r"^(内容|内容产出|输出内容|核心内容)$", key):
        return _clamp_weight(content_weight, 2.25, 3.1)
    if re.search(r"(数据来源|来源|测算依据|时效限制|依据|备注|说明)", key):
        if longest_value <= 24:
            return _clamp_weight(content_weight, 1.05, 1.85)
        return _clamp_weight(content_weight, 1.85, 3.05)
    if re.search(r"(核心特征|明显短板|短板|缺陷|不足|机会点|机会|风险|解决方案|方案|解法|需求|痛点|描述|说明|具体说明|原因|建议|方向|策略|内容|分析|结论|理由|脚本|文案|金句)", key):
        return _clamp_weight(content_weight, 2.15, 3.25)
    if re.search(r"(目标人群|核心人群|用户画像|人群画像|客群|受众)", key):
        return _clamp_weight(content_weight, 1.45, 2.45)
    if re.search(r"(市场规模|预测市场规模|规模|用户规模|门店规模|营收规模|年营收|融资)", key):
        return _clamp_weight(content_weight, 1.0, 1.65)
    if re.search(r"(同比增速|预测增速|增速|增长率|复合增长率|cagr)$", key, re.I):
        return _clamp_weight(content_weight, 0.82, 1.18)
    if re.search(r"(市占率|占比|比例|评分|程度|紧迫度|可行性|等级|状态)$", key):
        return _clamp_weight(content_weight, 0.78, 1.2)
    if re.search(r"(时间|周期|数量|容量|预算|金额|价格|单价|成本|售价|毛利|预估|价格带)$", key):
        return _clamp_weight(content_weight, 0.9, 1.35)
    return _clamp_weight(content_weight, 0.8, 2.7)


def _render_colgroup(headers: list[str], rows: list[list[str]]) -> str:
    if not headers:
        return ""
    weights = [_column_weight(header, rows, idx, headers) for idx, header in enumerate(headers)]
    total = sum(weights) or 1
    cols = "".join(f'<col style="width:{(weight / total) * 100:.2f}%">' for weight in weights)
    return f"<colgroup>{cols}</colgroup>"


def _is_right_aligned_column(header: str, rows: list[list[str]], index: int) -> bool:
    key = _normalize_header(header)
    if index == 0:
        return False
    if re.search(r"^(年份|年度)$", key):
        return False
    if re.search(r"(收入来源|数据来源|来源|测算依据|时效限制|依据|备注|说明)", key):
        return False
    if re.search(r"(同比增速|预测增速|增速|增长率|复合增长率|cagr|市占率|占比|比例|评分|程度|紧迫度|可行性|等级|状态)$", key, re.I):
        return True
    if re.search(r"(市场规模|预测市场规模|用户规模|门店规模|营收规模|年营收|融资|预算|金额|价格|单价|成本|售价|毛利|价格带)$", key):
        return True
    if re.search(r"(收入估算|月收入|年收入|稳定期月收入估算)$", key):
        return True
    return False


def _column_longest_value(header: str, rows: list[list[str]], index: int) -> int:
    key = _normalize_header(header)
    values = [_plain_cell(row[index]) if index < len(row) else "" for row in rows]
    return max([len(key), *[len(value) for value in values]], default=0)


def _is_descriptive_or_source_column(header: str) -> bool:
    key = _normalize_header(header)
    return bool(
        re.search(
            r"(年份|年度|收入来源|数据来源|来源|测算依据|时效限制|依据|备注|说明|内容|描述|结论|核心特征|机会点|风险|策略|建议|脚本|文案|金句)",
            key,
        )
    )


def _is_compact_two_column_comparison_table(headers: list[str], rows: list[list[str]]) -> bool:
    if len(headers) != 2 or not rows:
        return False
    if _is_key_value_table(headers):
        return False
    if any(_is_descriptive_or_source_column(header) for header in headers):
        return False
    return all(_column_longest_value(header, rows, idx) <= 18 for idx, header in enumerate(headers))


def _is_center_aligned_column(header: str, rows: list[list[str]], index: int) -> bool:
    if _is_right_aligned_column(header, rows, index):
        return False
    key = _normalize_header(header)
    if re.search(r"^(年份|年度|收入来源|数据来源|测算依据|时效限制|备注|说明)$", key):
        return False
    longest_value = _column_longest_value(header, rows, index)
    values = [_plain_cell(row[index]) if index < len(row) else "" for row in rows]
    values = [value for value in values if value]
    average_value = sum(len(value) for value in values) / len(values) if values else 0
    if re.search(r"^(序号|编号|排名|id|no|痛点编号|类目|类别|项目|维度|方式|渠道|平台|媒介|阶段|类型|月份|月|人数|人次|数量|来源|依据|依据章节|轮次|角色|资产类型|固定变动)$", key, re.I):
        return longest_value <= 18
    return bool(
        rows
        and longest_value <= 18
        and average_value <= 12
    )


def _cell_class(headers: list[str], rows: list[list[str]], index: int) -> str:
    header = headers[index] if index < len(headers) else ""
    key = _normalize_header(header)
    classes = ["table-cell"]
    key_value_table = _is_key_value_table(headers)
    if key_value_table and index == 0:
        classes.append("cell-label")
    if _is_compact_two_column_comparison_table(headers, rows):
        classes.append("cell-center")
    else:
        if _is_right_aligned_column(header, rows, index):
            classes.append("cell-right")
        if not key_value_table and _is_center_aligned_column(header, rows, index):
            classes.append("cell-center")
    if key in {"序号", "编号", "排名", "id", "no", "痛点编号"}:
        classes.append("cell-compact")
    if re.search(r"(核心特征|短板|缺陷|不足|机会点|机会|风险|解决方案|方案|解法|需求|痛点|描述|说明|具体说明|原因|建议|方向|策略|内容|分析|结论|理由|脚本|文案|金句)", key):
        classes.append("cell-rich")
    return " ".join(classes)


def _normalize_header(header: str) -> str:
    header = re.sub(r"[（(][^）)]*[）)]", "", header)
    header = re.sub(r'[\s*`：:]+', '', header)
    return header.lower()


def _header_index(headers: list[str]) -> dict[str, int]:
    return {_normalize_header(header): idx for idx, header in enumerate(headers)}


def _first_index(index: dict[str, int], names: list[str]) -> int | None:
    for name in names:
        key = _normalize_header(name)
        for header_key, idx in index.items():
            if not header_key:
                continue
            if header_key == key or header_key.startswith(key) or key in header_key or header_key in key:
                return idx
    return None


def _is_story_output_table(headers: list[str], rows: list[list[str]]) -> bool:
    if not rows:
        return False
    index = _header_index(headers)
    story_indexes = [
        _first_index(index, ["核心金句", "金句"]),
        _first_index(index, ["短视频脚本", "短视频", "视频脚本"]),
        _first_index(index, ["图文文案", "图文"]),
        _first_index(index, ["私域文案", "私域"]),
        _first_index(index, ["适用平台", "平台"]),
    ]
    story_field_count = len({idx for idx in story_indexes if idx is not None})
    has_code = _first_index(index, ["序号", "内容编号", "故事编号", "故事ID"]) is not None
    has_story_context = _first_index(index, ["故事类型", "故事ID", "故事角度"]) is not None
    return has_code and has_story_context and story_field_count >= 4


def _render_story_accordion(headers: list[str], rows: list[list[str]]) -> str:
    index = _header_index(headers)
    code_idx = _first_index(index, ["序号", "内容编号", "故事编号"])
    story_id_idx = _first_index(index, ["故事ID"])
    if code_idx is None:
        code_idx = story_id_idx
    type_idx = _first_index(index, ["故事类型"])
    angle_idx = _first_index(index, ["故事角度"])
    platform_idx = _first_index(index, ["适用平台", "平台"])
    quote_idx = _first_index(index, ["核心金句", "金句"])

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
    plain_label = _plain_cell(label)
    plain_value = _plain_cell(value)
    is_quote = "quote-block" in css_class
    should_collapse = (not is_quote) and re.search(r"(短视频脚本|视频脚本|图文文案|私域文案|正文|脚本|文案)", plain_label)
    if should_collapse:
        return (
            f'        <details class="{css_class.strip()} story-collapsible-field"><summary>'
            f'<span class="story-field-label">{_cell_html(label)}</span><span class="story-field-count">{len(plain_value)}字</span></summary>\n'
            f'          <div class="story-field-body">{_cell_html(value)}</div></details>'
        )
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
