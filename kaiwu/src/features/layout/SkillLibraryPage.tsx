import type { Dispatch, SetStateAction } from 'react';
import { CheckCircle2, Plus, Search, Sparkles } from 'lucide-react';

import { skillCategories } from '../../data';
import type { SkillCategory, SkillLibraryItem, SkillModal, SkillView } from '../../types';
import '../../styles/project/library-shared.css';
import '../../styles/project/skill-library-page.css';
import '../../styles/project/tones.css';

type SkillLibraryPageProps = {
  activeSkillCategory: SkillCategory;
  enabledSkillIds: string[];
  installedSkillIds: string[];
  setActiveSkillCategory: Dispatch<SetStateAction<SkillCategory>>;
  setSkillModal: Dispatch<SetStateAction<SkillModal>>;
  setSkillModalData: Dispatch<SetStateAction<SkillLibraryItem | null>>;
  setSkillSearchQuery: Dispatch<SetStateAction<string>>;
  setSkillView: Dispatch<SetStateAction<SkillView>>;
  skillItems: SkillLibraryItem[];
  skillSearchQuery: string;
  skillView: SkillView;
  onUseSkill: (skill: SkillLibraryItem) => void;
};

function getSourceLabel(skill: SkillLibraryItem) {
  if (skill.source === 'custom') return '自定义';
  if (skill.source === 'external') return '技能包';
  return '内置';
}

function searchSkill(skill: SkillLibraryItem, query: string) {
  if (!query) return true;
  return skill.name.toLowerCase().includes(query);
}

export function SkillLibraryPage({
  activeSkillCategory,
  enabledSkillIds,
  installedSkillIds,
  setActiveSkillCategory,
  setSkillModal,
  setSkillModalData,
  setSkillSearchQuery,
  setSkillView,
  skillItems,
  skillSearchQuery,
  skillView,
  onUseSkill,
}: SkillLibraryPageProps) {
  const installedSet = new Set(installedSkillIds);
  const enabledSet = new Set(enabledSkillIds);
  const query = skillSearchQuery.trim().toLowerCase();
  const visibleSkills = skillItems
    .filter((skill) => (skillView === 'installed' ? installedSet.has(skill.id) : skill.source !== 'custom'))
    .filter((skill) => (activeSkillCategory === '全部' ? true : skill.category === activeSkillCategory))
    .filter((skill) => searchSkill(skill, query));

  const installedCount = skillItems.filter((skill) => installedSet.has(skill.id)).length;

  const openSkillModal = (skill: SkillLibraryItem, modal: Exclude<SkillModal, null | 'custom' | 'external'>) => {
    setSkillModalData(skill);
    setSkillModal(modal);
  };

  return (
    <section className="library-page">
      <header className="library-header">
        <div>
          <div className="settings-kicker">Skill Hub</div>
          <h2>{skillView === 'market' ? '技能库' : '已安装技能'}</h2>
          <p>{skillView === 'market' ? '发现、安装和查看可用于对话的工具能力。' : `管理 ${installedCount} 个已安装技能的启用状态。`}</p>
        </div>
        <button className="primary-action library-header-action" onClick={() => setSkillModal('custom')} type="button">
          <Plus size={14} />
          添加自定义技能
        </button>
      </header>

      <div className="library-toolbar">
        <label className="library-search">
          <Search size={15} />
          <input
            value={skillSearchQuery}
            onChange={(event) => setSkillSearchQuery(event.target.value)}
            placeholder="搜索技能标题"
            aria-label="搜索技能标题"
          />
        </label>
        <div className="library-tabs">
          <button className={skillView === 'market' ? 'active' : ''} onClick={() => setSkillView('market')} type="button">技能市场</button>
          <button className={skillView === 'installed' ? 'active' : ''} onClick={() => setSkillView('installed')} type="button">已安装</button>
        </div>
      </div>

      <div className="skill-category-row">
        {skillCategories.map((category) => (
          <button
            key={category}
            className={activeSkillCategory === category ? 'active' : ''}
            onClick={() => setActiveSkillCategory(category)}
            type="button"
          >
            {category}
          </button>
        ))}
      </div>

      {visibleSkills.length > 0 ? (
        <div className="skill-library-grid">
          {visibleSkills.map((skill) => {
            const installed = installedSet.has(skill.id);
            const enabled = enabledSet.has(skill.id);
            return (
              <article key={skill.id} className={`skill-library-card tone-${skill.tone || 'slate'}`}>
                <div className="skill-card-top">
                  <span className="skill-card-icon">{installed ? <CheckCircle2 size={15} /> : <Sparkles size={15} />}</span>
                  <span className="skill-card-category">{skill.category}</span>
                </div>
                <h3>{skill.name}</h3>
                <p>{skill.description}</p>
                <div className="skill-card-footer">
                  <span>{installed ? (enabled ? '已启用' : '已停用') : getSourceLabel(skill)}</span>
                  <div className="skill-card-actions">
                    <button onClick={() => openSkillModal(skill, 'detail')} type="button">详情</button>
                    <button onClick={() => installed ? onUseSkill(skill) : openSkillModal(skill, 'install')} type="button">
                      {installed ? '去使用' : '安装'}
                    </button>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <div className="library-empty-state">
          <strong>没有匹配的技能</strong>
          <span>换个关键词或分类试试。</span>
        </div>
      )}
    </section>
  );
}
