/**
 * =============================================================================
 * # 角色
 * 静态数据层 —— 为曜势科技 App 提供所有硬编码的业务配置数据。
 * 包括侧边栏菜单、赛道方向、模型选项、技能市场、项目库文件夹、
 * 快捷技能映射等核心业务数据。所有常量在此集中管理，统一导出。
 *
 * # 输入
 * - lucide-react 图标组件（Users / Sparkles / FileStack）
 * - 业务需求文档中的配置清单
 * - 固定的 UI 文案与示例数据
 *
 * # 输出结构
 * ## 1. 侧边栏与导航
 * sidebarItems —— 侧边栏菜单项配置
 *
 * ## 2. 赛道与技能
 * directions —— 五大创业赛道（通用/需求洞察/商业方案/产品创造/营销推广）
 * quickSkillsByDirection —— 各赛道对应的快捷技能映射
 *
 * ## 3. 模型配置
 * modelOptions —— 内置 AI 模型列表（开物深思/开物极速/开物研究）
 *
 * ## 4. 技能市场
 * skillMarketItems —— 可安装技能的完整信息
 * installedSkills —— 已安装技能名称列表
 * skillTemplates —— 技能模板配置
 * skillCategories —— 技能分类（全部/市场调研/商业方案/品牌建设/产品设计/营销方案/执行路线）
 *
 * ## 5. 项目库
 * projectFolders —— 7 个项目文件夹配置
 *
 * ## 6. 通用数据
 * heroLines / heroText —— 首页打字机文案
 * settingsSections —— 设置页 7 个标签页
 * skillOptions / projectFiles —— 弹窗选择和示例数据
 * =============================================================================
 */

import {
  FileStack,
  Sparkles,
  Users,
} from 'lucide-react';

export const sidebarItems = [
  { key: 'home', label: '新对话', active: true },
  { key: 'expert', label: '创造模式', icon: Users },
  { key: 'skills', label: '技能库', icon: Sparkles },
  { key: 'projects', label: '项目库', icon: FileStack },
];

export const directions = ['通用', '需求洞察', '商业方案', '产品创造', '营销推广'] as const;

export const quickSkillsByDirection = {
  通用: [] as string[],
  需求洞察: ['多平台数据爬取', '市场分析', '目标人群画像', '竞品分析', '机会点挖掘'],
  商业方案: ['商业计划生成', '收入模型设计', '成本结构拆解', '融资叙事梳理', '执行路径规划'],
  产品创造: ['AI 生图', 'AI 生视频', 'AI 编程', '原型设计', 'MVP 功能定义'],
  营销推广: ['账号内容设计', '多平台分发', '数据监控', '达人匹配', '投流优化'],
} as const;

export const modelOptions = [
  { name: 'DeepSeek-V4-Pro', desc: '复杂创业问题与深度推演', id: 'deepseek-v4-pro' },
  { name: 'Doubao-Seed-2.0-Lite', desc: '快速生成方案与草稿', id: 'doubao-seed-2-0-lite-260215' },
];

export const imageModelOptions = [
  'doubao-seedream-5-0-260128',
  'doubao-seedream-5-0-lite-260128',
  'doubao-seedream-4-5-251128',
  'doubao-seedream-4-0-250828',
] as const;

export const imageRatioOptions = ['21:9', '16:9', '3:2', '4:3', '1:1', '3:4', '2:3', '9:16'] as const;
export const imageResolutionOptions = ['2K', '4K'] as const;

export const projectFiles = [
  { name: '商业计划书初稿', desc: '文档 · 更新于今天', meta: 'BP / 12 页' },
  { name: '用户访谈纪要', desc: '研究资料 · 18 条访谈', meta: '调研 / 32 KB' },
  { name: '竞品功能清单', desc: '表格 · 6 个竞品', meta: '表格 / 128 行' },
  { name: 'MVP 功能范围', desc: '产品资料 · 已评审', meta: 'PRD / 8 页' },
  { name: '首批种子用户画像', desc: '运营资料 · 最近打开', meta: '画像 / 5 类' },
];

export const skillOptions = [
  { name: '需求拆解', desc: '把想法拆成用户、场景、痛点', meta: '产品' },
  { name: '竞品分析', desc: '提炼定位、功能和差异化', meta: '研究' },
  { name: '增长方案', desc: '输出获客、转化和留存动作', meta: '增长' },
  { name: '商业模式推演', desc: '梳理收入、成本和关键假设', meta: '商业' },
  { name: '融资材料润色', desc: '优化 BP 表达和投资人叙事', meta: '融资' },
];

export const heroLines = ['从一个模糊想法开始，串联需求调研、商业方案、产品设计与营销推广，', '让 OPC 创业者把每一步判断、产物和行动沉淀成可持续推进的创业项目。'];
export const heroText = heroLines.join('\n');

export const settingsSections = ['账户管理', '系统设置', '智能体设置', '记忆', '模型', '软件配置', '帮助与反馈'] as const;

export const skillMarketItems = [
  {
    name: '用户痛点访谈模拟器',
    desc: '模拟真实用户访谈，挖出痛点、动机、阻力和验证问题',
    category: '市场调研',
    tone: 'blue',
    doc: '在真实访谈前，模拟目标用户会怎么说，生成访谈问题、潜在回答、痛点层级和下一步真实访谈要验证的问题。适用于需求调研、用户画像、产品验证和市场切口判断。',
  },
  {
    name: '差异化定位设计师',
    desc: '找到和别人不一样、用户能听懂的定位表达',
    category: '品牌建设',
    tone: 'indigo',
    doc: '围绕人群、场景、痛点、价格带、竞品和团队资源，比较多个定位方向，输出一句话定位、竞品对比表达和用户听得懂的版本。',
  },
  {
    name: '第一单成交设计师',
    desc: '设计第一个可卖产品、价格、成交路径和验证指标',
    category: '商业方案',
    tone: 'purple',
    doc: '把商业模式拉回第一笔钱：明确第一批付费客户、第一个可卖产品或服务、首单价格、成交路径、成交话术和 7-30 天验证指标。',
  },
  {
    name: 'Slogan 打磨师',
    desc: '打磨一句能传播、能被记住的品牌口号',
    category: '品牌建设',
    tone: 'green',
    doc: '把品牌定位、用户利益、情绪记忆和传播节奏压缩成一句用户能记住、能转述的 slogan，并按清晰度、记忆度、差异化、传播性和可信度筛选。',
  },
  {
    name: '小红书运营总监',
    desc: '设计小红书定位、关键词、选题、笔记和转化路径',
    category: '营销方案',
    tone: 'rose',
    doc: '围绕小红书搜索、种草、收藏、评论、私信和成交，输出账号定位、关键词池、内容栏目、笔记选题、正文结构、CTA、转化路径和发布节奏。',
  },
  {
    name: '每日任务拆解官',
    desc: '把创业大计划拆成今天能完成的 3 件关键任务',
    category: '执行路线',
    tone: 'amber',
    doc: '把创业计划、报告或当前卡点拆成今日主目标、3 个具体任务、步骤、预计时间、产出物、完成标准、不要做清单和晚间复盘问题。',
  },
  { name: '心理登月', desc: '从用户心理层面寻找替代方案，用体验创新解决同质化竞争', category: '品牌建设', tone: 'indigo', doc: '当产品陷入同质化竞争或遇到技术瓶颈时，从心理层面重新定义问题，用体验替代技术方案，以更低成本达到更好效果。适用于差异化策略、用户体验重构、产品定位调整。' },
  { name: '发售人群针对坐标轴理论', desc: '人群分层、内容配比、精准投放与发售策略', category: '营销方案', tone: 'indigo', doc: '基于人群分层和坐标轴模型，规划精准的GTM策略，分配内容预算，设计分阶段发售方案。适用于新品上市、人群定位、投放策略制定。' },
  { name: '最小MVP从0-1', desc: '客户购买心智路径五阶段拆解，内容策略与转化优化', category: '产品设计', tone: 'indigo', doc: '拆解客户从认知到复购的五阶段心智路径，诊断转化漏斗问题，设计分阶段内容策略。适用于内容营销规划、客户旅程设计、转化率优化。' },
  { name: '网页采集助手', desc: '抓取网页信息并整理成结构化资料', category: '市场调研', tone: 'blue', doc: '用于读取网页正文、链接、标题和关键信息，并自动整理成摘要、要点、引用来源和后续待确认问题。适合市场信息收集、竞品页面整理、公开资料归档。' },
  { name: '表格分析器', desc: '读取表格、识别异常并生成分析摘要', category: '市场调研', tone: 'green', doc: '用于处理 XLSX、CSV 等结构化数据，支持字段识别、趋势归纳、异常值提示和结论摘要。适合经营数据、访谈统计、投放数据和竞品功能表分析。' },
  { name: '文档生成器', desc: '把提纲、资料和对话整理成正式文档', category: '商业方案', tone: 'purple', doc: '用于把对话内容、生成图片比例和用户提纲整理成正式文档，可输出需求说明、调研报告、会议纪要、方案草稿和执行计划。' },
  { name: '会议纪要整理', desc: '从录音或文本中提炼结论、任务和风险', category: '商业方案', tone: 'amber' },
  { name: '竞品追踪', desc: '监控产品变化、价格策略和内容动态', category: '市场调研', tone: 'rose' },
  { name: '投放复盘', desc: '聚合投放数据，定位素材和人群问题', category: '营销方案', tone: 'cyan' },
  { name: '代码审查', desc: '检查代码质量、潜在错误和重构机会', category: '产品设计', tone: 'indigo' },
  { name: '短视频脚本', desc: '生成分镜、口播和多平台标题版本', category: '营销方案', tone: 'pink' },
  { name: '知识库问答', desc: '连接项目资料，回答上下文相关问题', category: '市场调研', tone: 'slate' },
  { name: '邮件处理', desc: '分类邮件、生成回复并标记待办事项', category: '营销方案', tone: 'orange' },
  { name: '原型说明生成', desc: '把产品想法拆成页面、模块和交互说明', category: '产品设计', tone: 'teal' },
  { name: '数据看板摘要', desc: '读取指标变化，输出趋势、归因和建议', category: '市场调研', tone: 'lime' },
];

export const installedSkills = ['心理登月', '发售人群针对坐标轴理论', '最小MVP从0-1', '网页采集助手', '表格分析器', '知识库问答'];

export const skillTemplates = [
  { name: '网页信息提取', desc: '适合抓取、整理与摘要', category: '市场调研', tone: 'blue' },
  { name: '竞品研究包', desc: '适合搜索、对比和输出结论', category: '市场调研', tone: 'green' },
  { name: '脚本与内容工厂', desc: '适合选题、脚本和发布', category: '营销方案', tone: 'pink' },
  { name: '代码助手', desc: '适合生成、审查和调试', category: '产品设计', tone: 'indigo' },
];

export const skillCategories = ['全部', '市场调研', '商业方案', '品牌建设', '产品设计', '营销方案', '执行路线'] as const;

export const skillCategoryAliases: Record<string, Exclude<(typeof skillCategories)[number], '全部'>> = {
  方法论: '市场调研',
  办公提效: '商业方案',
  研究分析: '品牌建设',
  内容创意: '产品设计',
  开发自动化: '营销方案',
};

export function normalizeSkillCategory(category?: string) {
  if (!category) return '市场调研';
  return skillCategoryAliases[category] || category;
}

export const projectFolders = [
  { name: '图片库', count: '', desc: 'AI 生图结果、参考图和图片素材', tone: 'blue' },
  { name: '视频库', count: '12 个文件', desc: 'AI 视频结果、镜头草稿和视频素材', tone: 'purple', locked: true },
  { name: '编程文件库', count: '36 个文件', desc: 'AI 编程项目、代码文件和预览资产', tone: 'green', locked: true },
  { name: '创业资料', count: '18 个文件', desc: '商业计划、访谈纪要、市场材料', tone: 'blue' },
  { name: 'AI 对话产出', count: '26 个文件', desc: '由对话生成的文档、表格和摘要', tone: 'purple' },
  { name: '产品设计', count: '12 个文件', desc: 'PRD、原型说明、功能清单', tone: 'green' },
  { name: '营销素材', count: '9 个文件', desc: '脚本、选题、投放复盘和内容规划', tone: 'rose' },
];

export interface IFeatureCard {
  id: string;
  order: number;
  title: string;
  imageUrl: string;
}

export const FEATURE_CARDS: IFeatureCard[] = [
  { id: '1', order: 1, title: '需求调研', imageUrl: '/需求调研-800.webp' },
  { id: '2', order: 2, title: '数据洞察', imageUrl: '/数据洞察-800.webp' },
  { id: '3', order: 3, title: '图片生成', imageUrl: '/图片生成-800.webp' },
  { id: '4', order: 4, title: '商业报告', imageUrl: '/商业报告-800.webp' },
  { id: '5', order: 5, title: '品牌故事', imageUrl: '/品牌故事-800.webp' },
  { id: '6', order: 6, title: '内容营销', imageUrl: '/内容营销-800.webp' },
];

export interface IWorkflowStep {
  id: string;
  stepNumber: number;
  title: string;
  isActive: boolean;
}

export const WORKFLOW_STEPS: IWorkflowStep[] = [
  { id: '1', stepNumber: 1, title: '需求调研', isActive: true },
  { id: '2', stepNumber: 2, title: '全案计划', isActive: false },
  { id: '3', stepNumber: 3, title: '产品创造', isActive: false },
  { id: '4', stepNumber: 4, title: '营销推广', isActive: false },
];
