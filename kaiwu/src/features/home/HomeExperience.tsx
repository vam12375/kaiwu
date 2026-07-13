import { type CSSProperties, useEffect, useMemo, useRef, useState } from 'react';
import { ArrowUpRight, ChevronDown, ChevronLeft, ChevronRight, FileText, GalleryHorizontalEnd, HelpCircle, X } from 'lucide-react';
import type { Direction, ShowToast, SkillLibraryItem } from '../../types';
import { ChatInput, type StartupSkillSelection } from './ChatInput';
import '../../styles/home/home-experience.css';

type HomeSkillCard = StartupSkillSelection & {
  id: string;
  index: string;
  skill: SkillLibraryItem;
  titleLines: string[];
  toneClass: string;
  rotationClass: string;
  titleSize: string;
};

type HomeCase = {
  id: string;
  index: string;
  title: string;
  body: string;
  tag: string;
  image: string;
  brandName?: string;
  reports?: HomeCaseReport[];
};

type HomeCaseReport = {
  stage: string;
  title: string;
  summary: string;
  href: string;
};

const HOME_CARD_ROTATION_CLASSES = ['tilt-left-strong', 'tilt-right', 'tilt-left', 'tilt-right-strong'] as const;

const HOME_CARD_TONES: Record<string, { toneClass: string; color: string }> = {
  blue: { toneClass: 'tone-blue', color: '#2563eb' },
  indigo: { toneClass: 'tone-indigo', color: '#4f46e5' },
  green: { toneClass: 'tone-green', color: '#16a34a' },
  purple: { toneClass: 'tone-violet', color: '#7c3aed' },
  amber: { toneClass: 'tone-amber', color: '#d97706' },
  rose: { toneClass: 'tone-rose', color: '#e11d48' },
  cyan: { toneClass: 'tone-cyan', color: '#0891b2' },
  pink: { toneClass: 'tone-pink', color: '#db2777' },
  slate: { toneClass: 'tone-slate', color: '#475569' },
  orange: { toneClass: 'tone-orange', color: '#ea580c' },
  teal: { toneClass: 'tone-teal', color: '#14b8a6' },
  lime: { toneClass: 'tone-lime', color: '#65a30d' },
};

const HOME_CARD_FALLBACK_TONES = [
  HOME_CARD_TONES.blue,
  HOME_CARD_TONES.indigo,
  HOME_CARD_TONES.teal,
  HOME_CARD_TONES.rose,
  HOME_CARD_TONES.amber,
  HOME_CARD_TONES.cyan,
] as const;

const HOME_CARD_TITLE_LINES: Record<string, string[]> = {
  '用户痛点访谈模拟器': ['用户痛点', '访谈模拟器'],
  '差异化定位设计师': ['差异化', '定位设计师'],
  '第一单成交设计师': ['第一单', '成交设计师'],
  'Slogan 打磨师': ['Slogan', '打磨师'],
  '小红书运营总监': ['小红书', '运营总监'],
  '每日任务拆解官': ['每日任务', '拆解官'],
  '发售人群针对坐标轴理论': ['发售人群针对', '坐标轴理论'],
  '最小MVP从0-1': ['最小 MVP', '从 0-1'],
  '网页采集助手': ['网页采集助手'],
  '会议纪要整理': ['会议纪要', '整理'],
  '数据看板摘要': ['数据看板', '摘要'],
  '原型说明生成': ['原型说明', '生成'],
};

function getTitleVisualLength(text: string) {
  return Array.from(text.trim()).reduce((total, char) => (
    /[A-Za-z0-9-]/.test(char) ? total + 0.62 : total + 1
  ), 0);
}

function splitHomeCardTitle(name: string) {
  const title = name.trim();
  const override = HOME_CARD_TITLE_LINES[title];
  if (override) return override;

  const chars = Array.from(title);
  const length = getTitleVisualLength(title);
  if (length <= 6.4) return [title];
  if (length <= 10) {
    const splitAt = Math.ceil(chars.length / 2);
    return [chars.slice(0, splitAt).join(''), chars.slice(splitAt).join('')];
  }

  const lines: string[] = [];
  let current = '';
  chars.forEach((char) => {
    const next = `${current}${char}`;
    if (current && getTitleVisualLength(next) > 6.4 && lines.length < 2) {
      lines.push(current);
      current = char;
      return;
    }
    current = next;
  });
  if (current) lines.push(current);
  return lines.slice(0, 3);
}

function getHomeCardTitleSize(lines: string[]) {
  const maxLength = Math.max(...lines.map(getTitleVisualLength));
  if (maxLength >= 7) return '18px';
  if (maxLength >= 6) return '19px';
  if (lines.length >= 3) return '18px';
  if (lines.length >= 2) return '21px';
  return '25px';
}

function buildHomeSkillCard(skill: SkillLibraryItem, index: number): HomeSkillCard {
  const tone = (skill.tone && HOME_CARD_TONES[skill.tone]) || HOME_CARD_FALLBACK_TONES[index % HOME_CARD_FALLBACK_TONES.length];
  const label = skill.category || (skill.source === 'external' ? '技能包' : 'SKILL');
  const titleLines = splitHomeCardTitle(skill.name);
  return {
    id: skill.id,
    index: String(index + 1).padStart(2, '0'),
    skill,
    label,
    title: skill.name,
    titleLines,
    description: skill.description || '打开详情查看技能说明',
    prompt: `请结合「${skill.name}」技能，帮我处理下面这个创业问题：`,
    color: tone.color,
    toneClass: tone.toneClass,
    rotationClass: HOME_CARD_ROTATION_CLASSES[index % HOME_CARD_ROTATION_CLASSES.length],
    titleSize: getHomeCardTitleSize(titleLines),
  };
}

const HOME_CASES: HomeCase[] = [
  {
    id: 'pet-silver',
    index: 'CASE 01',
    title: '宠物银饰',
    body: '从情绪消费切入，构建宠物纪念饰品的定位、产品线和内容种草路径。',
    tag: '情绪消费',
    image: '/home-cases/case-pet-silver.jpg',
    brandName: '凝时',
    reports: [
      {
        stage: '01 市场调研',
        title: '宠物银饰情感定制赛道调研',
        summary: '判断宠物纪念银饰的成长期机会，明确"故事定制"的市场入口。',
        href: '/home-case-reports/pet-silver/market-research.html',
      },
      {
        stage: '02 商业方案',
        title: '凝时商业模式计划书',
        summary: '沉淀品牌定位、定价策略、盈利模型和可落地的商业闭环。',
        href: '/home-case-reports/pet-silver/business-plan.html',
      },
      {
        stage: '03 产品落地',
        title: '凝时产品落地手册',
        summary: '拆出 3 个 SKU、成本核算、定价和 4 周启动验证方案。',
        href: '/home-case-reports/pet-silver/product-handbook.html',
      },
      {
        stage: '04 营销方案',
        title: '凝时内容营销方案',
        summary: '围绕 5A 漏斗、故事矩阵和平台传播，规划内容营销打法。',
        href: '/home-case-reports/pet-silver/marketing-plan.html',
      },
      {
        stage: '05 内容体系',
        title: '凝时内容营销体系',
        summary: '输出 26 条可连续发布的故事库、8 周发布节奏和五媒介分配。',
        href: '/home-case-reports/pet-silver/content-system.html',
      },
    ],
  },
  {
    id: 'real-estate',
    index: 'CASE 02',
    title: '房地产中介',
    body: '围绕本地房源、客户信任和私域复购，设计顾问型中介品牌方案。',
    tag: '本地服务',
    image: '/home-cases/case-real-estate.jpg',
    brandName: '合租侠',
    reports: [
      {
        stage: '01 市场调研',
        title: '商业地产复合赛道调研',
        summary: '判断办公+商业复合空间的需求、竞品和机会，明确案例的市场入口。',
        href: '/home-case-reports/real-estate/market-research.html',
      },
      {
        stage: '02 商业方案',
        title: '合租侠商业模式计划书',
        summary: '沉淀品牌定位、盈利模型、服务路径和可落地的商业闭环。',
        href: '/home-case-reports/real-estate/business-plan.html',
      },
      {
        stage: '03 产品落地',
        title: '合租侠产品落地手册',
        summary: '把中介服务拆成具体 SKU、价格、交付动作和启动验证方案。',
        href: '/home-case-reports/real-estate/product-handbook.html',
      },
      {
        stage: '04 营销方案',
        title: '合租侠内容营销方案',
        summary: '围绕信任建立、私域转化和本地服务传播，规划营销打法。',
        href: '/home-case-reports/real-estate/marketing-plan.html',
      },
      {
        stage: '05 内容体系',
        title: '合租侠内容营销体系',
        summary: '输出可连续发布的故事库、发布节奏和平台内容分配。',
        href: '/home-case-reports/real-estate/content-system.html',
      },
    ],
  },
  {
    id: 'restaurant',
    index: 'CASE 03',
    title: '餐饮品牌',
    body: '从单品记忆点、门店视觉和首发活动，拆出可复制的小餐饮起盘模型。',
    tag: '线下门店',
    image: '/home-cases/case-restaurant.jpg',
    brandName: '锅气',
    reports: [
      {
        stage: '01 市场调研',
        title: '麻辣香锅工作餐赛道调研',
        summary: '判断麻辣香锅存量竞争下的细分机会，明确"快香锅"的市场入口。',
        href: '/home-case-reports/restaurant/market-research.html',
      },
      {
        stage: '02 商业方案',
        title: '锅气商业模式计划书',
        summary: '沉淀品牌定位、盈利模型、定价策略和可落地的商业闭环。',
        href: '/home-case-reports/restaurant/business-plan.html',
      },
      {
        stage: '03 产品落地',
        title: '锅气产品落地手册',
        summary: '把餐饮服务拆成具体 SKU、定价、成本核算和启动验证方案。',
        href: '/home-case-reports/restaurant/product-handbook.html',
      },
      {
        stage: '04 营销方案',
        title: '锅气内容营销方案',
        summary: '围绕 5A 漏斗、故事矩阵和平台传播，规划内容营销打法。',
        href: '/home-case-reports/restaurant/marketing-plan.html',
      },
      {
        stage: '05 内容体系',
        title: '锅气内容营销体系',
        summary: '输出 32 条可连续发布的故事库、8 周发布节奏和五媒介分配。',
        href: '/home-case-reports/restaurant/content-system.html',
      },
    ],
  },
  {
    id: 'fashion',
    index: 'CASE 04',
    title: '服装品牌',
    body: '明确人群风格、价格带和首批 SKU，形成适合内容平台的新品叙事。',
    tag: '消费品牌',
    image: '/home-cases/case-fashion.jpg',
    brandName: '简序',
    reports: [
      { stage: '01 市场调研', title: '设计师品牌服装赛道调研', summary: '判断"高性价比极简通勤装"的市场空白，明确内容电商驱动的机会。', href: '/home-case-reports/fashion/market-research.html' },
      { stage: '02 商业方案', title: '简序商业模式计划书', summary: '沉淀品牌定位、定价策略和内容驱动的商业闭环。', href: '/home-case-reports/fashion/business-plan.html' },
      { stage: '03 产品落地', title: '简序产品落地手册', summary: '拆出 4 个 SKU、成本核算和 4 周启动验证方案。', href: '/home-case-reports/fashion/product-handbook.html' },
      { stage: '04 营销方案', title: '简序内容营销方案', summary: '围绕 5A 漏斗和故事矩阵，规划小红书驱动的营销打法。', href: '/home-case-reports/fashion/marketing-plan.html' },
      { stage: '05 内容体系', title: '简序内容营销体系', summary: '输出 32 条可连续发布的故事库和 8 周发布节奏。', href: '/home-case-reports/fashion/content-system.html' },
    ],
  },
  {
    id: 'qianban',
    index: 'CASE 05',
    title: '牵伴 AI',
    body: '用 AI 把家庭照片、长辈回忆和代际沟通编织成可互动、可沉淀的亲情故事。',
    tag: '银发陪伴',
    image: '/home-cases/case-qianban.jpg',
    brandName: '牵伴 AI',
    reports: [
      {
        stage: '项目方案',
        title: '牵伴 AI 家庭记忆项目方案',
        summary: '围绕家庭记忆、长辈陪伴和 AI 生成故事，展示产品体验、用户价值与商业想象。',
        href: '/home-case-reports/qianban/index.html',
      },
    ],
  },
];

type HomeExperienceProps = {
  activeDirection: Direction;
  quickSkills: string[];
  skillItems: SkillLibraryItem[];
  selectedSkill: SkillLibraryItem | null;
  onSkillDetailOpen: (skill: SkillLibraryItem) => void;
  onStartupSkillSelect?: (skill: SkillLibraryItem) => void;
  onSelectedSkillRemove: () => void;
  homeTextareaRef: React.RefObject<HTMLTextAreaElement | null>;
  inputText: string;
  setInputText: (value: string) => void;
  isComposingRef: React.MutableRefObject<boolean>;
  handleSend: () => void;
  stopGeneration: () => void;
  isLoading: boolean;
  modelIndex: number;
  setModelIndex: (value: number) => void;
  onReferenceHistoryClick?: () => void;
  showToast: ShowToast;
};

export function HomeExperience({
  activeDirection,
  quickSkills,
  skillItems,
  selectedSkill,
  onSkillDetailOpen,
  onStartupSkillSelect,
  onSelectedSkillRemove,
  homeTextareaRef,
  inputText,
  setInputText,
  isComposingRef,
  handleSend,
  stopGeneration,
  isLoading,
  modelIndex,
  setModelIndex,
  onReferenceHistoryClick,
  showToast,
}: HomeExperienceProps) {
  const scrollRootRef = useRef<HTMLDivElement>(null);
  const skillStageRef = useRef<HTMLDivElement>(null);
  const [activeSkillId, setActiveSkillId] = useState<string | null>(null);
  const [casePanelOpen, setCasePanelOpen] = useState(false);
  const [activeCaseId, setActiveCaseId] = useState<string | null>(null);
  const skillCards = useMemo(() => skillItems.map(buildHomeSkillCard), [skillItems]);
  const activeSkill = skillCards.find((card) => card.id === activeSkillId) || null;
  const activeCase = HOME_CASES.find((item) => item.id === activeCaseId) || null;

  useEffect(() => {
    scrollRootRef.current?.scrollTo({ top: 0 });
  }, []);

  useEffect(() => {
    if (activeSkillId && !skillCards.some((card) => card.id === activeSkillId)) {
      setActiveSkillId(null);
    }
  }, [activeSkillId, skillCards]);

  const scrollToDashboard = () => {
    scrollRootRef.current?.scrollTo({
      top: scrollRootRef.current.clientHeight,
      behavior: 'smooth',
    });
  };

  const scrollSkills = (direction: 'previous' | 'next') => {
    skillStageRef.current?.scrollBy({
      left: direction === 'previous' ? -360 : 360,
      behavior: 'smooth',
    });
  };

  const selectStartupSkill = (card: HomeSkillCard) => {
    setActiveSkillId(card.id);
    onStartupSkillSelect?.(card.skill);
  };

  const closeCasePanel = () => {
    setCasePanelOpen(false);
    setActiveCaseId(null);
  };

  const openCase = (item: HomeCase) => {
    if (!item.reports?.length) {
      showToast({ message: `${item.title}案例资料建设中`, variant: 'info' });
      return;
    }
    setActiveCaseId(item.id);
  };

  const casePanelClassName = [
    'home-case-panel',
    casePanelOpen ? 'open' : '',
    activeCase ? 'detail-open' : '',
  ].filter(Boolean).join(' ');

  return (
    <div className="home-experience" ref={scrollRootRef}>
      <section className="home-intro-page" aria-label="开物首页开场">
        <header className="home-intro-topbar">
          <img className="home-intro-logo" src="/kaiwu-intro-logo.png" alt="开物 Kaiwu" />
          <span>JUST DO IT</span>
        </header>
        <div className="home-intro-main">
          <div className="home-intro-sticker" aria-hidden="true" />
          <h1>
            如果你有一个<br />
            创业梦想<br />
            就用<strong>开物</strong>来立刻实现它吧！
          </h1>
          <p>洞察 · 模式 · 产品 · 行动</p>
        </div>
        <footer className="home-intro-footer">
          <button className="home-scroll-cue" onClick={scrollToDashboard} type="button">
            <span>继续创业计划</span>
            <ChevronDown size={17} />
          </button>
        </footer>
      </section>

      <section className="home-dashboard-page" aria-label="开物首页主工作台">
        <div className="home-dashboard-layout">
          <header className="home-dashboard-topbar">
            <nav className="home-dashboard-nav" aria-label="首页快捷操作">
              <button className="home-case-open" onClick={() => setCasePanelOpen(true)} type="button">
                <GalleryHorizontalEnd size={16} />
                <span>项目案例</span>
              </button>
              <button className="home-help-button" type="button" aria-label="帮助" title="帮助">
                <HelpCircle size={16} />
                <span>帮助</span>
              </button>
            </nav>
          </header>

          <section className="home-hero-copy">
            <h2>
              在对话框说出你的想法<br />
              <span>即刻开启创业之旅</span>
            </h2>
            <p>
              只需几轮沟通对话，您便可获得《深度调研报告》《品牌商业方案报告》
              <br />
              《产品落地执行手册》《系统化内容营销方案》《自媒体文案报告》，让项目全貌在您面前一览无余。
            </p>
          </section>

          <ChatInput
            activeDirection={activeDirection}
            quickSkills={quickSkills}
            selectedSkill={selectedSkill}
            onSelectedSkillRemove={onSelectedSkillRemove}
            startupSkill={activeSkill}
            onStartupSkillRemove={() => setActiveSkillId(null)}
            placeholder={activeSkill?.prompt}
            homeTextareaRef={homeTextareaRef}
            inputText={inputText}
            setInputText={setInputText}
            isComposingRef={isComposingRef}
            handleSend={handleSend}
            stopGeneration={stopGeneration}
            isLoading={isLoading}
            modelIndex={modelIndex}
            setModelIndex={setModelIndex}
            onReferenceHistoryClick={onReferenceHistoryClick}
            showToast={showToast}
          />

          <section className="home-skill-zone" aria-label="创业技能卡片">
            <button
              className="home-skill-arrow previous"
              onClick={() => scrollSkills('previous')}
              type="button"
              aria-label="查看上一组技能卡"
              title="上一组"
            >
              <ChevronLeft size={24} />
            </button>
            <div className="home-skill-stage" ref={skillStageRef}>
              {skillCards.map((card) => (
                <article
                  key={card.id}
                  className={`home-skill-card ${card.toneClass} ${card.rotationClass}${card.titleLines.length > 1 ? ' title-multiline' : ''}${card.id === activeSkillId ? ' active' : ''}`}
                  style={{ '--home-skill-title-size': card.titleSize } as CSSProperties}
                >
                  <button
                    className="home-skill-select"
                    onClick={() => selectStartupSkill(card)}
                    type="button"
                    aria-pressed={card.id === activeSkillId}
                    aria-label={`选择${card.title}`}
                  >
                    <span className="home-skill-label">{card.label}</span>
                    <span className="home-skill-index">{card.index}</span>
                    <strong>
                      {card.titleLines.map((line) => (
                        <span key={line}>{line}</span>
                      ))}
                    </strong>
                    <small>
                      <span>{card.description}</span>
                    </small>
                  </button>
                  <button
                    className="home-skill-help"
                    onClick={() => onSkillDetailOpen(card.skill)}
                    type="button"
                    aria-label={`查看${card.title}详情`}
                    title="查看技能详情"
                  >
                    <HelpCircle size={15} />
                  </button>
                </article>
              ))}
            </div>
            <button
              className="home-skill-arrow next"
              onClick={() => scrollSkills('next')}
              type="button"
              aria-label="查看下一组技能卡"
              title="下一组"
            >
              <ChevronRight size={24} />
            </button>
          </section>

          <p className="home-skill-footnote">
            在您后续创业的执行阶段，我们的技能库还会持续更新，在创业过程中的各个细节为您持续赋能。
          </p>
        </div>

        <section className={casePanelClassName} aria-label="项目案例">
          <div className="home-case-board">
            <header className="home-case-head">
              {activeCase ? (
                <div className="home-case-detail-title">
                  <button className="home-case-back" onClick={() => setActiveCaseId(null)} type="button">
                    <ChevronLeft size={16} />
                    <span>返回案例</span>
                  </button>
                  <span>CASE LIBRARY</span>
                  <h2>{activeCase.title}案例资料</h2>
                  <p>{activeCase.body}</p>
                </div>
              ) : (
                <div>
                  <span>PROJECT CASES</span>
                  <h2>五个创业案例</h2>
                </div>
              )}
              <button className="home-case-close" onClick={closeCasePanel} type="button" aria-label="关闭项目案例" title="关闭">
                <X size={19} />
              </button>
            </header>
            {activeCase ? (
              <div className="home-case-detail">
                <div className="home-case-detail-hero" style={{ '--home-case-image': `url(${activeCase.image})` } as CSSProperties}>
                  <small>{activeCase.index}</small>
                  <strong>{activeCase.brandName || activeCase.title}</strong>
                  <span>{activeCase.tag}</span>
                </div>
                <div className="home-case-report-grid">
                  {activeCase.reports?.map((report) => (
                    <article className="home-case-report-card" key={report.href}>
                      <div className="home-case-report-icon">
                        <FileText size={18} />
                      </div>
                      <div>
                        <small>{report.stage}</small>
                        <strong>{report.title}</strong>
                        <p>{report.summary}</p>
                      </div>
                      <a href={report.href} target="_blank" rel="noreferrer">
                        <span>查看完整报告</span>
                        <ArrowUpRight size={14} />
                      </a>
                    </article>
                  ))}
                </div>
              </div>
            ) : (
              <div className="home-case-grid">
                {HOME_CASES.map((item) => (
                  <button
                    key={item.id}
                    className={`home-case-card${item.reports?.length ? ' is-ready' : ''}`}
                    style={{ '--home-case-image': `url(${item.image})` } as CSSProperties}
                    onClick={() => openCase(item)}
                    type="button"
                    aria-label={`打开${item.title}项目案例`}
                  >
                    <div>
                      <small>{item.index}</small>
                      <strong>{item.title}</strong>
                      <p>{item.body}</p>
                    </div>
                    <span>{item.reports?.length ? '查看案例' : item.tag}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </section>
      </section>
    </div>
  );
}
