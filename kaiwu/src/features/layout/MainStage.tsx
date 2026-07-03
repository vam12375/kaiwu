import { ArrowUp, Bot, Brain, ChevronDown, ChevronRight, Cpu, FileStack, HelpCircle, Search, Settings2, UserRound } from 'lucide-react';

import { directions, modelOptions, projectFolders, projectLibraryFiles, settingsSections } from '../../data';
import { ConversationPanel } from '../chat/ConversationPanel';
import { SkillLibraryPage } from './SkillLibraryPage';

type MainStageProps = Record<string, any>;

export function MainStage(props: MainStageProps) {
  const {
    activeDirection,
    activeNodeId,
    activePage,
    activeSettingsSection,
    activeSkillCategory,
    codingMode,
    codingModelOpen,
    codingPreviewUrl,
    conversationOpen,
    conversationTitle,
    convTextareaRef,
    countOpen,
    enabledSkillIds,
    fileIndex,
    followupNodeRef,
    handleSend,
    homeTextareaRef,
    imageCount,
    imageLibraryOpen,
    imageModelOpen,
    imageRatio,
    imageSizeOpen,
    inputText,
    installedSkillIds,
    isComposingRef,
    isImageMode,
    isLoading,
    libraryModal,
    messages,
    modelIndex,
    nodeStatus,
    openPicker,
    openProjectFile,
    projectImages,
    projectView,
    quickSkills,
    ratioOpen,
    realProjectFiles,
    referenceImageIndexes,
    removeUploadedFile,
    resetConversation,
    selectedFolderIndex,
    setActiveDirection,
    setActivePage,
    setActiveSettingsSection,
    setActiveSkillCategory,
    setCodingMode,
    setCodingModelOpen,
    setConversationOpen,
    setCountOpen,
    setImageCount,
    setImageLibraryOpen,
    setImageModelOpen,
    setImageRatio,
    setImageSizeOpen,
    setInputText,
    setLibraryModal,
    setModelIndex,
    setOpenPicker,
    setPreviewImageIndex,
    setProjectModal,
    setProjectView,
    setRatioOpen,
    setReferenceImageIndexes,
    setSelectedFileIndex,
    setSelectedFolderIndex,
    setSkillModal,
    setSkillModalData,
    setSkillSearchQuery,
    setSkillView,
    setSidebarCollapsed,
    setSuggestedQuestions,
    setVideoLibraryOpen,
    setVideoModelOpen,
    setVideoSettingOpen,
    sidebarCollapsed,
    skillItems,
    skillSearchQuery,
    skillView,
    stopGeneration,
    suggestedQuestions,
    typedHeroText,
    uploadedFiles,
    videoLibraryOpen,
    videoModelOpen,
    videoSettingOpen,
  } = props;

  return (
            <main className="main-stage">
              <button
                className={sidebarCollapsed ? 'sidebar-toggle solo visible' : 'sidebar-toggle solo'}
                onClick={() => setSidebarCollapsed(false)}
                type="button"
                aria-label="展开侧边栏"
                title="展开侧边栏"
              >
                <ChevronRight size={16} />
              </button>
              <div className="ambient-orb orb-one" />
              <div className="ambient-orb orb-two" />
              <div className="ambient-orb orb-three" />
              {conversationOpen ? (
                <ConversationPanel
                  activeDirection={activeDirection}
                  activeNodeId={activeNodeId}
                  conversationTitle={conversationTitle}
                  convTextareaRef={convTextareaRef}
                  countOpen={countOpen}
                  fileIndex={fileIndex}
                  followupNodeRef={followupNodeRef}
                  handleSend={handleSend}
                  imageCount={imageCount}
                  imageRatio={imageRatio}
                  inputText={inputText}
                  isComposingRef={isComposingRef}
                  isImageMode={isImageMode}
                  isLoading={isLoading}
                  libraryModal={libraryModal}
                  messages={messages}
                  modelIndex={modelIndex}
                  nodeStatus={nodeStatus}
                  openPicker={openPicker}
                  ratioOpen={ratioOpen}
                  removeUploadedFile={removeUploadedFile}
                  resetConversation={resetConversation}
                  setCountOpen={setCountOpen}
                  setImageCount={setImageCount}
                  setImageRatio={setImageRatio}
                  setInputText={setInputText}
                  setLibraryModal={setLibraryModal}
                  setModelIndex={setModelIndex}
                  setOpenPicker={setOpenPicker}
                  setRatioOpen={setRatioOpen}
                  setSelectedFolderIndex={setSelectedFolderIndex}
                  setSuggestedQuestions={setSuggestedQuestions}
                  stopGeneration={stopGeneration}
                  suggestedQuestions={suggestedQuestions}
                  uploadedFiles={uploadedFiles}
                />
              ) : activePage === 'coding' ? (
                <section className="coding-page">
                  <header className="coding-topbar"><div className="coding-project"><span className="project-square" /><strong>Mobile App UI Kit Design</strong><ChevronDown size={13} /></div><div className="coding-center-tools"><button type="button">AI</button><button type="button">Version 11</button></div><div className="coding-right-tools"><button className={codingMode === 'preview' ? 'active' : ''} onClick={() => setCodingMode('preview')} type="button">预览</button><button className={codingMode === 'code' ? 'active' : ''} onClick={() => setCodingMode('code')} type="button">代码</button></div></header>
                  <div className="coding-layout"><main className="coding-workspace">{codingMode === 'code' ? <div className="code-mode"><aside className="file-tree"><div className="file-section">guidelines</div><button type="button">▾ src</button><button type="button">▾ app</button><button type="button">▾ components</button><button className="active" type="button">App.tsx</button><button type="button">Attributions.md</button><button type="button">▾ styles</button><button type="button">globals.css</button><button type="button">package.json</button><button type="button">vite.config.ts</button></aside><section className="code-editor"><pre>{`import { HomeScreen } from './components/HomeScreen';\nimport { BottomNav } from './components/BottomNav';\n\nexport default function App() {\n  return (\n    <main className="app-shell">\n      <HomeScreen />\n      <BottomNav />\n    </main>\n  );\n}\n\nexport const theme = {\n  radius: 24,\n  primary: '#2563eb',\n  surface: '#ffffff',\n};`}</pre></section></div> : <div className="preview-mode">{codingPreviewUrl ? (
                    <div style={{position:'relative',width:'100%',height:'100%'}}>
                      <iframe src={codingPreviewUrl} style={{width:'100%',height:'100%',border:'none',borderRadius:'12px',background:'#fff'}} title="HTML Preview" />
                      <button onClick={() => { fetch(codingPreviewUrl).then(r => r.blob()).then(b => { const a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = codingPreviewUrl.split('/').pop() || 'file.html'; a.click(); URL.revokeObjectURL(a.href); }); }}
                        className="coding-save-btn" title="下载文件" type="button">⬇ 保存</button>
                    </div>
                  ) : (
                    <div className="vibe-page"><nav><strong>Vibe Studio</strong><span>Design system preview</span></nav><section className="vibe-hero"><div><h1>Build mobile ideas faster</h1><p>Generate screens, components and flows with an AI coding workspace.</p><button type="button">Start prototype</button></div><div className="vibe-phone"><span /><span /><span /></div></section><div className="vibe-grid"><article><strong>Components</strong><p>Reusable UI blocks</p></article><article><strong>Flows</strong><p>Onboarding and paywall</p></article><article><strong>Tokens</strong><p>Color and spacing</p></article></div></div>
                  )}</div>}<footer className="coding-status"><span>main</span><span>{codingMode === 'code' ? 'TypeScript' : 'Preview'}</span><span>1 warning</span></footer></main><aside className="coding-chat"><header><div><strong>AI 编程助手</strong><span>正在协助构建移动端 UI</span></div><button type="button">⋯</button></header><div className="chat-thread" /><div className="coding-composer"><textarea placeholder="Ask for changes" /><div className="composer-foot"><button type="button">＋</button><button className="model-chip" onClick={() => setCodingModelOpen((value: boolean) => !value)} type="button">Gemini 3.1 Pro <ChevronDown size={12} /></button>{codingModelOpen && <div className="coding-model-popover model-menu"><div className="model-menu-title">内置模型</div><button className="model-menu-row selected" type="button"><span className="model-icon">✦</span><span className="model-name">Gemini 3.1 Pro</span><span className="model-badge">限时折扣</span><span className="model-brain">♧</span></button><button className="model-menu-row" type="button"><span className="model-icon">◆</span><span className="model-name">Claude 4 Sonnet</span><span className="model-brain">♧</span></button><button className="model-menu-row" type="button"><span className="model-icon">◆</span><span className="model-name">GPT-5 Coding</span><span className="model-brain">♧</span></button><button className="model-menu-row" type="button"><span className="model-icon">◆</span><span className="model-name">开物代码模型</span><span className="model-brain">♧</span></button><div className="model-menu-title custom">自定义模型</div><button className="model-menu-row" type="button"><span className="model-icon">◆</span><span className="model-name">DeepSeek-V4 Pro:deepseek-v4-pro</span><span className="model-brain">♧</span></button><button className="model-config-row" type="button">+ 配置自定义模型</button></div>}<button className="send-dot" type="button">↑</button></div></div></aside></div>
                </section>
              ) : activePage === 'video' ? (
                <section className={videoLibraryOpen ? 'image-workspace video-workspace library-open' : 'image-workspace video-workspace'}>
                  <header className="image-topbar"><div className="coding-project"><span className="project-square" /><strong>镜头运动短片生成</strong><ChevronDown size={13} /></div>{!videoLibraryOpen && <div className="image-filterbar"><button onClick={() => setVideoLibraryOpen(true)} type="button">视频库</button></div>}</header>
                  <main className="image-feed"><article className="image-result-card"><div className="image-result-meta"><p>城市夜景中的人物缓慢转身，镜头从近景拉远，霓虹光影、低饱和电影色调、轻微景深变化。</p><span>视频生成 · 视频 2.0 · 16:9 · 5 秒 · 高清 1080P</span></div><div className="video-preview-card"><div className="play-button">▶</div><div className="video-timeline"><span /></div></div><div className="result-actions"><button type="button">重新编辑</button><button type="button">再次生成</button><button type="button">下载视频</button></div></article></main>
                  {videoLibraryOpen && <aside className="image-library-drawer"><div className="drawer-head"><strong>视频库</strong><button onClick={() => setVideoLibraryOpen(false)} type="button">×</button></div><div className="drawer-grid video-drawer-grid">{[0, 1, 2, 3, 4, 5] .map((index: number) => (<button key={index} className="video-thumb" type="button"><span>▶</span></button>))}</div></aside>}
                  <div className="image-composer"><button className="upload-slot" type="button">＋</button><div className="image-composer-main"><textarea placeholder="描述你想生成的视频画面、镜头运动和节奏..." defaultValue="城市夜景中的人物缓慢转身，镜头从近景拉远" /><div className="image-composer-tools"><button onClick={() => { setVideoModelOpen((value: boolean) => !value); setVideoSettingOpen(false); }} type="button">视频 2.0</button><button onClick={() => { setVideoSettingOpen((value: boolean) => !value); setVideoModelOpen(false); }} type="button">16:9 · 5秒 · 1080P</button><button type="button">2 条</button><span>消耗 600 积分/次</span></div>{videoModelOpen && <div className="image-popover image-model-popover model-menu"><div className="model-menu-title">内置模型</div><button className="model-menu-row selected" type="button"><span className="model-icon">✦</span><span className="model-name">视频 2.0</span><span className="model-badge">推荐</span><span className="model-brain">♧</span></button><button className="model-menu-row" type="button"><span className="model-icon">✦</span><span className="model-name">视频 1.5</span><span className="model-brain">♧</span></button><button className="model-menu-row" type="button"><span className="model-icon">◆</span><span className="model-name">运镜增强</span><span className="model-brain">♧</span></button><button className="model-config-row" type="button">+ 配置自定义模型</button></div>}{videoSettingOpen && <div className="image-popover image-size-popover"><strong>画面比例</strong><div className="ratio-grid"><button className="active" type="button">16:9</button><button type="button">9:16</button><button type="button">1:1</button><button type="button">4:3</button></div><strong>视频时长</strong><div className="resolution-row"><button className="active" type="button">5 秒</button><button type="button">10 秒</button></div><div className="size-fields"><span>1080P</span><span>24 FPS</span><span>MP4</span></div></div>}</div><button className="image-send" type="button">↑</button></div><button className="help-float" type="button">?</button>
                </section>
              ) : activePage === 'image' ? (
                <section className={imageLibraryOpen ? 'image-workspace library-open' : 'image-workspace'}>
                  <header className="image-topbar"><div className="coding-project"><span className="project-square" /><strong>动态模糊定格生成</strong><ChevronDown size={13} /></div>{!imageLibraryOpen && <div className="image-filterbar"><button onClick={() => setImageLibraryOpen(true)} type="button">图片库</button></div>}</header>
                  <main className="image-feed"><article className="image-result-card"><div className="image-result-meta"><p>动态模糊的定格，模糊人物瞬间运动轨迹。强烈的风感、低饱和色调、电影感光影、运动摄影。</p><span>图片生成 · 图片 4.5 · 1:1 · 高清 2K</span></div><div className="generated-grid">{[0, 1, 2, 3] .map((index: number) => (<button key={index} className="generated-image" onClick={() => setPreviewImageIndex(index)} type="button" />))}</div><div className="result-actions"><button type="button">重新编辑</button><button type="button">再次生成</button><button type="button">更多</button></div></article></main>
                  {imageLibraryOpen && <aside className="image-library-drawer"><div className="drawer-head"><strong>图片库</strong><button onClick={() => setImageLibraryOpen(false)} type="button">×</button></div><div className="drawer-grid">{[0, 1, 2, 3, 4, 5] .map((index: number) => (<button key={index} className="generated-image" onClick={() => setPreviewImageIndex(index)} type="button" />))}</div></aside>}
                  <div className="image-composer"><button className="upload-slot" type="button">＋</button><div className="image-composer-main">{referenceImageIndexes.length > 0 && <div className="reference-strip">{referenceImageIndexes.map((imageIndex: number, itemIndex: number) => (<div key={`${imageIndex}-${itemIndex}`} className="reference-thumb generated-image"><button onClick={() => setReferenceImageIndexes((items: number[]) => items.filter((_: number, index: number) => index !== itemIndex))} type="button">×</button></div>))}</div>}<textarea placeholder="描述你想生成的画面..." defaultValue="动态模糊的定格，模糊人物瞬间运动轨迹" /><div className="image-composer-tools"><button onClick={() => { setImageModelOpen((value: boolean) => !value); setImageSizeOpen(false); }} type="button">图片 4.5</button><button onClick={() => { setImageSizeOpen((value: boolean) => !value); setImageModelOpen(false); }} type="button">1:1 · 高清 2K</button><button type="button">4 张</button><span>消耗 200 积分/次</span></div>{imageModelOpen && <div className="image-popover image-model-popover model-menu"><div className="model-menu-title">内置模型</div><button className="model-menu-row selected" type="button"><span className="model-icon">✦</span><span className="model-name">图片 4.5</span><span className="model-badge">推荐</span><span className="model-brain">♧</span></button><button className="model-menu-row" type="button"><span className="model-icon">✦</span><span className="model-name">图片 4.0</span><span className="model-brain">♧</span></button><button className="model-menu-row" type="button"><span className="model-icon">◆</span><span className="model-name">写实增强</span><span className="model-brain">♧</span></button><button className="model-menu-row" type="button"><span className="model-icon">◆</span><span className="model-name">插画模型</span><span className="model-brain">♧</span></button><div className="model-menu-title custom">自定义模型</div><button className="model-menu-row" type="button"><span className="model-icon">◆</span><span className="model-name">Image-Pro:custom-image-pro</span><span className="model-brain">♧</span></button><button className="model-config-row" type="button">+ 配置自定义模型</button></div>}{imageSizeOpen && <div className="image-popover image-size-popover"><strong>选择比例</strong><div className="ratio-grid"><button type="button">21:9</button><button type="button">16:9</button><button type="button">3:2</button><button type="button">4:3</button><button className="active" type="button">1:1</button><button type="button">3:4</button><button type="button">2:3</button><button type="button">9:16</button></div><strong>选择分辨率</strong><div className="resolution-row"><button className="active" type="button">高清 2K</button><button type="button">超清 4K</button></div><div className="size-fields"><span>W 2048</span><span>H 2048</span><span>PX</span></div></div>}</div><button className="image-send" type="button">↑</button></div><button className="help-float" type="button">?</button>
                </section>
              ) : activePage === 'settings' ? (
                <section className="settings-page wb-settings">
                  <aside className="wb-settings-nav">
                    {settingsSections.map((section) => (
                      <button key={section} className={activeSettingsSection === section ? 'active' : ''} onClick={() => setActiveSettingsSection(section)} type="button">
                        <span className="settings-nav-icon">{section === '账户管理' ? <UserRound size={14} /> : section === '系统设置' ? <Settings2 size={14} /> : section === '智能体设置' ? <Bot size={14} /> : section === '记忆' ? <Brain size={14} /> : section === '模型' ? <Cpu size={14} /> : section === '软件配置' ? <FileStack size={14} /> : <HelpCircle size={14} />}</span>
                        <span>{section}</span>
                      </button>
                    ))}
                  </aside>
                  <main className="wb-settings-main">
                    <button className="settings-close" onClick={() => setActivePage('home')} type="button">×</button>
                    <h2>{activeSettingsSection}</h2>
                    <div className="settings-rule" />
    
                    {activeSettingsSection === '系统设置' && <div className="wb-setting-list"><div className="wb-setting-row"><div><strong>发送消息</strong><p>设置聊天输入框中发送消息的快捷键。</p></div><button className="select-button" type="button">Enter <ChevronDown size={14} /></button></div><div className="wb-setting-row"><div><strong>技能自动更新</strong><p>开启后将自动更新已安装的技能为最新版本。</p></div><button className="switch on" type="button"><span /></button></div><div className="wb-setting-row"><div><strong>沙箱安全</strong><p>保护您的数据，AI 对工作空间以外的修改和删除操作需要授权。</p></div><button className="switch on" type="button"><span /></button></div><div className="wb-path-row"><strong>默认工作空间存储路径</strong><p>新建任务、工作空间时将自动存放在该路径下。</p><div><span>C:\Users\user\KaiwuAI</span><button type="button">更改</button></div></div></div>}
    
                    {activeSettingsSection === '智能体设置' && <div className="wb-setting-list"><div className="wb-setting-row"><div><strong>禁用全部插件</strong><p>开启后禁用全部技能、MCP 和插件。当前状态：技能、MCP、插件可被正常使用。</p></div><button className="switch" type="button"><span /></button></div><div className="wb-setting-row"><div><strong>禁用智能体团队</strong><p>禁用后，智能体不会自动组建团队来完成任务。使用专家模式时可自动开启。</p></div><button className="switch" type="button"><span /></button></div></div>}
    
                    {activeSettingsSection === '记忆' && <div className="wb-setting-list"><p className="settings-desc">记忆让曜势科技记住你的偏好和习惯，对话越多，它就越懂你。</p><div className="wb-setting-row"><div><strong>生成对话记忆</strong><p>允许曜势科技从对话中提取并记住相关上下文，以便在未来对话中提供更连续、个性化的回应。</p></div><button className="switch on" type="button"><span /></button></div><div className="memory-card"><p>**工作背景** 用户正在开发"曜势科技"，这是一款面向 OPC 创业者的 0-1 创业产品。</p><div><strong>来自对话的记忆</strong><span>1 天前从对话中更新</span></div></div><div className="import-memory-row"><div><strong>从其他AI导入记忆</strong><p>一键同步你在其他 AI 上的使用习惯。</p></div><button type="button">导入</button></div></div>}
    
                    {activeSettingsSection === '模型' && <div className="wb-setting-list"><h3>自定义模型</h3><div className="wb-setting-row"><div><strong>本地配置文件</strong><p>管理写入到 %USERPROFILE%\.kaiwu\models.json 的本地自定义模型配置。</p></div><button type="button">+ 添加模型</button></div><h3>已保存模型</h3><div className="model-saved-row"><span>◆</span><div><strong>DeepSeek-V4 Pro</strong><p>深度求索</p></div><button type="button">⌕</button><button type="button">⌫</button></div></div>}
    
                    {activeSettingsSection === '软件配置' && <div className="wb-setting-list"><h3>工作空间依赖项</h3><div className="wb-setting-row"><div><strong>内置运行时</strong><p>允许使用随包提供的 Node.js、Python 和 Git Bash 工具。</p></div><button className="switch on" type="button"><span /></button></div><h3>运行时列表</h3><div className="runtime-table"><div><strong>工具</strong><strong>说明</strong><strong>状态</strong></div><div><span>🟢 Node.js</span><span>基于 Chrome V8 引擎的 JavaScript 运行时，用于服务端开发</span><button className="switch on" type="button"><span /></button></div><div><span>🐍 Python</span><span>通用编程语言，适用于脚本编写、自动化和数据处理</span><button className="switch on" type="button"><span /></button></div><div><span>🔶 Git Bash</span><span>在 Windows 上提供类 Unix 命令行环境</span><button className="switch on" type="button"><span /></button></div></div></div>}
    
                    {activeSettingsSection === '帮助与反馈' && <div className="wb-setting-list help-list"><button type="button"><span>▣ 帮助文档</span><span>↗</span></button><button type="button"><span>▤ 意见反馈</span></button><button type="button"><span>↔ 联系我们</span><span>↗</span></button><div className="policy-links">隐私政策　|　服务协议</div></div>}
    
                    {activeSettingsSection === '账户管理' && <div className="wb-setting-list"><div className="account-profile-card"><div className="account-large-avatar">曜</div><div><strong>OPC创业者</strong><p>曜势科技 创业工作区账户</p></div><button type="button">更换头像</button></div><div className="wb-setting-row"><div><strong>账户名称</strong><p>用于侧边栏、项目协作和对话归档显示。</p></div><button type="button">OPC创业者</button></div><div className="wb-setting-row"><div><strong>登录密码</strong><p>定期更新密码以保护创业项目资料和生成图片比例。</p></div><button type="button">修改密码</button></div><div className="wb-setting-row"><div><strong>绑定邮箱</strong><p>op****@kaiwu.ai</p></div><button type="button">更换邮箱</button></div></div>}
                  </main>
                </section>
              ) : activePage === 'skills' ? (
                <SkillLibraryPage
                  activeSkillCategory={activeSkillCategory}
                  enabledSkillIds={enabledSkillIds}
                  installedSkillIds={installedSkillIds}
                  setActiveSkillCategory={setActiveSkillCategory}
                  setSkillModal={setSkillModal}
                  setSkillModalData={setSkillModalData}
                  setSkillSearchQuery={setSkillSearchQuery}
                  setSkillView={setSkillView}
                  skillItems={skillItems}
                  skillSearchQuery={skillSearchQuery}
                  skillView={skillView}
                />
              ) : activePage === 'projects' ? (
                <section className="library-page project-page">
                  <header className="library-header">
                    <div>
                      <div className="settings-kicker">Project Files</div>
                      <h2>{projectView === 'home' ? '项目库' : projectView === 'folder' ? projectFolders[selectedFolderIndex].name : projectView === 'ai' ? 'AI 产出文件' : '我上传的文件'}</h2>
                      <p>{projectView === 'home' ? '集中管理 AI 对话产出的文件和你在项目中创建、上传的资料。' : '管理项目文件、文件夹和资料来源。'}</p>
                    </div>
                    <div className="project-actions">
                      <button className="secondary-action" onClick={() => setProjectModal('new-folder')} type="button">新建文件夹</button>
                      <button className="primary-action" onClick={() => setProjectModal('upload')} type="button">上传文件</button>
                    </div>
                  </header>
                  <div className="library-toolbar">
                    <div className="library-search"><Search size={15} /><span>搜索文件夹、文档、表格、AI 产出...</span></div>
                    <div className="library-tabs"><button className={projectView === 'home' ? 'active' : ''} onClick={() => setProjectView('home')} type="button">全部文件</button><button className={projectView === 'ai' ? 'active' : ''} onClick={() => setProjectView('ai')} type="button">AI 产出</button><button className={projectView === 'uploaded' ? 'active' : ''} onClick={() => setProjectView('uploaded')} type="button">我上传的</button></div>
                  </div>
                  {projectView === 'home' && <section className="project-section"><div className="section-title-row"><h3>文件夹</h3><span>点击文件夹弹窗查看文件</span></div><div className="folder-grid">{projectFolders.map((folder, index) => (<button key={folder.name} className={`folder-card tone-${folder.tone}`} onClick={() => { setSelectedFolderIndex(index); setProjectModal('folder-detail'); }} type="button"><div className="folder-icon">▣</div><div><h3>{folder.name}</h3><p>{folder.desc}</p><span>{(() => { const c = folder.name === '图片库' ? projectImages.length : realProjectFiles.filter((f: { folder: string }) => f.folder === folder.name).length; return `${c} 个文件`; })()}</span></div></button>))}</div></section>}
                  <section className="project-section"><div className="section-title-row"><h3>{projectView === 'ai' ? 'AI 产出文件' : projectView === 'uploaded' ? '我上传的文件' : '最近文件'}</h3><span>点击文件弹窗查看详情</span></div><div className="file-table">
                    {/* Real project files */}
                    {realProjectFiles.length > 0 && realProjectFiles.map((file: { name: string; folder: string; type: string; modified: string; url: string }, i: number) => (
                      <button key={`real-${i}`} className="file-row" onClick={() => openProjectFile(file)} type="button">
                        <span style={{display:'inline-grid',placeItems:'center',borderRadius:'9px',color:'#334155',fontSize:'11px',fontWeight:700,background:'rgba(15,23,42,0.06)',height:'28px',padding:'0 8px',margin:'0 10px'}}>{file.type}</span>
                        <span className="file-main"><strong>{file.name}</strong><small>{file.folder} · {file.modified}</small></span>
                        <span className="file-updated">{file.modified}</span>
                        <span className="file-action">查看</span>
                      </button>
                    ))}
                    {projectLibraryFiles.filter((file) => projectView === 'ai' ? file.source.includes('AI') : projectView === 'uploaded' ? file.source.includes('上传') : true).map((file) => { const fileIndex = projectLibraryFiles.findIndex((item) => item.name === file.name); return (<button key={file.name} className="file-row" onClick={() => { setSelectedFileIndex(fileIndex); setProjectModal('file-detail'); }} type="button"><span className={`file-type tone-${file.tone}`}>{file.type}</span><span className="file-main"><strong>{file.name}</strong><small>{file.folder} · {file.source}</small></span><span className="file-updated">{file.updated}</span><span className="file-action">查看详情</span></button>); })}
                  </div></section>
                </section>
              ) : (
                <>
              <section className="hero-area">
                <div className="hero-copy-block">
                  <div className="hero-mark" aria-hidden="true">
                    <div className="hero-wordmark hero-wordmark-back">曜势</div>
                    <div className="hero-wordmark hero-wordmark-front">曜势</div>
                  </div>
                  <h1>
                    <span className="hero-typed">{typedHeroText || ' '}</span>
                    <span className="hero-caret" aria-hidden="true" />
                  </h1>
                </div>
              </section>
    
              <section className="composer-area">
                <div className="composer-stack">
                  <div className="venture-track" aria-label="创业阶段轨道">
                    <div className="track-line" />
                    {directions.map((item, index) => {
                      const isOffice = item === '通用';
                      const stepNumber = isOffice ? '通用' : index;
                      const displayLabel = isOffice ? '日常办公' : item;
                      return (
                        <button
                          key={item}
                          className={`${activeDirection === item ? 'track-node active' : 'track-node'} ${isOffice ? 'office-node' : 'venture-node'}`}
                          onClick={() => setActiveDirection(item)}
                          type="button"
                        >
                          <span className="node-dot">{stepNumber}</span>
                          <span className="node-label">{displayLabel}</span>
                        </button>
                      );
                    })}
                  </div>
    
                  {/* 已上传文件标签（首页） */}
                  {uploadedFiles.length > 0 && (
                    <div className="uploaded-files-bar">
                      {uploadedFiles.map((f: { name: string }, i: number) => (
                        <span key={i} className="uploaded-file-tag">
                          <span className="file-tag-icon">📄</span>
                          <span className="file-tag-name">{f.name}</span>
                          <button className="file-tag-close" onClick={() => removeUploadedFile(f.name)} type="button" title="移除文件">×</button>
                        </span>
                      ))}
                    </div>
                  )}
    
                  <div className="composer-card">
                    <textarea ref={homeTextareaRef} placeholder="描述你的创业想法、目标用户、当前卡点，曜势会帮你拆成可执行方案..." onChange={(e) => setInputText(e.target.value)} onCompositionStart={() => { isComposingRef.current = true; }} onCompositionEnd={() => { isComposingRef.current = false; }} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey && !isComposingRef.current) { e.preventDefault(); handleSend(); } else if (e.key === 'Enter' && e.ctrlKey) { e.preventDefault(); handleSend(); } }} />
                    <div className="skill-row in-composer">
                      {quickSkills.map((item: string) => (
                        <button key={item} className="skill-chip">
                          {item}
                        </button>
                      ))}
                    </div>
                    <div className="composer-toolbar">
                      <div className="toolbar-left">
                        <div className="picker-wrap">
                          <button
                            className={openPicker === 'model' ? 'toolbar-select model-select is-active' : 'toolbar-select model-select'}
                            onClick={() => setOpenPicker(openPicker === 'model' ? null : 'model')}
                            type="button"
                          >
                            <Bot size={14} />
                            <span>{modelOptions[modelIndex].name}</span>
                            <ChevronDown size={13} />
                          </button>
                          {openPicker === 'model' && (
                            <div className="picker-popover">
                              {modelOptions.map((item, index) => (
                                <button
                                  key={item.name}
                                  className={modelIndex === index ? 'model-menu-row selected' : 'model-menu-row'}
                                  onClick={() => {
                                    setModelIndex(index);
                                    setOpenPicker(null);
                                  }}
                                  type="button"
                                >
                                  <span className="model-icon">✦</span>
                                  <span className="model-name">{item.name}</span>
                                  <span className="model-desc">{item.desc}</span>
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
    
                        <div className="picker-wrap">
                          <button
                            className={libraryModal === 'file' || fileIndex !== null ? 'toolbar-select is-active-soft' : 'toolbar-select'}
                            onClick={() => {
                              setOpenPicker(null);
                              setLibraryModal('file');
                              const aiIdx = projectFolders.findIndex(f => f.name === 'AI 对话产出');
                              if (aiIdx >= 0) setSelectedFolderIndex(aiIdx);
                            }}
                            type="button"
                          >
                            <span>📂</span>
                            <span>参考历史文件</span>
                            <ChevronDown size={13} />
                          </button>
                        </div>
    
                      </div>
                      <div className="toolbar-right">
                        <button className={`icon-action send-action ${isLoading ? 'send-disabled' : ''}`} aria-label="发送" title="发送" onClick={handleSend} disabled={isLoading} type="button">
                          <ArrowUp size={17} />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
    
                <div className="footer-note">内容由 AI 生成，请核实完整性</div>
              </section>
                </>
              )}
            </main>
  );
}

