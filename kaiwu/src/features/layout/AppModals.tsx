import { useEffect, useRef, useState } from 'react';
import { Search } from 'lucide-react';

import { skillOptions } from '../../data';
import { createProjectFolder, uploadProjectFile } from '../../api/projectFiles';
import type { CustomSkillInput, SkillLibraryItem } from '../../types';

type AppModalsProps = Record<string, any>;

export function AppModals(props: AppModalsProps) {
  const {
    enabledSkillIds,
    fileIndex,
    installSkill,
    installedSkillIds,
    libraryModal,
    previewImageIndex,
    projectFolders,
    projectModal,
    realProjectFiles,
    rechargeModalOpen,
    rechargeView,
    refreshProjectFiles,
    refreshProjectFolders,
    saveCustomSkill,
    setFileIndex,
    setLibraryModal,
    setPreviewImageIndex,
    setProjectModal,
    setRechargeModalOpen,
    setRechargeView,
    setReferenceImageIndexes,
    setSkillIndex,
    setSkillModal,
    setSkillModalData,
    skillIndex,
    skillModal,
    skillModalData,
    toggleSkillEnabled,
    uninstallSkill,
  } = props;

  const [customSkillForm, setCustomSkillForm] = useState<CustomSkillInput>({
    name: '',
    category: '办公提效',
    description: '',
    connection: '',
  });
  const [projectFolderName, setProjectFolderName] = useState('');
  const [projectFolderDesc, setProjectFolderDesc] = useState('');
  const [projectModalStatus, setProjectModalStatus] = useState('');
  const [selectedProjectFile, setSelectedProjectFile] = useState<File | null>(null);
  const [selectedUploadFolder, setSelectedUploadFolder] = useState('');
  const [uploadDragging, setUploadDragging] = useState(false);
  const [uploadingProjectFile, setUploadingProjectFile] = useState(false);
  const projectUploadInputRef = useRef<HTMLInputElement>(null);

  const currentSkill = skillModalData as SkillLibraryItem | null;
  const currentSkillInstalled = Boolean(currentSkill && installedSkillIds.includes(currentSkill.id));
  const currentSkillEnabled = Boolean(currentSkill && enabledSkillIds.includes(currentSkill.id));
  const uploadExcludedFolders = new Set(['图片库', '视频库', '最近文件']);
  const selectableProjectFolders = (projectFolders || []).filter((folder: { name: string }) => !uploadExcludedFolders.has(folder.name));
  const defaultUploadFolder = selectableProjectFolders.find((folder: { name: string }) => folder.name === '创业资料')?.name || selectableProjectFolders[0]?.name || '';

  useEffect(() => {
    if (skillModal === 'custom') {
      setCustomSkillForm({
        name: '',
        category: '办公提效',
        description: '',
        connection: '',
      });
    }
  }, [skillModal]);

  useEffect(() => {
    if (projectModal === 'new-folder') {
      setProjectFolderName('');
      setProjectFolderDesc('');
      setProjectModalStatus('');
    }
    if (projectModal === 'upload') {
      setProjectModalStatus('');
      setSelectedProjectFile(null);
      setSelectedUploadFolder(defaultUploadFolder);
      setUploadDragging(false);
    }
  }, [projectModal, defaultUploadFolder]);

  useEffect(() => {
    if (projectModal !== 'upload') return;
    const selectedStillValid = selectableProjectFolders.some((folder: { name: string }) => folder.name === selectedUploadFolder);
    if (!selectedStillValid) {
      setSelectedUploadFolder(defaultUploadFolder);
    }
  }, [projectModal, selectableProjectFolders, selectedUploadFolder, defaultUploadFolder]);

  const updateCustomSkillForm = (field: keyof CustomSkillInput, value: string) => {
    setCustomSkillForm((current) => ({ ...current, [field]: value }));
  };

  const handleSaveCustomSkill = () => {
    const saved = saveCustomSkill(customSkillForm);
    if (!saved) return;
    setSkillModalData(saved);
    setSkillModal('detail');
  };

  const handleCreateProjectFolder = async () => {
    const name = projectFolderName.trim();
    if (!name) {
      setProjectModalStatus('请输入文件夹名称');
      return;
    }

    try {
      setProjectModalStatus('正在创建...');
      await createProjectFolder({ name, desc: projectFolderDesc.trim() });
      await refreshProjectFolders?.();
      setProjectModal(null);
    } catch {
      setProjectModalStatus('创建失败，请检查名称是否重复');
    }
  };

  const selectProjectUploadFile = (files: FileList | null) => {
    const file = files?.[0];
    if (!file) return;
    setSelectedProjectFile(file);
    setProjectModalStatus('');
  };

  const handleUploadProjectFile = async () => {
    if (!selectedProjectFile) {
      setProjectModalStatus('请选择要上传的文件');
      return;
    }
    if (!selectedUploadFolder) {
      setProjectModalStatus('请先创建一个可保存文件的文件夹');
      return;
    }

    try {
      setUploadingProjectFile(true);
      setProjectModalStatus('正在上传...');
      await uploadProjectFile(selectedProjectFile, selectedUploadFolder);
      await refreshProjectFiles?.();
      await refreshProjectFolders?.();
      setProjectModal(null);
    } catch {
      setProjectModalStatus('上传失败，请稍后重试');
    } finally {
      setUploadingProjectFile(false);
    }
  };

  return (
    <>
            {/* Image Preview Modal */}
            {previewImageIndex !== null && (
              <div className="modal-backdrop" onClick={() => setPreviewImageIndex(null)}>
                <section className="image-preview-modal" onClick={(event) => event.stopPropagation()}>
                  <div className="preview-large generated-image" />
                  <div className="preview-actions">
                    <button className="secondary-action" onClick={() => setPreviewImageIndex(null)} type="button">关闭</button>
                    <button className="primary-action" onClick={() => { setReferenceImageIndexes((items: number[]) => [...items, previewImageIndex]); setPreviewImageIndex(null); }} type="button">导入到输入框作为参考图</button>
                  </div>
                </section>
              </div>
            )}
      
            {/* Skill Modal */}
            {skillModal && (
              <div className="modal-backdrop" onClick={() => setSkillModal(null)}>
                <section className="project-modal" onClick={(event) => event.stopPropagation()}>
                  <header className="modal-header">
                    <div>
                      <div className="modal-kicker">技能库</div>
                      <h2>{skillModal === 'custom' ? '添加自定义技能' : skillModal === 'install' ? '安装技能' : skillModal === 'manage' ? '管理技能' : currentSkill?.name || '技能详情'}</h2>
                    </div>
                    <button className="modal-close" onClick={() => setSkillModal(null)} type="button">×</button>
                  </header>

                  {skillModal === 'custom' && (
                    <div className="project-modal-body">
                      <div className="form-field">
                        <span>技能名称</span>
                        <input value={customSkillForm.name} onChange={(event) => updateCustomSkillForm('name', event.target.value)} placeholder="例如：合同审阅助手" />
                      </div>
                      <div className="form-field">
                        <span>分类</span>
                        <select value={customSkillForm.category} onChange={(event) => updateCustomSkillForm('category', event.target.value)}>
                          <option>办公提效</option>
                          <option>方法论</option>
                          <option>研究分析</option>
                          <option>内容创意</option>
                          <option>开发自动化</option>
                        </select>
                      </div>
                      <div className="form-field">
                        <span>调用说明</span>
                        <textarea value={customSkillForm.description} onChange={(event) => updateCustomSkillForm('description', event.target.value)} placeholder="描述这个技能什么时候被调用、输入什么、输出什么..." />
                      </div>
                      <div className="form-field">
                        <span>连接方式</span>
                        <input value={customSkillForm.connection} onChange={(event) => updateCustomSkillForm('connection', event.target.value)} placeholder="MCP / API / 本地脚本 / 浏览器动作" />
                      </div>
                      <div className="modal-actions">
                        <button className="secondary-action" onClick={() => setSkillModal(null)} type="button">取消</button>
                        <button className="primary-action" onClick={handleSaveCustomSkill} disabled={!customSkillForm.name.trim()} type="button">保存技能</button>
                      </div>
                    </div>
                  )}

                  {skillModal !== 'custom' && currentSkill && (
                    <div className="project-modal-body">
                      <div className="skill-summary-card">
                        <div className={`skill-summary-icon tone-${currentSkill.tone || 'slate'}`}>{currentSkillInstalled ? '✓' : '✦'}</div>
                        <div>
                          <h3>{currentSkill.name}</h3>
                          <p>{currentSkill.description}</p>
                          <span>{currentSkill.category} · {currentSkillInstalled ? (currentSkillEnabled ? '已启用' : '已停用') : '未安装'}</span>
                        </div>
                      </div>

                      {skillModal === 'install' && (
                        <>
                          <p className="modal-desc">安装后，开物可以在对话中根据任务自动调用「{currentSkill.name}」。</p>
                          <div className="file-detail-grid">
                            <span>技能分类</span><strong>{currentSkill.category}</strong>
                            <span>默认启用</span><strong>是</strong>
                            <span>来源</span><strong>{currentSkill.source === 'custom' ? '自定义' : currentSkill.source === 'external' ? '技能包' : '内置市场'}</strong>
                            <span>安装范围</span><strong>当前浏览器工作区</strong>
                          </div>
                        </>
                      )}

                      {skillModal === 'manage' && (
                        <>
                          <div className="setting-item">
                            <div><strong>默认启用</strong><small>允许模型在合适任务中自动调用</small></div>
                            <button className={currentSkillEnabled ? 'switch on' : 'switch'} onClick={() => toggleSkillEnabled(currentSkill.id)} type="button"><span /></button>
                          </div>
                          <div className="modal-subtle-actions">
                            <button onClick={() => setSkillModal('detail')} type="button">查看文本</button>
                            <button onClick={() => { uninstallSkill(currentSkill.id); setSkillModal(null); setSkillModalData(null); }} type="button">卸载技能</button>
                          </div>
                        </>
                      )}

                      {skillModal === 'detail' && (
                        <div className="skill-raw-box">
                          <div className="skill-raw-title">Skill 文本内容</div>
                          <textarea readOnly value={currentSkill.full_content || currentSkill.doc || currentSkill.description} />
                        </div>
                      )}

                      <div className="modal-actions">
                        <button className="secondary-action" onClick={() => setSkillModal(null)} type="button">关闭</button>
                        {currentSkillInstalled ? (
                          <button className="primary-action" onClick={() => setSkillModal('manage')} type="button">管理技能</button>
                        ) : (
                          <button className="primary-action" onClick={() => { installSkill(currentSkill.id); setSkillModal('detail'); }} type="button">确认安装</button>
                        )}
                      </div>
                    </div>
                  )}
                </section>
              </div>
            )}
      
            {/* Project Modal */}
            {projectModal && (
              <div className="modal-backdrop" onClick={() => setProjectModal(null)}>
                <section className="project-modal" onClick={(event) => event.stopPropagation()}>
                  <header className="modal-header">
                    <div>
                      <div className="modal-kicker">项目库</div>
                      <h2>{projectModal === 'new-folder' ? '新建文件夹' : '上传文件'}</h2>
                    </div>
                    <button className="modal-close" onClick={() => setProjectModal(null)} type="button">×</button>
                  </header>
                  {projectModal === 'new-folder' && (
                    <div className="project-modal-body">
                      <div className="form-field">
                        <span>文件夹名称</span>
                        <input value={projectFolderName} onChange={(event) => setProjectFolderName(event.target.value)} placeholder="例如：融资材料" />
                      </div>
                      <div className="form-field">
                        <span>用途说明</span>
                        <textarea value={projectFolderDesc} onChange={(event) => setProjectFolderDesc(event.target.value)} placeholder="描述这个文件夹将用于存放什么资料..." />
                      </div>
                      {projectModalStatus && <div className="modal-status">{projectModalStatus}</div>}
                      <div className="modal-actions">
                        <button className="secondary-action" onClick={() => setProjectModal(null)} type="button">取消</button>
                        <button className="primary-action" onClick={handleCreateProjectFolder} type="button">创建文件夹</button>
                      </div>
                    </div>
                  )}
                  {projectModal === 'upload' && (
                    <div className="project-modal-body">
                      <input
                        ref={projectUploadInputRef}
                        className="sr-only-input"
                        type="file"
                        onChange={(event) => selectProjectUploadFile(event.target.files)}
                      />
                      <div
                        className={uploadDragging ? 'upload-drop is-dragging' : 'upload-drop'}
                        onClick={() => projectUploadInputRef.current?.click()}
                        onDragEnter={(event) => { event.preventDefault(); setUploadDragging(true); }}
                        onDragOver={(event) => { event.preventDefault(); setUploadDragging(true); }}
                        onDragLeave={(event) => { event.preventDefault(); setUploadDragging(false); }}
                        onDrop={(event) => {
                          event.preventDefault();
                          setUploadDragging(false);
                          selectProjectUploadFile(event.dataTransfer.files);
                        }}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter' || event.key === ' ') projectUploadInputRef.current?.click();
                        }}
                      >
                        <strong>{selectedProjectFile ? selectedProjectFile.name : '拖拽文件到这里'}</strong>
                        <span>{selectedProjectFile ? `${Math.ceil(selectedProjectFile.size / 1024)} KB` : '或点击选择本地文件'}</span>
                      </div>
                      <div className="form-field">
                        <span>保存到文件夹</span>
                        <select value={selectedUploadFolder} onChange={(event) => setSelectedUploadFolder(event.target.value)}>
                          {selectableProjectFolders.map((folder: { name: string }) => (
                            <option key={folder.name} value={folder.name}>{folder.name}</option>
                          ))}
                        </select>
                      </div>
                      {selectableProjectFolders.length === 0 && <div className="modal-status">请先创建一个文件夹再上传</div>}
                      {projectModalStatus && <div className="modal-status">{projectModalStatus}</div>}
                      <div className="modal-actions">
                        <button className="secondary-action" onClick={() => setProjectModal(null)} type="button">取消</button>
                        <button className="primary-action" onClick={handleUploadProjectFile} disabled={uploadingProjectFile || selectableProjectFolders.length === 0} type="button">{uploadingProjectFile ? '上传中...' : '开始上传'}</button>
                      </div>
                    </div>
                  )}
                </section>
              </div>
            )}
      
            {/* Recharge Modal */}
            {rechargeModalOpen && (
              <div className="modal-backdrop" onClick={() => setRechargeModalOpen(false)}>
                <section className="project-modal recharge-modal" onClick={(event) => event.stopPropagation()}>
                  <header className="modal-header">
                    <div><h2>积分充值</h2><p>购买积分用于对话、生图、视频、编程和项目产物生成。</p></div>
                    <button className="modal-close" onClick={() => setRechargeModalOpen(false)} type="button">×</button>
                  </header>
                  <div className="recharge-tabs"><button className={rechargeView === 'credits' ? 'active' : ''} onClick={() => setRechargeView('credits')} type="button">充值积分</button><button className={rechargeView === 'plans' ? 'active' : ''} onClick={() => setRechargeView('plans')} type="button">套餐升级</button></div>
                  {rechargeView === 'credits' ? <><div className="recharge-options three"><button className="recharge-card" type="button"><span>轻量补充</span><strong>¥ 19</strong><small>2,000 积分 · 适合对话、文档生成</small></button><button className="recharge-card active" type="button"><span>标准补充</span><strong>¥ 49</strong><small>6,000 积分 · 适合调研、生图和方案生成</small></button><button className="recharge-card" type="button"><span>高频补充</span><strong>¥ 99</strong><small>15,000 积分 · 适合视频、编程和批量产物生成</small></button></div><div className="recharge-plan-tip"><div><strong>需要更稳定的月度额度？</strong><span>升级创业套餐，获得每月固定积分、项目库扩容和更高并发。</span></div><button onClick={() => setRechargeView('plans')} type="button">查看套餐</button></div></> : <div className="recharge-options plan-options"><button className="recharge-card plan-card" type="button"><span>Starter 创业起步版</span><strong>¥ 39/月</strong><small>每月 8,000 积分 · 3 个创业项目 · 基础项目库容量 · 适合想法验证和轻量调研</small></button><button className="recharge-card plan-card active" type="button"><span>Pro 创业加速版</span><strong>¥ 99/月</strong><small>每月 25,000 积分 · 20 个创业项目 · 项目库扩容 · 生图/视频/编程优先队列</small></button></div>}
                  <div className="modal-actions"><button className="secondary-action" onClick={() => setRechargeModalOpen(false)} type="button">取消</button><button className="primary-action" type="button">{rechargeView === 'credits' ? '确认充值' : '确认升级'}</button></div>
                </section>
              </div>
            )}
      
            {/* Library Modal (file/skill picker) */}
            {libraryModal && (
              <div className="modal-backdrop" onClick={() => setLibraryModal(null)}>
                <section className="library-modal" onClick={(event) => event.stopPropagation()}>
                  <header className="modal-header">
                    <div>
                      <div className="modal-kicker">{libraryModal === 'file' ? '项目库' : '技能库'}</div>
                      <h2>{libraryModal === 'file' ? '从项目库中选择文件' : '从技能库中生成图片张数'}</h2>
                    </div>
                    <button className="modal-close" onClick={() => setLibraryModal(null)} type="button">
                      ×
                    </button>
                  </header>
      
                  <div className="modal-search">
                    <Search size={16} />
                    <span>{libraryModal === 'file' ? '搜索文档、表格、访谈记录...' : '搜索技能、工作流、专家能力...'}</span>
                  </div>
      
                  <div className="modal-content">
                    <aside className="modal-categories">
                      <button className="category-item active" type="button">最近使用</button>
                      <button className="category-item" type="button">全部</button>
                      <button className="category-item" type="button">收藏</button>
                      <button className="category-item" type="button">团队共享</button>
                    </aside>
      
                    <div className="modal-list">
                      <div className="modal-list-title">AI 对话产出</div>
                      {(libraryModal === 'file' ? realProjectFiles.filter((f: { folder: string }) => f.folder === 'AI 对话产出') : skillOptions) .map((item: any, index: number) => (
                        <button
                          key={item.name}
                          className={
                            libraryModal === 'file'
                              ? fileIndex === index
                                ? 'modal-row selected'
                                : 'modal-row'
                              : skillIndex === index
                                ? 'modal-row selected'
                                : 'modal-row'
                          }
                          onClick={() => {
                            if (libraryModal === 'file') {
                              setFileIndex(index);
                            } else {
                              setSkillIndex(index);
                            }
                            setLibraryModal(null);
                          }}
                          type="button"
                        >
                          <span className="row-icon">{libraryModal === 'file' ? (item.type === 'HTML' ? '🌐' : '📄') : '✦'}</span>
                          <span className="row-main">
                            <strong>{item.name}</strong>
                            <small>{item.folder} · {item.modified}</small>
                          </span>
                          <span className="row-meta">{item.type}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                </section>
              </div>
            )}
    </>
  );
}

