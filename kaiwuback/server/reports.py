"""报告生成模块"""
import json, re, threading, uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime
from server.llm_client import call_deepseek, call_llm
from server.config import PROJECT_LIB, REPORT_TEMPLATES_DIR, DATA_INTEGRITY
from server.intent.recognizer import get_uploaded_files_text
from server.utils.handbook_renderer import render_handbook_to_html
from server.utils.markdown import markdown_to_html


def _is_number_sequence(text):
    """检测文本是否为逗号分隔的数字序列，如 '9,9,8,7,8,9,9,8'"""
    text = text.strip()
    if not text or len(text) < 3:
        return False
    parts = [p.strip() for p in text.split(',')]
    if len(parts) < 3:
        return False
    for p in parts:
        try:
            float(p)
        except ValueError:
            return False
    return True


def _parse_chart_value(s):
    """从图表数据字符串中提取数值，兼容 '85%' '1200万' '9.5亿' '7/10分' 等格式"""
    s = s.strip().replace(',','').replace('%','').replace('亿','').replace('万','').replace('元','').replace('分','').replace('/10','').replace('分制','')
    try:
        return float(s)
    except ValueError:
        pass
    m = re.search(r'[\d.]+', s)
    if m:
        try:
            return float(m.group())
        except ValueError:
            pass
    return 0


# REPORT_TEMPLATES_DIR imported from config above

NODE_REPORT_MAP = [
    # (node_ids, template_file, report_title)
    ({"node4"}, "品牌商业计划书.html", "系统化内容营销解决方案"),
    ({"node3", "node3.1"}, "产品落地执行手册.html", "产品落地执行手册"),
    ({"node2"}, "品牌商业计划书.html", "品牌商业计划书"),
    ({"node1"}, "杂志风报告模板.html", "深度商业调研报告"),
]


def detect_nodes_from_history(history: list) -> set:
    """从对话历史中推断涉及哪些node。通过分析意图识别结果。
    由于历史消息不包含node标记，使用关键词匹配推断。"""
    nodes = set()
    all_text = " ".join([m.get("content", "")[:800] for m in history])
    # Node1: 调研/市场/行业/竞品
    if any(kw in all_text for kw in ["调研", "市场", "行业", "竞品", "洞察", "TAM", "需求"]):
        nodes.add("node1")
    # Node1.5: 品牌精神/品牌屋/Slogan/品牌故事
    if any(kw in all_text for kw in ["品牌精神", "品牌屋", "品牌策略", "品牌全案", "Slogan", "品牌故事", "品牌文化"]):
        nodes.add("node1.5")
    # Node2: 商业方案/商业底层/定位/产品矩阵
    if any(kw in all_text for kw in ["商业方案", "商业底层", "商业计划", "赛道定位", "产品矩阵", "盈利模式"]):
        nodes.add("node2")
    # Node3: 产品设计（产品落地手册/SKU/成本核算/启动方案等）
    if any(kw in all_text for kw in ["产品定位", "SKU", "产品落地手册", "成本核算", "产品规划", "启动方案", "验证周期", "获客方案", "定价策略", "利润空间"]):
        nodes.add("node3")
    # Node3.1: 生成图片
    if any(kw in all_text for kw in ["生成图片", "生成一张", "画一张", "文生图"]):
        nodes.add("node3.1")
    # Node4: PPT
    if any(kw in all_text for kw in ["PPT", "大纲", "幻灯片"]):
        nodes.add("node4")
    return nodes


def select_report_template(history: list) -> tuple:
    """根据对话历史涉及的node，选择报告模板。返回(template_path, report_title)"""
    nodes = detect_nodes_from_history(history)
    print(f"[REPORT] Detected nodes: {nodes}", flush=True)
    for node_set, template_file, title in NODE_REPORT_MAP:
        if node_set & nodes:
            template_path = REPORT_TEMPLATES_DIR / template_file
            if template_path.exists():
                return str(template_path), title
    # 默认：深度商业调研报告
    return str(REPORT_TEMPLATES_DIR / "千瓜风格报告.html"), "深度商业调研报告"


def generate_summary_report(message, history, model=None):
    """简化版报告生成：发送全部上下文→LLM生成结构化markdown→解析为slides"""
    # 根据用户请求判定报告类型
    # 所有报告统一使用规范模板
    lower_msg = message.lower()
    if any(kw in lower_msg for kw in ["品牌手册"]):
        report_title = "品牌手册"
    elif any(kw in lower_msg for kw in ["产品手册", "产品落地"]):
        report_title = "产品落地执行手册"
    elif any(kw in lower_msg for kw in ["营销解决方案", "营销手册"]):
        report_title = "系统化内容营销解决方案"
    elif any(kw in lower_msg for kw in ["商业计划书"]):
        report_title = "品牌商业计划书"
    elif any(kw in lower_msg for kw in ["调研报告", "调研", "报告"]):
        report_title = "深度商业调研报告"
    else:
        _, report_title = select_report_template(history)
    template_file = "规范调研报告模板.html"
    template_path = REPORT_TEMPLATES_DIR / template_file
    tf = Path(template_path)
    if not tf.exists():
        return {"error": "template not found"}
    template_html = tf.read_text(encoding="utf-8")

    # 发送对话历史（截断提速）
    conv_text = ""
    for m in history[-15:]:
        role = "用户" if m.get("role") == "user" else "AI"
        conv_text += "【" + role + "】\n" + (m.get("content","")[:1000]) + "\n\n"

    # 注入已上传文件内容
    file_context = get_uploaded_files_text()
    if file_context:
        conv_text = file_context + "\n\n---\n## 对话内容\n" + conv_text

    # 根据报告类型选择不同prompt
    if "产品落地" in report_title or "产品手册" in report_title:
        prompt = f"""## 对话上下文（必须优先使用其中数据）
{conv_text}

## ⚠️ 核心规则（违反将导致报告作废）
1. 对话中已有的行业信息、产品数据、品牌名、定位**必须原样照搬**，禁止修改替换
2. 对话中不存在的补充内容可合理拓展，但**不能改写对话已确认的核心事实**
3. 所有数据、观点与对话上下文100%对齐

## 数据补全原则
- ✅ 对话有数据 → 直接引用，标注「对话原文」
- ⚠️ 对话有推论 → 合理推导，标注「行业测算，可人工复核」
- ❌ 对话无提及 → **必须**用行业常识补全具体数据，标注「基于行业公开数据推算」
- **绝对禁止留空章节，每一节都必须有实际内容，不能只写标题**
- **⚠️ 每章必须输出指定数量的小节（用###标记），每小节≥150字实际内容。禁止将多个小节合并、禁止跳过任何小节、禁止以一段话概括代替整个小节。**

### ⚠️ 图表格式（严格按此格式，禁止用其他方式表示图表）
BAR: 标签1|数值1, 标签2|数值2
HBAR: 标签1|数值1, 标签2|数值2
PIE: 标签1|百分比1, 标签2|百分比2
禁止用代码块、ASCII图或中文描述代替。

## 报告结构（六大章节，每章2-3小节，总计15-25页，章节缺一不可）

### ## 一、产品定位与概览（3-4页）
必须包含以下3个小节（每个用 ### 标记，禁止省略）：
- 产品定位：一句话定位+目标市场+核心差异化，必须用表格，≥150字
- 产品架构：产品线分层（引流款/利润款/形象款），用PIE图表呈现各层占比，≥150字
- 核心功能列表：3-5个核心功能+优先级+开发难度，必须用表格，≥150字

### ## 二、SKU规划与详情（4-6页）
必须包含以下3个小节（每个用 ### 标记，禁止省略）：
- 首批SKU清单：品名/规格/成本/定价/目标毛利率，必须用表格，≥150字
- 产品规格明细：材质/尺寸/工艺/包装，必须用表格，≥150字
- 定价策略：成本加成+竞品锚定+感知价值定价，用BAR图表对比竞品价格带，≥150字

### ## 三、供应链与生产（3-4页）
必须包含以下3个小节（每个用 ### 标记，禁止省略）：
- 供应商选择标准：资质/产能/交期/价格，必须用表格对比，≥150字
- 生产成本拆解：原料/加工/包装/物流占比，用PIE图表，≥150字
- 品控标准：关键质检节点+验收标准，必须用表格，≥150字

### ## 四、上市计划与路径（3-4页）
必须包含以下3个小节（每个用 ### 标记，禁止省略）：
- 4周启动路径：每周关键任务+里程碑+负责人，必须用表格，≥150字
- 渠道上线计划：线上/线下渠道+上线时间+预期销量，用HBAR图表，≥150字
- 首批备货计划：SKU/数量/库存周转天数，必须用表格，≥150字

### ## 五、验证指标与迭代（2-3页）
必须包含以下3个小节（每个用 ### 标记，禁止省略）：
- 核心验证指标：CTR/转化率/复购率/NPS目标，必须用表格，≥150字
- 用户反馈机制：评价监控+用户访谈+数据埋点方案，≥150字
- 迭代路径：V1.0→V1.1→V2.0 版本规划+升级标准，用BAR图表，≥150字

### ## 六、团队与资源（2-3页）
必须包含以下3个小节（每个用 ### 标记，禁止省略）：
- 团队配置：角色/人数/核心能力/到位时间，必须用表格，≥150字
- 预算总览：研发/生产/营销/运营占比，用PIE图表，≥150字
- 关键风险与应对：风险清单+影响评级+预案，必须用表格，≥150字

**⚠️ 所有章节和小节输出完成后，必须写一行结语（回扣产品核心价值，30-50字），然后立即输出以下终止标识，标识之后禁止再生成任何内容：**
以上为产品落地执行手册完整输出，六大章节+18小节已全部呈现。

输出："""
    elif "营销" in report_title:
        prompt = f"""## 对话上下文（必须优先使用其中数据）
{conv_text}

## ⚠️ 核心规则（违反将导致报告作废）
1. 对话中已有的行业信息、品牌名、数据、定位**必须原样照搬**，禁止修改替换
2. 对话中不存在的补充内容可合理拓展，但**不能改写对话已确认的核心事实**
3. 所有数据、观点与对话上下文100%对齐

## 数据补全原则
- ✅ 对话有数据 → 直接引用，标注「对话原文」
- ⚠️ 对话有推论 → 合理推导，标注「行业测算，可人工复核」
- ❌ 对话无提及 → **必须**用行业常识补全具体数据，标注「基于行业公开数据推算」
- **绝对禁止留空章节，每一节都必须有实际内容，不能只写标题**
- **⚠️ 每章必须输出指定数量的小节（用###标记），每小节≥150字实际内容。禁止将多个小节合并、禁止跳过任何小节、禁止以一段话概括代替整个小节。第四章种草文案必须包含3个完整示例。**

### ⚠️ 图表格式（严格按此格式，禁止用其他方式表示图表）
BAR: 标签1|数值1, 标签2|数值2
HBAR: 标签1|数值1, 标签2|数值2
PIE: 标签1|百分比1, 标签2|百分比2
禁止用代码块、ASCII图或中文描述代替。

## 报告结构（六大章节，每章2-3小节，总计30-40页，章节缺一不可）

### ## 一、内容营销策略总览（5-6页）
必须包含以下3个小节（每个用 ### 标记，禁止省略）：
- 营销目标与KPI体系：品牌/转化/留存三维目标，必须用表格，≥150字
- 内容矩阵规划：图文/短视频/直播/长文四类内容占比，用PIE图表，≥150字
- 预算分配方案：渠道/内容类型/时间三个维度，用HBAR图表，≥150字

### ## 二、平台运营策略（6-8页）
必须包含以下3个小节（每个用 ### 标记，禁止省略）：
- 小红书运营方案：账号定位/内容日历/爆款公式/互动策略，必须用表格，≥150字
- 抖音运营方案：短视频矩阵/直播排期/投流策略/热门话题，必须用表格，≥150字
- 私域运营方案：社群SOP/朋友圈剧本/一对一话术/裂变机制，必须用表格，≥150字

### ## 三、内容生产与分发（5-7页）
必须包含以下3个小节（每个用 ### 标记，禁止省略）：
- 内容生产SOP：选题→撰稿→审核→发布全流程，必须用表格，≥150字
- 内容日历：月度选题规划+热点日历+重要节点，必须用表格，≥150字
- 分发矩阵：各平台发布时间/频次/优化策略，用BAR图表，≥150字

### ## 四、种草文案与脚本（6-8页）
必须包含以下3个小节（每个用 ### 标记，禁止省略，禁止以概括代替实际内容）：
- 小红书种草文案模板：标题公式/正文结构/标签策略/图片规范，**必须附3个完整示例**，≥200字
- 抖音短视频脚本模板：黄金3秒/信息点/CTA，**必须附3个完整脚本示例**，≥200字
- 产品详情页文案框架：卖点提炼/信任背书/转化钩子，必须用表格，≥150字

### ## 五、营销数据分析（4-6页）
必须包含以下3个小节（每个用 ### 标记，禁止省略）：
- 核心数据看板：曝光/点击/转化/ROI，必须用表格，≥150字
- 内容效果评估：爆款率/互动率/转化率/粉丝增长，用BAR图表，≥150字
- A/B测试方案：变量/样本量/评估标准，必须用表格，≥150字

### ## 六、执行计划与排期（4-5页）
必须包含以下3个小节（每个用 ### 标记，禁止省略）：
- 季度执行路线图：Q1-Q4关键战役+资源需求，必须用表格，≥150字
- 团队配置与分工：角色/人数/职责/KPI，必须用表格，≥150字
- 预算与ROI预估：总预算/分项预算/预期ROI，用PIE图表，≥150字

**⚠️ 所有章节和小节输出完成后，必须写一行结语（回扣品牌核心价值，30-50字），然后立即输出以下终止标识，标识之后禁止再生成任何内容：**
以上为系统化内容营销解决方案完整输出，六大章节+18小节已全部呈现。

输出："""
    elif "品牌手册" in report_title or "商业计划书" in report_title:
        prompt = f"""## 对话上下文（必须优先使用其中数据）
{conv_text}

## ⚠️ 核心规则（违反将导致报告作废）
1. 对话中已有的行业信息、品牌名、数据、定位、用户画像**必须原样照搬**，禁止修改替换
2. 对话中不存在的补充内容可合理拓展，但**不能改写对话已确认的核心事实**
3. 所有数据、观点与对话上下文100%对齐

## 数据补全原则
- ✅ 对话有数据 → 直接引用，标注「对话原文」
- ⚠️ 对话有推论 → 合理推导，标注「行业测算，可人工复核」
- ❌ 对话无提及 → **必须**用行业常识补全具体数据，标注「基于行业公开数据推算」
- **绝对禁止留空章节，每一节都必须有实际内容，不能只写标题**
- **⚠️ 每章必须输出指定数量的小节（用###标记），每小节≥150字实际内容。禁止将多个小节合并、禁止跳过任何小节。第二章品牌体系的6个小节缺一不可，尤其是视觉风格建议必须输出≥6行完整表格。**

### ⚠️ 图表格式（严格按此格式，禁止用其他方式表示图表）
每当你需要插入图表时，必须单独一行，严格使用以下格式之一：
BAR: 标签1|数值1, 标签2|数值2, 标签3|数值3
HBAR: 标签1|数值1, 标签2|数值2, 标签3|数值3
PIE: 标签1|百分比1, 标签2|百分比2, 标签3|百分比3
禁止使用代码块、ASCII图、中文描述替代图表。

## 报告结构（三章，每章多个小节，缺一不可，总计25-30页）

### ⛔ 章节结构强制规则
输出时必须严格使用以下二级标题作为章节分隔，**三个 ## 标题缺一不可，禁止合并或跳过**：
```
## 一、商业模式
（内容...）
## 二、品牌体系
（内容...）
## 三、方案总结与下一步建议
（内容...）
```
**篇幅分配**：全文总量27-33页。第一章保持10-12页，第二章保持12-15页，第三章占2-3页。**第三章是额外增量，不得通过压缩前两章篇幅来挤出空间。**

### ## 一、商业模式（10-12页）
必须包含以下6个小节（每个用 ### 标记，禁止省略）：
- 核心价值主张：一句话定位+价值曲线图，用BAR图表，≥150字
- 目标用户画像：人群分层/年龄/城市/收入/消费场景，必须用表格，≥150字
- 盈利模式：收入结构/毛利率，用HBAR图表，≥150字
- 定价策略：产品线定价带+与竞品对比，必须用表格，≥150字
- 渠道策略：线上/线下渠道分布+贡献占比，用PIE图表，≥150字
- 成本结构与盈亏平衡分析：固定/变动成本拆解（必须用表格）+ 时间线/关键里程碑/盈亏平衡月度计算，用BAR图表，≥200字

### ## 二、品牌体系（12-15页）
**⛔ 必须以上方指定的 `## 二、品牌体系` 作为独立章节标题开始，不可省略。**
必须包含以下6个小节（每个用 ### 标记，禁止省略任何小节）：
- 品牌命名方案：**必须**提供3个品牌名方案（无论对话是否有），格式为4列表格：方案名称 | 品牌含义 | 目标人群 | 适用场景，每行一个完整方案，禁止只写文字说明不写表格，≥200字
- 品牌理念与价值观：核心理念+3条价值观+行为准则，≥150字
- 品牌差异化定位：与竞品的3个差异维度，用HBAR图表，≥150字
- 品牌愿景：3年/5年目标+品牌人格描述，≥150字
- 品牌故事：创始故事+用户故事+产品故事，3段各100-200字，≥300字
- **⚠️ 视觉风格建议（严禁跳过）**：主色调/辅助色/强调色/字体选择/Logo风格/应用场景，**必须用≥6行表格呈现，每行完整填充具体色值（如#2C3E50）或具体字体名（如思源黑体），禁止以任何理由跳过或留空**，≥200字

### ## 三、方案总结与下一步建议（2-3页）
**⛔ 必须作为独立章节，以上方指定的 `## 三、方案总结与下一步建议` 作为章节标题开始。**

**报告核心结论回顾**：用一段80-120字的文字收束全文。必须回扣报告中已提到的品牌名、核心产品定位和关键财务结论。

**关键决策汇总表**（必须输出）：
| 决策项 | 报告结论 | 依据 |
|--------|---------|------|
| 品牌名 | 报告中推荐的首选方案 | 为什么 |
| 核心产品/服务 | 报告中的核心产品定位 | 为什么 |
| 首发渠道 | 报告中的首选渠道 | 为什么 |
| 盈亏平衡 | 第X个月 | 关键条件 |
| 启动资金 | 金额 | 用途说明 |

**近期行动建议**：基于报告分析，列出3条建议优先执行的行动，每条一句话。

**结语**：用一段60-100字的收束文字结束全报告。回扣品牌故事或品牌理念中一句核心的话，语调平稳、有分量。

**结语之后，必须立即输出以下终止标识，标识之后禁止再生成任何内容：**
以上为品牌商业计划书完整输出，商业模式+品牌体系+方案总结三大章节已全部呈现。

输出："""
    else:
        prompt = f"""## ⛔ 第一步：从对话中识别赛道（必须先行）
在输出任何内容之前，从对话上下文中提取核心行业/赛道是什么。要求：
- 以对话中用户反复讨论、投入最大篇幅的行业为准
- 不要把对话中作为举例、类比、渠道提及的行业误判为主赛道（如对话聊宠物饰品时提到"宠物友好咖啡厅"作为渠道，赛道是宠物饰品，不是咖啡）
- 识别后用一句话锁定：**"本报告聚焦赛道：[从对话中提取的具体行业名称]"**

## 对话上下文（必须优先使用其中数据）
{conv_text}

## ⚠️ 核心规则（违反将导致报告作废）
1. 对话中已有的行业信息、品牌名、数据、定位、用户画像**必须原样照搬**，禁止修改替换
2. 对话中不存在的补充内容可合理拓展，但**不能改写对话已确认的核心事实**
3. 所有数据、观点与对话上下文100%对齐
4. **报告的行业/赛道必须与第一步锁定的赛道完全一致，禁止替换为其他行业**

## 数据补全原则
- ✅ 对话有数据 → 直接引用，标注「对话原文」
- ⚠️ 对话有推论 → 合理推导，标注「行业测算，可人工复核」
- ❌ 对话无提及 → **必须**用行业常识补全具体数据，标注「基于行业公开数据推算」
- **绝对禁止留空章节，每一节都必须有实际内容，不能只写标题**
- **⚠️ 每章必须输出2-3个小节（用###标记），每小节≥150字实际内容。禁止将多个小节合并、禁止跳过任何小节。四个章节缺一不可。**

### 图表格式（每个章节至少1个图表/表格）
BAR: 标签|数值, 标签|数值
PIE: 标签|百分比, 标签|百分比
HBAR: 标签|数值, 标签|数值

### ⛔ 章节结构强制规则
输出时必须严格使用以下二级标题作为章节分隔，**四个 ## 标题缺一不可，禁止合并或跳过**：
```
## 一、行业发展概述
（内容...）
## 二、消费者洞察
（内容...）
## 三、案例分析
（内容...）
## 四、未来展望
（内容...）
```
**篇幅分配**：全文总量20-28页。每章约5-7页，各章篇幅均衡分配。

### ## 一、行业发展概述（5-7页）
**⛔ 必须以上方指定的 `## 一、行业发展概述` 作为独立章节标题开始，不可省略。**
必须包含以下3个小节（每个用 ### 标记，禁止省略）：
- 行业定义与范畴：界定行业边界与细分赛道，必须用表格，≥150字
- 市场规模与增速：近3年数据+未来预测，必须用表格+BAR图表，≥200字
- 产业链与竞争格局：上下游拆解+主要玩家对比，必须用HBAR图表，≥150字

### ## 二、消费者洞察（5-7页）
**⛔ 必须以上方指定的 `## 二、消费者洞察` 作为独立章节标题开始，不可省略。**
必须包含以下3个小节（每个用 ### 标记，禁止省略）：
- 目标用户画像：年龄/性别/城市/收入/消费习惯，必须用表格，≥150字
- 消费行为与偏好：购买频率、渠道偏好、价格敏感度，必须用表格，≥150字
- 需求痛点与未满足场景：用户原声引用+痛点矩阵，必须用表格，≥150字

### ## 三、案例分析（5-7页）
**⛔ 必须以上方指定的 `## 三、案例分析` 作为独立章节标题开始，不可省略。**
必须包含以下3个小节（每个用 ### 标记，禁止省略）：
- 成功品牌案例分析：至少2个品牌的商业模式/增长路径，必须用表格对比，≥150字
- 创新产品与模式拆解：产品创新点+市场反馈，必须用表格，≥150字
- 行业最佳实践与启示：提炼可复用的方法论，≥150字

### ## 四、未来展望（5-7页）
**⛔ 必须以上方指定的 `## 四、未来展望` 作为独立章节标题开始，不可省略。**
必须包含以下3个小节（每个用 ### 标记，禁止省略）：
- 行业趋势预判：技术/政策/消费三方面，用PIE图表呈现影响因素权重，≥150字
- 增长机会与潜力赛道：细分机会点+市场规模预估，必须用表格，≥150字
- 进入策略与风险建议：时间线+风险评估+应对方案，≥150字

**⛔ 四章十二小节全部输出完成后，必须写一段60-100字的结语（回扣行业核心发现，给出一句关键判断），然后立即输出以下收尾行，收尾行之后禁止再生成任何内容：**
以上为本次深度调研报告的全部内容，四大章节+十二小节+结语已全部呈现。数据基于对话上下文及行业公开信息综合得出，标注[行业测算]部分建议人工复核后使用。

输出："""

    # ── 方案B：产品手册/营销方案不调LLM，直接从对话历史提取内容 → 模板渲染 ──
    is_handbook = "产品落地" in report_title or "产品手册" in report_title or "营销" in report_title
    if is_handbook:
        # 提取对话历史中最近3条AI消息，拼成Markdown
        ai_msgs = [m["content"] for m in history if m.get("role") == "ai" and m.get("content")]
        handbook_md = "\n\n".join(ai_msgs[-3:]) if ai_msgs else ""
        if len(handbook_md) < 100:
            return {"error": "对话内容不足，无法生成手册。请先完成产品设计/营销方案节点。"}

        html_content = render_handbook_to_html(handbook_md, report_title, "")
        file_id = uuid.uuid4().hex[:6]
        file_path = PROJECT_LIB / "编程文件库" / f"{report_title}_{file_id}.html"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(html_content, encoding='utf-8')
        print(f"[HANDBOOK] Template-rendered {len(html_content)} chars, no LLM call", flush=True)
        return {"report_title": report_title, "file_path": str(file_path), "method": "template"}

    # 其他报告类型保持原有LLM流程
    max_tok, timeout_sec = 40000, 300
    try:
        report_md = call_deepseek(
            "你是专业报告撰写专家。核心规则：1) 对话中已有的数据、品牌名、数字、定位必须原样照搬，不得修改或替换 2) 仅对话缺失的数据才用行业常识补全并标注来源 3) 直接输出Markdown正文，禁止开场白客套话。",
            prompt, timeout=timeout_sec, max_tokens=max_tok, model=model
        )
        print(f"[REPORT] Generated {len(report_md)} chars", flush=True)
    except Exception as e:
        return {"error": "LLM call failed: " + str(e)[:200]}

    if not report_md or len(report_md) < 100:
        return {"error": "Report too short or empty"}

    # 解析markdown为slides
    lines = report_md.strip().split('\n')

    import re as _re_clean
    # 提取标题 - 跳过LLM开场白
    cover_title = report_title
    cover_sub = ""
    skip_prefixes = ["好的", "根据您", "基于您", "我们", "以下", "首先", "让我"]
    for line in lines[:15]:
        s = line.strip()
        # Skip conversational preamble
        if any(s.startswith(p) for p in skip_prefixes):
            continue
        if s.startswith('# ') and not cover_title:
            t = _re_clean.sub(r'\*\*|__|副标题[:：]\s*|标题[:：]\s*', '', s[2:].strip())[:80]
            if t and len(t) > 2:
                cover_title = t
        elif s.startswith('## ') and not cover_sub:
            t = _re_clean.sub(r'\*\*|__|副标题[:：]\s*', '', s[3:].strip())[:80]
            if t:
                cover_sub = t

    if not cover_title or cover_title == report_title:
        for line in lines:
            s = line.strip()
            s_clean = _re_clean.sub(r'\*\*|__|#', '', s).strip()
            if s_clean and len(s_clean) > 5 and not s_clean.startswith('|') and not s_clean.startswith('-') and '副标题' not in s_clean:
                cover_title = s_clean[:80]
                break
    if not cover_sub:
        cover_sub = "基于对话数据的深度分析报告"

    # 将markdown内容按 ## 章节拆分
    chapters = []
    current_chapter = {"title": "核心发现", "slides": []}
    current_slide_content = []
    in_table = False
    table_rows = []
    table_header = ""

    def flush_slide(ch, slide_content):
        if not slide_content:
            return
        text = '\n'.join(slide_content).strip()
        if len(text) < 30:
            return
        # Determine slide type
        stype = "text"
        if '|' in text and text.count('|') > 3:
            stype = "table"
        # Extract title from first heading
        title = ""
        body_lines = []
        for l in text.split('\n'):
            ls = l.strip()
            if ls.startswith('### '):
                title = ls[4:].strip()
            elif ls.startswith('## '):
                title = ls[3:].strip()
            elif ls.startswith('# '):
                title = ls[2:].strip()
            else:
                body_lines.append(l)
        if not title:
            title = ch["title"]

        # Extract data points
        data_points = []
        for l in body_lines:
            if '|' in l and not l.strip().startswith('|'):
                parts = [p.strip() for p in l.split('|') if p.strip()]
                if len(parts) >= 2:
                    data_points.append({"value": parts[0], "label": parts[1] if len(parts) > 1 else ""})

        # Clean body text
        body_text = '\n'.join([l for l in body_lines if l.strip() and not l.strip().startswith('#')])

        ch["slides"].append({
            "type": "data" if data_points else "text",
            "title": title,
            "data_points": data_points,
            "body_text": body_text,
            "source": "曜势科技 AI 分析 · 基于对话数据"
        })

    for line in lines:
        s = line.strip()
        if s.startswith('## '):
            # New chapter
            if current_chapter["slides"] or current_slide_content:
                flush_slide(current_chapter, current_slide_content)
                current_slide_content = []
            if current_chapter["slides"]:
                chapters.append(current_chapter)
            current_chapter = {"title": s[3:].strip()[:60], "slides": []}
        elif s.startswith('### '):
            # New slide within chapter
            flush_slide(current_chapter, current_slide_content)
            current_slide_content = [s]
        elif s == '---' or s == '***':
            flush_slide(current_chapter, current_slide_content)
            current_slide_content = []
        else:
            current_slide_content.append(line)

    # Final flush
    flush_slide(current_chapter, current_slide_content)
    if current_chapter["slides"]:
        chapters.append(current_chapter)

    # Fallback if parsing produced nothing useful
    if not chapters or sum(len(ch["slides"]) for ch in chapters) < 2:
        # Simple: split the whole report into paragraph chunks
        paras = [p.strip() for p in report_md.split('\n\n') if len(p.strip()) > 40]
        chapters = [{"title": "调研报告", "slides": []}]
        for i, para in enumerate(paras):
            lines_in_para = para.split('\n')
            title = lines_in_para[0].strip().lstrip('#').strip()[:60] if lines_in_para else f"关键发现 {i+1}"
            chapters[0]["slides"].append({
                "type": "text",
                "title": title,
                "data_points": [],
                "body_text": para,
                "source": "曜势科技 AI 分析"
            })

    # Ensure minimum 10 slides for brand/business reports, 8 for research
    min_slides = 10 if ("品牌手册" in report_title or "商业计划书" in report_title) else 8
    total_slides = sum(len(ch["slides"]) for ch in chapters)
    while total_slides < min_slides:
        for ch in chapters:
            for sl in list(ch["slides"]):
                if total_slides >= min_slides: break
                if sl.get("body_text") and len(sl["body_text"]) > 150:
                    # Split long content across multiple slides
                    text = sl["body_text"]
                    # Split on paragraph or sentence boundaries
                    parts = text.split('\n\n') if '\n\n' in text else text.split('\n')
                    parts = [p.strip() for p in parts if p.strip()]
                    if len(parts) >= 2:
                        mid = len(parts) // 2
                        sl["body_text"] = '\n\n'.join(parts[:mid])
                        for pi in range(mid, len(parts), max(1, mid)):
                            chunk = '\n\n'.join(parts[pi:pi+max(1,mid)])
                            if chunk.strip():
                                ch["slides"].append({
                                    "type": "text",
                                    "title": sl["title"],
                                    "data_points": [],
                                    "body_text": chunk,
                                    "source": "曜势科技 AI 分析"
                                })
                                total_slides += 1
            if total_slides >= min_slides: break

    # ── 去重：合并高度相似幻灯片（同一章节内文字重复>60%则合并）───
    def _text_similarity(a: str, b: str) -> float:
        if not a or not b: return 0
        wa = set(a.replace('\n',' ').split())
        wb = set(b.replace('\n',' ').split())
        if not wa or not wb: return 0
        return len(wa & wb) / max(len(wa), len(wb))

    for ch in chapters:
        merged = []
        for sl in ch["slides"]:
            if merged and _text_similarity(
                sl.get("body_text",""), merged[-1].get("body_text","")
            ) > 0.6:
                # 合并：追加数据点，保留更长的正文
                merged[-1]["data_points"].extend(sl.get("data_points",[]))
                if len(sl.get("body_text","")) > len(merged[-1].get("body_text","")):
                    merged[-1]["body_text"] = sl["body_text"]
            else:
                merged.append(sl)
        # 章节页数上限：调研/品牌报告多一些，产品手册适中
        max_per_ch = 10 if ("品牌" in report_title or "商业计划书" in report_title) else (6 if "调研" in report_title else 5)
        ch["slides"] = merged[:max_per_ch]

    # 补充缺失章节：并行调用LLM基于对话数据生成
    # 品牌/商业计划书25-30页，产品手册15-25页，调研报告25-35页
    if "品牌" in report_title or "商业计划书" in report_title:
        min_content = 6
    elif "产品" in report_title:
        min_content = 4
    else:
        min_content = 5
    fill_tasks = []
    for ch in chapters:
        needed = min_content - len(ch["slides"])
        for _ in range(max(0, needed)):
            fill_prompt = f"""基于以下对话数据，为「{ch["title"]}」章节生成一页补充内容。
要求：提取对话中的具体数据、数字、表格，用实际数据填充，禁止使用"详见Node1/Node2"等占位语。
如果没有直接数据，用行业常识合理推算并标注[行业测算]。

对话数据：
{conv_text[:3000]}

输出格式（纯markdown，60-150字）：
### {ch["title"]}
正文内容+数据表格（如有）"""
            fill_tasks.append((ch, fill_prompt))

    def _fill_slide(ch, prompt):
        try:
            fill_text = call_deepseek(
                "你是专业报告撰写专家。优先使用对话已有数据，缺失时用行业常识补充。禁止留空或写占位语。",
                prompt, timeout=15, max_tokens=200, model=model
            )
            if fill_text and len(fill_text) > 50:
                fill_text = fill_text.replace("### " + ch["title"], "").strip()
                return {"type": "text", "title": ch["title"],
                        "data_points": [], "body_text": fill_text,
                        "source": "曜势科技 AI补全"}
        except Exception:
            pass
        return None

    if fill_tasks:
        with ThreadPoolExecutor(max_workers=2) as ex:
            futures = {ex.submit(_fill_slide, ch, p): (ch, p) for ch, p in fill_tasks}
            for f in as_completed(futures):
                ch, _ = futures[f]
                result = f.result()
                if result:
                    ch["slides"].append(result)

    # Build spec-compliant HTML (匹配宠物银饰市场深度调研报告结构)
    ds = datetime.now().strftime("%Y-%m-%d")
    rpt = report_title

    sh = ""
    ch_num = 0

    for ci, ch in enumerate(chapters):
        ch_num += 1
        cn = str(ch_num).zfill(2)
        ch_title = _esc(ch["title"])

        sh += (
            '<!-- CHAPTER ' + cn + ': ' + ch_title + ' -->\n'
            '<div class="chapter-header" id="ch' + str(ch_num) + '">\n'
            '  <span class="chapter-tag">CHAPTER ' + cn + '</span>\n'
            '  <h2>' + ch_title + '</h2>\n'
            '</div>\n'
        )

        for sli, sl in enumerate(ch["slides"]):
            title_esc = _esc(sl["title"])

            if title_esc and title_esc != ch["title"]:
                sh += (
                    '<div class="section-header">\n'
                    '  <h3><span class="dot"></span>' + title_esc + '</h3>\n'
                    '</div>\n'
                )

            body_html = ""
            text_parts = []
            chart_parts = []
            card_parts = ""

            # Data cards
            if sl.get("data_points") and len(sl["data_points"]) >= 2:
                # Detect if data_points are number-sequence scores (e.g. "9,9,8,7" | "品牌名")
                # If so, render as mini bar chart instead of text cards
                all_numbers = all(
                    _is_number_sequence(dp.get("label", "")) for dp in sl["data_points"]
                )
                if all_numbers:
                    colors = ['#1a365d','#2c5282','#ed8936','#38a169','#e53e3e','#6366f1']
                    bars_html = ''
                    for i, dp in enumerate(sl["data_points"][:6]):
                        nums = [float(x.strip()) for x in dp["label"].split(',')]
                        max_n = max(nums) if nums else 10
                        bar_segs = ''
                        for n in nums:
                            h = max(4, int((n / max_n) * 72)) if max_n > 0 else 4
                            bar_segs += '<div style="flex:1;min-width:16px;height:{}px;background:{};border-radius:3px 3px 0 0;margin:0 1px" title="{}"></div>'.format(h, colors[i % len(colors)], int(n))
                        bars_html += '<div style="display:flex;align-items:flex-end;gap:0;margin-bottom:10px"><span style="font-size:12px;color:#4a5568;width:70px;flex-shrink:0;text-align:right;padding-right:10px;line-height:1.3">{}</span><div style="display:flex;align-items:flex-end;flex:1;gap:0">{}</div></div>'.format(_esc(dp["value"]), bar_segs)
                    chart_parts.append(
                        '<div class="content"><div class="chart-box">\n'
                        '  <h4>📊 评分对比</h4>\n'
                        '  <div class="chart-area">\n'
                        '    <div style="padding:16px 20px">' + bars_html + '</div>\n'
                        '  </div>\n</div></div>\n'
                    )
                else:
                    cards = ""
                    for dp in sl["data_points"][:4]:
                        cards += '<div class="data-card bordered"><div class="card-label">' + _esc(dp["label"]) + '</div><div class="card-value" style="font-size:24px">' + _esc(dp["value"]) + '</div></div>'
                    card_parts = '<div class="content"><div class="data-cards">' + cards + '</div></div>\n'

            if sl.get("body_text"):
                body_lines = sl["body_text"].split('\n')
                for line in body_lines:
                    ps2 = line.strip()
                    if not ps2:
                        continue

                    if ps2.startswith('BAR:'):
                        raw = ps2[4:].strip()
                        pairs = [p.strip().split('|') for p in raw.split(',') if '|' in p]
                        items = [{"label":p[0].strip(),"val":_parse_chart_value(p[1])} for p in pairs if len(p)>=2]
                        if items:
                            colors = ['#1a365d','#2c5282','#ed8936','#38a169','#e53e3e']
                            max_v = max(it["val"] for it in items) or 1
                            bars = ''
                            for j,it in enumerate(items):
                                h = max(20,int((it["val"]/max_v)*240))
                                bars += '<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:8px;justify-content:flex-end;min-width:60px"><span style="font-weight:700;font-size:15px;color:#2d3748">'+_esc(str(it["val"]))+'</span><div style="width:100%;max-width:80px;height:'+str(h)+'px;background:'+colors[j%len(colors)]+';border-radius:4px 4px 0 0"></div><span style="font-size:12px;color:#718096;text-align:center">'+_esc(it["label"])+'</span></div>'
                            chart_parts.append(
                                '<div class="content"><div class="chart-box">\n'
                                '  <h4>📊 数据对比</h4>\n'
                                '  <div class="chart-area">\n'
                                '    <div style="display:flex;align-items:flex-end;gap:24px;height:260px;width:100%;max-width:600px">\n' + bars + '\n</div>\n'
                                '  </div>\n</div></div>\n'
                            )

                    elif ps2.startswith('HBAR:'):
                        raw = ps2[5:].strip()
                        pairs = [p.strip().split('|') for p in raw.split(',') if '|' in p]
                        items = [{"label":p[0].strip(),"val":_parse_chart_value(p[1])} for p in pairs if len(p)>=2]
                        if items:
                            colors = ['#1a365d','#2c5282','#ed8936','#38a169','#e53e3e']
                            max_v = max(it["val"] for it in items) or 1
                            hbars = ''
                            for j,it in enumerate(items):
                                pct = min(100,int((it["val"]/max_v)*100))
                                hbars += '<div style="display:flex;align-items:center;gap:12px;margin-bottom:10px"><span style="width:90px;font-size:13px;color:#2d3748;text-align:right;flex-shrink:0">'+_esc(it["label"])+'</span><div style="flex:1;height:22px;background:#f7fafc;border-radius:4px;overflow:hidden"><div style="width:'+str(pct)+'%;height:100%;background:'+colors[j%len(colors)]+';border-radius:4px"></div></div><span style="font-size:13px;font-weight:600;color:#2d3748;width:50px">'+_esc(str(it["val"]))+'</span></div>'
                            chart_parts.append(
                                '<div class="content"><div class="chart-box">\n'
                                '  <h4>📊 横向对比</h4>\n'
                                '  <div class="chart-area">\n'
                                '    <div style="width:100%;max-width:600px">\n' + hbars + '\n</div>\n'
                                '  </div>\n</div></div>\n'
                            )

                    elif ps2.startswith('PIE:'):
                        raw = ps2[4:].strip()
                        pairs = [p.strip().split('|') for p in raw.split(',') if '|' in p]
                        items = []
                        for p in pairs:
                            if len(p) < 2: continue
                            label, val_str = p[0].strip(), p[1].strip()
                            pct_val = _parse_chart_value(val_str)
                            # 如果解析出0，可能是LLM把顺序写反了（数值|标签），尝试交换
                            if pct_val == 0:
                                swapped = _parse_chart_value(label)
                                if swapped > 0:
                                    pct_val = swapped
                                    label = val_str
                            items.append({"label": label, "pct": pct_val})
                        if items:
                            colors = ['#1a365d','#2c5282','#ed8936','#38a169','#e53e3e','#718096']
                            grad_parts = []
                            cum = 0
                            for j,it in enumerate(items):
                                c = colors[j%len(colors)]
                                grad_parts.append(c+' '+str(int(cum))+'% '+str(int(cum+it["pct"]))+'%')
                                cum += it["pct"]
                            gradient = 'conic-gradient('+','.join(grad_parts)+')'
                            legend = ''
                            for j,it in enumerate(items):
                                legend += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px"><span style="width:12px;height:12px;border-radius:3px;background:'+colors[j%len(colors)]+';flex-shrink:0"></span><span style="font-size:13px;color:#2d3748">'+_esc(it["label"])+' <strong>'+_esc(str(it["pct"]))+'%</strong></span></div>'
                            chart_parts.append(
                                '<div class="content"><div class="chart-box">\n'
                                '  <h4>📊 占比分布</h4>\n'
                                '  <div class="chart-area">\n'
                                '    <div style="width:180px;height:180px;border-radius:50%;background:'+gradient+';flex-shrink:0"></div>\n'
                                '    <div style="min-width:160px">'+legend+'</div>\n'
                                '  </div>\n</div></div>\n'
                            )

                    elif ps2.startswith('|') and '|' in ps2[1:]:
                        continue  # tables handled separately

                    elif ps2 and not ps2.startswith('#'):
                        # 过滤代码块和未解析的图表数据
                        if ps2.startswith('```') or ps2.startswith('标签 ') or '|' in ps2 and not ps2.startswith('|'):
                            continue
                        cleaned = _re_clean.sub(r'\*\*|__', '', ps2)
                        text_parts.append('<p>' + _esc(cleaned) + '</p>')

            # Assemble sections
            if text_parts:
                body_html += '<div class="body-text">\n' + '\n'.join(text_parts) + '\n</div>\n'

            if card_parts:
                body_html += card_parts

            # Handle tables in body_text
            if sl.get("body_text"):
                table_lines = []
                in_tbl = False
                for line in sl["body_text"].split('\n'):
                    ls = line.strip()
                    if ls.startswith('|') and ls.endswith('|'):
                        if not in_tbl:
                            in_tbl = True
                            table_lines = []
                        table_lines.append(ls)
                    else:
                        if in_tbl and table_lines:
                            in_tbl = False
                            header_row = None
                            data_rows = []
                            for tl in table_lines:
                                cells = [c.strip() for c in tl.split('|')[1:-1]]
                                if all(re.match(r'^[-:\s]+$', c) for c in cells):
                                    continue
                                if header_row is None:
                                    header_row = cells
                                else:
                                    data_rows.append(cells)
                            if header_row and data_rows:
                                col_count = len(header_row)
                                tbl = '<div class="content"><table class="report-data"><thead><tr>'
                                for c in header_row:
                                    tbl += '<th>' + _esc(c.replace('**', '')) + '</th>'
                                tbl += '</tr></thead><tbody>'
                                for row in data_rows:
                                    if len(row) < 2:
                                        continue
                                    tbl += '<tr>'
                                    for ci2 in range(col_count):
                                        cell = row[ci2] if ci2 < len(row) else "—"
                                        tbl += '<td>' + _esc(cell.replace('**', '')) + '</td>'
                                    tbl += '</tr>'
                                tbl += '</tbody></table></div>\n'
                                body_html += tbl
                        table_lines = []

            if chart_parts:
                body_html += '\n'.join(chart_parts)

            if body_html.strip():
                sh += body_html

    # Final check: ensure minimum content
    if len(sh.strip()) < 500:
        sh += '<div class="body-text"><p>报告生成中，请基于更多对话数据重新生成。</p></div>'
    # Inject into template - between SLIDES_HERE and footer
    ss = template_html.find("<!-- SLIDES_HERE")
    if ss == -1:
        return {"error": "template error"}
    footer_pos = template_html.find('<div class="footer"')
    if footer_pos == -1:
        footer_pos = template_html.find('</body>')
    final_html = template_html[:ss] + "\n" + sh + "\n" + template_html[footer_pos:]
    # Replace title placeholders (use report_title, not extracted cover_title which can be corrupted)
    safe_title = _esc(report_title)
    final_html = final_html.replace('<h1>深度商业调研报告</h1>', '<h1>' + safe_title + '</h1>')
    final_html = final_html.replace('深度商业调研报告</title>', safe_title + '</title>')
    final_html = final_html.replace('<title>深度商业调研报告</title>', '<title>' + safe_title + '</title>')
    # Report-specific accent color (规范第八节)
    if "商业计划书" in report_title:
        accent_color = "#d4a017"  # 金色
    elif "产品" in report_title:
        accent_color = "#38a169"  # 绿色
    elif "营销" in report_title:
        accent_color = "#3182ce"  # 蓝色
    else:
        accent_color = "#ed8936"  # 橙色(默认)
    final_html = final_html.replace('--accent:#ed8936', '--accent:' + accent_color)
    # Page count (规范第十一节)
    page_count = "25-35页" if "调研" in report_title else ("25-30页" if "商业计划书" in report_title or "品牌手册" in report_title else ("15-25页" if "产品" in report_title else "30-40页"))
    final_html = final_html.replace('页数：约30页', '页数：约' + page_count)
    # 确保页面加载完成后重新初始化图标
    final_html = final_html.replace('</body>', '<script>setTimeout(function(){if(typeof lucide!=="undefined")lucide.createIcons();},300);</script></body>')

    import uuid as _u
    import shutil
    st = "".join(c for c in rpt if c.isalnum() or c in "._- ")[:30]
    fn = st + "_" + _u.uuid4().hex[:6] + ".html"
    logo_src = REPORT_TEMPLATES_DIR / "logo.png"
    for fd in ["编程文件库", "AI 对话产出"]:
        fp = PROJECT_LIB / fd / fn
        fp.write_text(final_html, encoding="utf-8")
        if logo_src.exists():
            shutil.copy(logo_src, PROJECT_LIB / fd / "logo.png")
    dp = Path.home() / "Desktop" / fn
    dp.write_text(final_html, encoding="utf-8")
    if logo_src.exists():
        shutil.copy(logo_src, Path.home() / "Desktop" / "logo.png")
    return {"file_path": str(PROJECT_LIB / "编程文件库" / fn), "desktop_path": str(dp), "report_title": rpt, "filename": fn}


def _esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
