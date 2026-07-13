from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


DESKTOP = Path("/Users/wangzijian/Desktop")
PDF_PATH = DESKTOP / "Kaiwu · 使用说明书-2026年07月10日.pdf"
MD_PATH = DESKTOP / "Kaiwu · 使用说明书-2026年07月10日.md"


def first_existing(paths):
    for path in paths:
        if Path(path).exists():
            return str(path)
    raise FileNotFoundError(paths)


FONT_PATH = first_existing(
    [
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
    ]
)
MONO_PATH = first_existing(
    [
        "/Library/Fonts/SourceCodePro-Regular.ttf",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
    ]
)

pdfmetrics.registerFont(TTFont("KaiwuSans", FONT_PATH))
pdfmetrics.registerFont(TTFont("KaiwuMono", MONO_PATH))


class Divider(Flowable):
    def __init__(self, color="#111827", thickness=1.1):
        super().__init__()
        self.color = colors.HexColor(color)
        self.thickness = thickness
        self.height = 13

    def wrap(self, avail_width, avail_height):
        self.width = avail_width
        return avail_width, self.height

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, self.height / 2, self.width, self.height / 2)


class Callout(Flowable):
    def __init__(self, lines, style, fill="#F3F4F6", accent="#D8B58A"):
        super().__init__()
        self.lines = lines
        self.style = style
        self.fill = colors.HexColor(fill)
        self.accent = colors.HexColor(accent)
        self.paras = [Paragraph(line, style) for line in lines]

    def wrap(self, avail_width, avail_height):
        inner_width = avail_width - 25
        self._sizes = [para.wrap(inner_width, avail_height) for para in self.paras]
        self.width = avail_width
        self.height = sum(h for _, h in self._sizes) + 22 + (len(self.paras) - 1) * 4
        return self.width, self.height

    def draw(self):
        self.canv.setFillColor(self.fill)
        self.canv.rect(0, 0, self.width, self.height, stroke=0, fill=1)
        self.canv.setFillColor(self.accent)
        self.canv.rect(0, 0, 2.2, self.height, stroke=0, fill=1)
        y = self.height - 13
        for para, (_, h) in zip(self.paras, self._sizes):
            y -= h
            para.drawOn(self.canv, 15, y)
            y -= 4


def esc(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


styles = getSampleStyleSheet()
title = ParagraphStyle(
    "Title",
    parent=styles["Title"],
    fontName="KaiwuSans",
    fontSize=27,
    leading=34,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#6E503D"),
    spaceAfter=10,
    wordWrap="CJK",
)
subtitle = ParagraphStyle(
    "Subtitle",
    parent=styles["Normal"],
    fontName="KaiwuSans",
    fontSize=12,
    leading=17,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#8E8E8E"),
    spaceAfter=34,
    wordWrap="CJK",
)
h1 = ParagraphStyle(
    "H1",
    parent=styles["Heading1"],
    fontName="KaiwuSans",
    fontSize=16,
    leading=22,
    textColor=colors.HexColor("#1F2937"),
    spaceBefore=15,
    spaceAfter=9,
    wordWrap="CJK",
)
h2 = ParagraphStyle(
    "H2",
    parent=styles["Heading2"],
    fontName="KaiwuSans",
    fontSize=12.8,
    leading=18,
    textColor=colors.HexColor("#374151"),
    spaceBefore=8,
    spaceAfter=5,
    wordWrap="CJK",
)
body = ParagraphStyle(
    "Body",
    parent=styles["BodyText"],
    fontName="KaiwuSans",
    fontSize=10.8,
    leading=18.2,
    textColor=colors.HexColor("#1F2937"),
    alignment=TA_LEFT,
    spaceAfter=8,
    wordWrap="CJK",
)
small = ParagraphStyle(
    "Small",
    parent=body,
    fontSize=9.4,
    leading=14.5,
    textColor=colors.HexColor("#374151"),
)
toc = ParagraphStyle(
    "Toc",
    parent=body,
    fontSize=12.8,
    leading=23,
    textColor=colors.HexColor("#4F7EE8"),
    leftIndent=4,
)
code = ParagraphStyle(
    "Code",
    parent=styles["Code"],
    fontName="KaiwuMono",
    fontSize=8.8,
    leading=13,
    backColor=colors.HexColor("#F3F4F6"),
    borderPadding=(7, 8, 7, 8),
    textColor=colors.HexColor("#111827"),
    wordWrap="LTR",
)


def p(text, style=body):
    return Paragraph(esc(text), style)


def section(num, name):
    return [Divider(), Paragraph(f"{num}. {esc(name)}", h1)]


def bullets(items):
    flow = []
    for item in items:
        flow.append(p(f"· {item}"))
    return flow


def codeblock(text):
    return Paragraph("<br/>".join(esc(line) for line in text.splitlines()), code)


def make_table(rows, widths):
    table_rows = []
    for row in rows:
        table_rows.append([Paragraph(esc(cell), small) for cell in row])
    table = LongTable(table_rows, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2F7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("FONTNAME", (0, 0), (-1, -1), "KaiwuSans"),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#D8DEE8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


story = []
story.append(Spacer(1, 38 * mm))
story.append(Paragraph("Kaiwu · 使用说明书", title))
story.append(Paragraph("曜势科技 · 2026-07-10", subtitle))
story.append(
    Callout(
        [
            "版本：v1.0（OPC 创业工作台版） ｜ 更新日期：2026-07-10 ｜ 适用对象：OPC 创业者、创业团队、项目运营者",
            "一句话：一个把“想法诊断、市场调研、商业方案、产品设计、内容营销、项目归档”串起来的 AI 创业工作台。",
        ],
        body,
    )
)
story.append(Spacer(1, 18))
story.append(Divider())
for i, name in enumerate(
    [
        "这是什么",
        "如何打开",
        "界面导览",
        "主对话：从想法到项目资料怎么用",
        "创造模式：AI 生图 / AI 视频 / AI 编程",
        "技能库与项目库",
        "典型工作流：一个创业项目这样推进",
        "设置与管理",
        "常见问题 FAQ",
    ],
    1,
):
    story.append(Paragraph(f"{i}. {esc(name)}", toc))
story.append(Spacer(1, 12))

story.extend(section(1, "这是什么"))
story.append(
    p(
        "Kaiwu 是曜势科技面向 OPC 创业者的 AI 创业智能体。它不是单次问答工具，而是一条从模糊想法到可执行资料的创业工作流。"
    )
)
story.append(
    p(
        "它会先通过对话理解你的背景、资源、预算、动机和限制，再逐步生成市场调研、商业方案、产品落地手册、营销方案和自媒体内容。过程中产生的报告、图片和文件会沉淀到项目库，方便后续继续迭代。"
    )
)
story.extend(
    bullets(
        [
            "需求洞察：用户诊断、市场调研、竞品分析、机会点判断。",
            "商业方案：商业模式、品牌定位、品牌故事、收入与成本结构。",
            "产品创造：首批 SKU、定价、成本、MVP 启动方案、AI 生图。",
            "营销推广：内容营销框架、小红书/抖音/B 站/私域文案、发布节奏。",
            "项目沉淀：AI 对话产出、图片库、创业资料、产品设计、营销素材集中管理。",
        ]
    )
)

story.extend(section(2, "如何打开"))
story.append(Paragraph("方式一：本地开发启动（推荐）", h2))
story.append(p("Kaiwu 当前项目是前后端分离结构，需要先启动后端，再启动前端。"))
story.append(
    codeblock(
        'cd "/Users/wangzijian/Desktop/kaiwu_All_v3.4 /kaiwu_All/kaiwuback"\npython main.py'
    )
)
story.append(Spacer(1, 6))
story.append(
    codeblock(
        'cd "/Users/wangzijian/Desktop/kaiwu_All_v3.4 /kaiwu_All/kaiwu"\nnpm install\nnpm run dev'
    )
)
story.append(
    p(
        "启动后，浏览器访问终端显示的前端地址即可使用。常见地址是 http://localhost:5173；如果你已经用本地封装服务运行，也可能是 http://localhost:8080。后端默认地址是 http://localhost:5001。"
    )
)
story.append(
    Callout(
        [
            "首次启动前端会安装依赖，时间稍长；之后启动会快很多。",
            "关闭方式：分别在前端和后端终端窗口按 Ctrl + C。",
        ],
        small,
    )
)
story.append(Paragraph("方式二：只检查后端是否正常", h2))
story.append(p("后端启动后访问健康检查地址：http://localhost:5001/api/health。看到 status 为 ok，说明服务已启动。"))

story.append(
    KeepTogether(
        [
            *section(3, "界面导览"),
            Callout(
                [
                    "Kaiwu 主要是三栏工作台：左边选入口，中间做任务，底部输入你的需求。",
                ],
                body,
                fill="#F8FAFC",
                accent="#7AA2E8",
            ),
            make_table(
                [
                    ["区域", "你会看到什么", "主要用途"],
                    ["左侧栏", "新对话、创造模式、技能库、项目库、历史对话、账户与设置。", "切换入口，找回历史，管理项目资料。"],
                    ["中间主舞台", "首页输入创业想法；生成中显示节点进度；项目库和技能库显示列表与详情。", "完成诊断、调研、方案生成和资料整理。"],
                    ["底部输入区", "选择模型、参考历史文件、上传文件、发送消息。AI 生图模式下显示图片模型、比例、分辨率和数量。", "输入需求，补充材料，发起下一步任务。"],
                ],
                [25 * mm, 73 * mm, 65 * mm],
            ),
        ]
    )
)

story.extend(section(4, "主对话：从想法到项目资料怎么用"))
story.append(
    p(
        "主对话是 Kaiwu 的核心入口。你可以直接说“我想做一个宠物银饰品牌”“我想进入咖啡行业”“我有一个 B2B 房产中介想法”，系统会自动识别当前应该进入哪个节点。"
    )
)
node_rows = [
    ["阶段", "名称", "它会做什么"],
    ["node0", "用户诊断", "先问清楚创始人背景、资源、预算、动机和约束，避免后续方案脱离现实。"],
    ["node1", "市场调研", "联网搜索行业数据，分析市场规模、趋势、竞品、用户画像和机会点。"],
    ["node1.5", "品牌设计", "提炼核心人群精神，输出品牌屋、命名方向、Logo/品牌故事/产品调性提示词。"],
    ["node2", "商业方案设计", "生成商业模式、品牌定位、产品线、定价逻辑和执行路径。"],
    ["node3", "产品设计", "确定首批 SKU、成本、定价、启动资金和最小验证方案。"],
    ["node4", "营销方案设计", "设计内容营销框架、渠道矩阵、5A 漏斗和 3 个月节奏。"],
    ["node5", "自媒体文案", "生成小红书、抖音、B 站、私域、海报等具体内容。"],
]
story.append(make_table(node_rows, [23 * mm, 35 * mm, 105 * mm]))
story.append(Spacer(1, 8))
story.append(Paragraph("发送与追问", h2))
story.append(p("直接在底部输入需求，按 Enter 发送；需要换行时使用 Shift + Enter。每个阶段完成后，底部会出现建议追问，例如“开始生成商业方案”“开始产品设计”。"))
story.append(Paragraph("导出与保存", h2))
story.append(p("市场调研、商业方案、产品手册、营销方案、自媒体文案完成后，会出现导出按钮。点击导出后，系统会生成报告文件，并归档到项目库和 AI 对话产出。"))

story.extend(section(5, "创造模式：AI 生图 / AI 视频 / AI 编程"))
story.append(
    make_table(
        [
            ["模式", "适合做什么", "使用要点"],
            ["AI 生图", "Logo、产品概念图、海报视觉、品牌氛围图。", "可选模型、比例、分辨率和数量，支持上传参考图。"],
            ["AI 视频", "品牌宣传视频素材、短视频画面草稿、镜头运动描述。", "把画面主体、风格、镜头、时长和节奏说清楚。"],
            ["AI 编程", "页面原型、简单工具、前端代码草稿。", "包含代码视图、预览视图和 AI 编程助手区域，适合快速验证想法。"],
        ],
        [27 * mm, 67 * mm, 69 * mm],
    )
)
story.append(Spacer(1, 8))
story.append(
    p(
        "普通对话按钮和 AI 生图按钮是不同入口：需要生成图片时进入创造模式里的 AI 生图；AI 视频、AI 编程沿用普通对话式输入，但工作台会切换到对应能力。"
    )
)

story.extend(section(6, "技能库与项目库"))
story.append(Paragraph("技能库", h2))
story.append(p("技能库是 Kaiwu 的工具能力中心，分“技能市场”和“已安装”。你可以搜索技能、按分类筛选、查看详情、安装技能，或点击“去使用”把技能带回对话输入区。"))
story.append(Paragraph("项目库", h2))
story.append(p("项目库用于集中管理 AI 生成文件和你上传的项目资料。支持新建文件夹、上传文件、搜索、查看详情、预览、下载、重命名和删除。"))
story.append(
    make_table(
        [
            ["文件夹", "常见内容"],
            ["AI 对话产出", "市场调研、商业方案、产品手册、营销方案、自媒体文案等导出文件。"],
            ["图片库", "AI 生图结果、产品概念图、Logo、海报图。"],
            ["视频库", "AI 视频相关素材或生成结果。"],
            ["编程文件库", "AI 编程生成的代码、页面原型、工具文件。"],
            ["创业资料 / 产品设计 / 营销素材", "项目运营过程中沉淀的资料包、方案和素材。"],
        ],
        [45 * mm, 118 * mm],
    )
)

story.extend(section(7, "典型工作流：一个创业项目这样推进"))
for item in [
    "把想法说清楚：输入行业、动机、资源、预算。",
    "完成用户诊断：补充背景，让后续方案更贴近真实情况。",
    "生成市场调研：看市场、竞品、用户和机会点。",
    "生成商业方案与产品设计：确定定位、商业模式、SKU、成本和启动方案。",
    "做营销方案和文案：输出渠道策略、内容节奏和具体平台文案。",
    "沉淀到项目库：把报告、图片和文案整理成项目资料包。",
]:
    story.append(p(item))

story.extend(section(8, "设置与管理"))
story.append(
    p(
        "设置包含账户管理、系统设置、智能体设置、记忆、模型、软件配置、帮助与反馈。API Key 和数据库信息不在前端页面里硬编码，本地开发时主要配置 kaiwuback/.env 和 kaiwu/.env.local 或 kaiwu/.env.example 中的 VITE_API_BASE_URL。"
    )
)
story.append(
    Callout(
        [
            "安全提醒：API Key、Token、密码不要写入源码，也不要放进对话截图或公开文档。",
            "如果 AI 没有回复，优先检查后端是否启动、模型配置是否正确、网络和 API Key 是否可用。",
        ],
        small,
    )
)

story.extend(section(9, "常见问题 FAQ"))
faq = [
    ("Q：页面打不开？", "A：先确认前端 dev server 是否还在运行；如果终端已关闭，重新执行 npm run dev。"),
    ("Q：页面打开了，但 AI 没有回复？", "A：检查后端是否运行在 http://localhost:5001，再检查 kaiwuback/.env 里的 API Key 是否填写。"),
    ("Q：生成的报告在哪里？", "A：导出的报告会进入项目库，通常也会归档到“AI 对话产出”文件夹。"),
    ("Q：图片生成结果在哪里？", "A：生成图会显示在对话里，也会进入项目库的“图片库”。"),
    ("Q：如何开始一个新项目？", "A：点击左侧“新对话”，输入新的创业想法即可。"),
]
for q, a in faq:
    story.append(KeepTogether([Paragraph(esc(q), h2), p(a)]))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("KaiwuSans", 8)
    canvas.setFillColor(colors.HexColor("#A3A3A3"))
    canvas.drawCentredString(A4[0] / 2, 12 * mm, "Kaiwu 使用说明书")
    canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, str(doc.page))
    canvas.restoreState()


doc = SimpleDocTemplate(
    str(PDF_PATH),
    pagesize=A4,
    rightMargin=18 * mm,
    leftMargin=18 * mm,
    topMargin=20 * mm,
    bottomMargin=20 * mm,
    title="Kaiwu · 使用说明书",
    author="曜势科技",
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)

md = """# Kaiwu · 使用说明书

版本：v1.0（OPC 创业工作台版）
更新日期：2026-07-10
适用对象：OPC 创业者、创业团队、项目运营者

一句话：一个把“想法诊断、市场调研、商业方案、产品设计、内容营销、项目归档”串起来的 AI 创业工作台。

## 目录
1. 这是什么
2. 如何打开
3. 界面导览
4. 主对话：从想法到项目资料怎么用
5. 创造模式：AI 生图 / AI 视频 / AI 编程
6. 技能库与项目库
7. 典型工作流：一个创业项目这样推进
8. 设置与管理
9. 常见问题 FAQ

## 一、这是什么
Kaiwu 是曜势科技面向 OPC 创业者的 AI 创业智能体。它不是单次问答工具，而是一条从模糊想法到可执行资料的创业工作流。

它会先通过对话理解你的背景、资源、预算、动机和限制，再逐步生成市场调研、商业方案、产品落地手册、营销方案和自媒体内容。过程中产生的报告、图片和文件会沉淀到项目库，方便后续继续迭代。

- 需求洞察：用户诊断、市场调研、竞品分析、机会点判断。
- 商业方案：商业模式、品牌定位、品牌故事、收入与成本结构。
- 产品创造：首批 SKU、定价、成本、MVP 启动方案、AI 生图。
- 营销推广：内容营销框架、小红书/抖音/B 站/私域文案、发布节奏。
- 项目沉淀：AI 对话产出、图片库、创业资料、产品设计、营销素材集中管理。

## 二、如何打开
### 方式一：本地开发启动（推荐）
Kaiwu 当前项目是前后端分离结构，需要先启动后端，再启动前端。

```bash
cd "/Users/wangzijian/Desktop/kaiwu_All_v3.4 /kaiwu_All/kaiwuback"
python main.py
```

```bash
cd "/Users/wangzijian/Desktop/kaiwu_All_v3.4 /kaiwu_All/kaiwu"
npm install
npm run dev
```

启动后，浏览器访问终端显示的前端地址即可使用。常见地址是 `http://localhost:5173`；如果你已经用本地封装服务运行，也可能是 `http://localhost:8080`。后端默认地址是 `http://localhost:5001`。

首次启动前端会安装依赖，时间稍长；之后启动会快很多。关闭方式：分别在前端和后端终端窗口按 Ctrl + C。

### 方式二：只检查后端是否正常
后端启动后访问健康检查地址：`http://localhost:5001/api/health`。看到 status 为 ok，说明服务已启动。

## 三、界面导览
Kaiwu 主要是三栏工作台：左边选入口，中间做任务，底部输入你的需求。

| 区域 | 你会看到什么 | 主要用途 |
|---|---|---|
| 左侧栏 | 新对话、创造模式、技能库、项目库、历史对话、账户与设置。 | 切换入口，找回历史，管理项目资料。 |
| 中间主舞台 | 首页输入创业想法；生成中显示节点进度；项目库和技能库显示列表与详情。 | 完成诊断、调研、方案生成和资料整理。 |
| 底部输入区 | 选择模型、参考历史文件、上传文件、发送消息。AI 生图模式下显示图片模型、比例、分辨率和数量。 | 输入需求，补充材料，发起下一步任务。 |

## 四、主对话：从想法到项目资料怎么用
主对话是 Kaiwu 的核心入口。你可以直接说“我想做一个宠物银饰品牌”“我想进入咖啡行业”“我有一个 B2B 房产中介想法”，系统会自动识别当前应该进入哪个节点。

| 阶段 | 名称 | 它会做什么 |
|---|---|---|
| node0 | 用户诊断 | 先问清楚创始人背景、资源、预算、动机和约束，避免后续方案脱离现实。 |
| node1 | 市场调研 | 联网搜索行业数据，分析市场规模、趋势、竞品、用户画像和机会点。 |
| node1.5 | 品牌设计 | 提炼核心人群精神，输出品牌屋、命名方向、Logo/品牌故事/产品调性提示词。 |
| node2 | 商业方案设计 | 生成商业模式、品牌定位、产品线、定价逻辑和执行路径。 |
| node3 | 产品设计 | 确定首批 SKU、成本、定价、启动资金和最小验证方案。 |
| node4 | 营销方案设计 | 设计内容营销框架、渠道矩阵、5A 漏斗和 3 个月节奏。 |
| node5 | 自媒体文案 | 生成小红书、抖音、B 站、私域、海报等具体内容。 |

## 五、创造模式：AI 生图 / AI 视频 / AI 编程
- AI 生图：适合生成 Logo、产品概念图、海报视觉、品牌氛围图。可选模型、比例、分辨率和数量，支持上传参考图。
- AI 视频：用于描述视频画面、镜头运动和节奏，生成品牌宣传视频素材的草稿。
- AI 编程：用于把产品想法或页面需求转成代码原型，包含代码视图、预览视图和 AI 编程助手区域。

## 六、技能库与项目库
技能库是 Kaiwu 的工具能力中心，分“技能市场”和“已安装”。项目库用于集中管理 AI 生成文件和你上传的项目资料。

## 七、典型工作流：一个创业项目这样推进
1. 把想法说清楚：输入行业、动机、资源、预算。
2. 完成用户诊断：补充背景，让后续方案更贴近真实情况。
3. 生成市场调研：看市场、竞品、用户和机会点。
4. 生成商业方案与产品设计：确定定位、商业模式、SKU、成本和启动方案。
5. 做营销方案和文案：输出渠道策略、内容节奏和具体平台文案。
6. 沉淀到项目库：把报告、图片和文案整理成项目资料包。

## 八、设置与管理
设置包含账户管理、系统设置、智能体设置、记忆、模型、软件配置、帮助与反馈。API Key 和数据库信息不在前端页面里硬编码，本地开发时主要配置 `kaiwuback/.env` 和 `kaiwu/.env.local` 或 `kaiwu/.env.example` 中的 `VITE_API_BASE_URL`。

## 九、常见问题 FAQ
Q：页面打不开？
A：先确认前端 dev server 是否还在运行；如果终端已关闭，重新执行 `npm run dev`。

Q：页面打开了，但 AI 没有回复？
A：检查后端是否运行在 `http://localhost:5001`，再检查 `kaiwuback/.env` 里的 API Key 是否填写。

Q：生成的报告在哪里？
A：导出的报告会进入项目库，通常也会归档到“AI 对话产出”文件夹。

Q：图片生成结果在哪里？
A：生成图会显示在对话里，也会进入项目库的“图片库”。

Q：如何开始一个新项目？
A：点击左侧“新对话”，输入新的创业想法即可。
"""

MD_PATH.write_text(md, encoding="utf-8")
