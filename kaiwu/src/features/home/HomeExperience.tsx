import { type CSSProperties, useEffect, useRef, useState } from 'react';
import { Box, ChevronDown, ChevronLeft, ChevronRight, GalleryHorizontalEnd, X } from 'lucide-react';
import type { Direction, ShowToast, SkillLibraryItem } from '../../types';
import { ChatInput, type StartupSkillSelection } from './ChatInput';
import '../../styles/home/home-experience.css';

type HomeSkillCard = StartupSkillSelection & {
  id: string;
  index: string;
  body: string;
  toneClass: string;
  rotationClass: string;
};

type HomeCase = {
  id: string;
  index: string;
  title: string;
  body: string;
  tag: string;
  image: string;
};

const HOME_SKILL_CARDS: HomeSkillCard[] = [
  {
    id: 'industry-scan',
    index: '01',
    label: 'INSIGHT',
    title: '行业扫描',
    description: '市场趋势 / 机会缺口 / 初步判断',
    body: '输入行业和目标市场，快速形成可验证的机会判断。',
    prompt: '输入行业和目标市场，开物会帮你快速判断趋势、缺口和机会。',
    color: '#2563eb',
    toneClass: 'tone-blue',
    rotationClass: 'tilt-left-strong',
  },
  {
    id: 'user-profile',
    index: '02',
    label: 'USER',
    title: '用户画像',
    description: '目标用户 / 使用场景 / 关键痛点',
    body: '输入目标人群和使用场景，拆出用户画像、痛点和触发因素。',
    prompt: '输入目标人群和使用场景，开物会帮你拆出画像、痛点和触发因素。',
    color: '#7c3aed',
    toneClass: 'tone-violet',
    rotationClass: 'tilt-right',
  },
  {
    id: 'brand-positioning',
    index: '03',
    label: 'BRAND',
    title: '品牌定位',
    description: '一句话定位 / 差异化 / 记忆点',
    body: '输入创业方向、目标用户和差异点，生成一句话定位。',
    prompt: '输入创业方向、目标用户和差异点，开物会帮你生成一句话定位。',
    color: '#14b8a6',
    toneClass: 'tone-teal',
    rotationClass: 'tilt-left',
  },
  {
    id: 'business-model',
    index: '04',
    label: 'MODEL',
    title: '商业模式',
    description: '收入结构 / 定价假设 / 成本逻辑',
    body: '输入产品、客户和收费方式，推演收入结构与成本边界。',
    prompt: '输入产品、客户和收费方式，开物会帮你推演商业模式。',
    color: '#2563eb',
    toneClass: 'tone-blue',
    rotationClass: 'tilt-right-strong',
  },
  {
    id: 'mvp-definition',
    index: '05',
    label: 'PRODUCT',
    title: 'MVP 定义',
    description: '核心功能 / 验证假设 / 优先级',
    body: '输入产品目标和核心场景，把想法压缩为第一版 MVP。',
    prompt: '输入产品目标和核心场景，开物会帮你定义第一版 MVP。',
    color: '#7c3aed',
    toneClass: 'tone-violet',
    rotationClass: 'tilt-left',
  },
  {
    id: 'action-route',
    index: '06',
    label: 'ACTION',
    title: '执行路线',
    description: '阶段动作 / 资源配置 / 下一步',
    body: '输入资源、周期和渠道，规划 30/60/90 天执行路线。',
    prompt: '输入资源、周期和渠道，开物会帮你规划执行路线。',
    color: '#14b8a6',
    toneClass: 'tone-teal',
    rotationClass: 'tilt-right-strong',
  },
  {
    id: 'competitor-analysis',
    index: '07',
    label: 'COMPETE',
    title: '竞品分析',
    description: '对标对象 / 差异机会 / 避坑策略',
    body: '输入竞品名称或行业关键词，整理可参考与可避开的竞争策略。',
    prompt: '输入竞品或行业关键词，开物会帮你整理竞争策略。',
    color: '#2563eb',
    toneClass: 'tone-blue',
    rotationClass: 'tilt-left-strong',
  },
  {
    id: 'launch-plan',
    index: '08',
    label: 'LAUNCH',
    title: '首发推广',
    description: '内容节奏 / 渠道组合 / 转化动作',
    body: '输入产品方向和预算，生成首发内容、活动节奏和渠道组合。',
    prompt: '输入产品方向和预算，开物会帮你设计首发推广节奏。',
    color: '#7c3aed',
    toneClass: 'tone-violet',
    rotationClass: 'tilt-right',
  },
  {
    id: 'project-deck',
    index: '09',
    label: 'DECK',
    title: '计划书',
    description: '项目摘要 / 核心亮点 / 展示结构',
    body: '输入你已有的资料或想法，整理成一页可展示的项目计划书。',
    prompt: '输入已有资料或想法，开物会帮你整理项目计划书。',
    color: '#14b8a6',
    toneClass: 'tone-teal',
    rotationClass: 'tilt-left',
  },
];

const HOME_CASES: HomeCase[] = [
  {
    id: 'pet-silver',
    index: 'CASE 01',
    title: '宠物银饰',
    body: '从情绪消费切入，构建宠物纪念饰品的定位、产品线和内容种草路径。',
    tag: '情绪消费',
    image: '/home-cases/case-pet-silver.jpg',
  },
  {
    id: 'real-estate',
    index: 'CASE 02',
    title: '房地产中介',
    body: '围绕本地房源、客户信任和私域复购，设计顾问型中介品牌方案。',
    tag: '本地服务',
    image: '/home-cases/case-real-estate.jpg',
  },
  {
    id: 'restaurant',
    index: 'CASE 03',
    title: '餐饮品牌',
    body: '从单品记忆点、门店视觉和首发活动，拆出可复制的小餐饮起盘模型。',
    tag: '线下门店',
    image: '/home-cases/case-restaurant.jpg',
  },
  {
    id: 'fashion',
    index: 'CASE 04',
    title: '服装品牌',
    body: '明确人群风格、价格带和首批 SKU，形成适合内容平台的新品叙事。',
    tag: '消费品牌',
    image: '/home-cases/case-fashion.jpg',
  },
];

type HomeExperienceProps = {
  activeDirection: Direction;
  quickSkills: string[];
  selectedSkill: SkillLibraryItem | null;
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
  showToast: ShowToast;
};

export function HomeExperience({
  activeDirection,
  quickSkills,
  selectedSkill,
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
  showToast,
}: HomeExperienceProps) {
  const scrollRootRef = useRef<HTMLDivElement>(null);
  const skillStageRef = useRef<HTMLDivElement>(null);
  const [activeSkillId, setActiveSkillId] = useState<string | null>('brand-positioning');
  const [casePanelOpen, setCasePanelOpen] = useState(false);
  const activeSkill = HOME_SKILL_CARDS.find((card) => card.id === activeSkillId) || null;

  useEffect(() => {
    scrollRootRef.current?.scrollTo({ top: 0 });
  }, []);

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

  return (
    <div className="home-experience" ref={scrollRootRef}>
      <section className="home-intro-page" aria-label="开物首页开场">
        <header className="home-intro-topbar">
          <span>开物 KAIWU</span>
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
            <div className="home-dashboard-brand" aria-label="开物">
              <span className="home-dashboard-brand-icon">
                <Box size={18} />
              </span>
              <strong>开物</strong>
            </div>
            <nav className="home-dashboard-nav" aria-label="首页快捷操作">
              <button className="home-case-open" onClick={() => setCasePanelOpen(true)} type="button">
                <GalleryHorizontalEnd size={16} />
                <span>项目案例</span>
              </button>
            </nav>
          </header>

          <section className="home-hero-copy">
            <h2>
              选择一张技能卡<br />
              <span>启动你的创业计划</span>
            </h2>
            <p>
              像抽取一张任务卡一样开始：调研、定位、商业模式、品牌、产品、营销和执行路线，帮助你快速完成最小 MVP。
            </p>
          </section>

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
              {HOME_SKILL_CARDS.map((card) => (
                <button
                  key={card.id}
                  className={`home-skill-card ${card.toneClass} ${card.rotationClass}${card.id === activeSkillId ? ' active' : ''}`}
                  onClick={() => setActiveSkillId(card.id)}
                  type="button"
                  aria-pressed={card.id === activeSkillId}
                >
                  <span className="home-skill-chip" aria-hidden="true">
                    <i />
                    <i />
                    <i />
                    <i />
                  </span>
                  <span className="home-skill-label">{card.label}</span>
                  <span className="home-skill-index">{card.index}</span>
                  <strong>{card.title}</strong>
                  <small>{card.description}</small>
                </button>
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
            showToast={showToast}
          />

          <footer className="home-dashboard-footer">
            <span>{activeSkill ? `${activeSkill.title} · ${activeSkill.description}` : '选择一张技能卡开始创业计划'}</span>
            <span>内容由 AI 生成，请核实完整性</span>
          </footer>
        </div>

        <section className={casePanelOpen ? 'home-case-panel open' : 'home-case-panel'} aria-label="项目案例">
          <div className="home-case-board">
            <header className="home-case-head">
              <div>
                <span>PROJECT CASES</span>
                <h2>四个创业案例</h2>
              </div>
              <button className="home-case-close" onClick={() => setCasePanelOpen(false)} type="button" aria-label="关闭项目案例" title="关闭">
                <X size={19} />
              </button>
            </header>
            <div className="home-case-grid">
              {HOME_CASES.map((item) => (
                <article
                  key={item.id}
                  className="home-case-card"
                  style={{ '--home-case-image': `url(${item.image})` } as CSSProperties}
                >
                  <div>
                    <small>{item.index}</small>
                    <strong>{item.title}</strong>
                    <p>{item.body}</p>
                  </div>
                  <span>{item.tag}</span>
                </article>
              ))}
            </div>
          </div>
        </section>
      </section>
    </div>
  );
}
