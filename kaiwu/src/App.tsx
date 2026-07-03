/**
 * =============================================================================
 * # 角色
 * 主组件层 —— 曜势科技 App 的根组件。
 * 担任整个应用的 orchestration 职责：管理全部 UI 状态、处理对话流、
 * SSE 流式响应、会话缓存、路由切换、文件管理与技能市场交互。
 * 面向 OPC 创业者，提供从需求调研到营销推广的四阶段创业支撑。
 *
 * # 输入
 * ## 1. 外部数据源
 * - http://localhost:5001/api/conversations —— 对话历史列表
 * - http://localhost:5001/api/skills —— 外部技能列表
 * - http://localhost:5001/api/project-images —— 项目图片库
 * - http://localhost:5001/api/project-files —— 项目文件库
 *
 * ## 2. 用户交互
 * - 文本输入（创业想法 / 追问 / 指令）
 * - 赛道选择（通用 / 需求洞察 / 商业方案 / 产品创造 / 营销推广）
 * - 模型切换（开物深思 / 开物极速 / 开物研究）
 * - 技能安装 / 文件管理 / 设置修改
 *
 * ## 3. 静态数据
 * - data.ts 提供的全部业务配置常量
 * - types.ts 提供的类型约束
 * - utils.ts 提供的 renderMarkdown 函数
 *
 * # 输出结构
 * ## 1. 页面路由（activePage 驱动）
 * | 页面标识 | 对应界面 | 说明 |
 * |---------|---------|------|
 * | home    | 首页 + 对话区 | 赛道选择 + 输入框 + 对话流 |
 * | skills  | 技能库 | 技能市场 / 已安装技能管理 |
 * | projects | 项目库 | 文件夹 + 文件列表 + 上传 |
 * | settings | 设置页 | 7 个设置标签页 |
 * | image   | AI 生图 | 图片生成工作台 |
 * | video   | AI 视频 | 视频生成工作台 |
 * | coding  | AI 编程 | 代码编辑器 + 预览 |
 *
 * ## 2. 对话引擎
 * - SSE 流式响应处理（analyzing → executing → responding）
 * - 节点进度展示（nodeStatus 进度条 + 动画）
 * - 会话缓存（convCacheRef 跨切换保活）
 * - 停止生成 / 保存会话 / 加载历史
 *
 * ## 3. 模态框系统
 * | 模态框类型 | 触发场景 |
 * |-----------|---------|
 * | skillModal | 技能详情 / 安装 / 管理 / 自定义 / 外部技能 |
 * | projectModal | 新建文件夹 / 上传 / 文件夹详情 / 文件详情 |
 * | libraryModal | 文件选择器 / 技能选择器 |
 * | rechargeModal | 积分充值 / 套餐升级 |
 * | previewImageModal | 图片预览 + 导入参考图 |
 *
 * ## 4. 核心状态一览
 * | 状态变量 | 类型 | 用途 |
 * |---------|------|------|
 * | activePage | SidebarPage | 当前页面路由 |
 * | activeDirection | Direction | 当前赛道方向 |
 * | conversationOpen | boolean | 是否显示对话界面 |
 * | messages | Message[] | 对话消息列表 |
 * | isLoading | boolean | 是否正在请求 AI |
 * | workflowPhase | string | SSE 工作流阶段 |
 * | sidebarCollapsed | boolean | 侧边栏折叠状态 |
 * =============================================================================
 */

import { useEffect, useRef, useState } from 'react';

import type {
  ConvHistory,
  Direction,
  SettingsSection,
  SidebarPage,
  ProjectView,
  ProjectModal,
  SkillView,
  SkillModal,
  SkillCategory,
  PickerType,
  LibraryModalType,
  SkillLibraryItem,
} from './types';
import {
  quickSkillsByDirection,
  modelOptions,
  heroText,
} from './data';
import { AppSidebar } from './features/layout/AppSidebar';
import { AppModals } from './features/layout/AppModals';
import { MainStage } from './features/layout/MainStage';
import { type AgentMessage } from './hooks/agentEventReducer';
import { useConversation } from './hooks/useConversation';
import { useConversationTask, type ConversationTaskCacheEntry } from './hooks/useConversationTask';
import { useSkillLibrary } from './hooks/useSkillLibrary';

// =============================================================================
// App Component
// =============================================================================

export function App() {
  // ---- State ----
  const [modelIndex, setModelIndex] = useState(0);
  const [fileIndex, setFileIndex] = useState<number | null>(null);
  const [skillIndex, setSkillIndex] = useState<number | null>(null);
  const [openPicker, setOpenPicker] = useState<PickerType>(null);
  const [libraryModal, setLibraryModal] = useState<LibraryModalType>(null);
  const [activeDirection, setActiveDirection] = useState<Direction>('通用');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [typedHeroText, setTypedHeroText] = useState('');
  const [activeSettingsSection, setActiveSettingsSection] = useState<SettingsSection>('系统设置');
  const [activePage, setActivePage] = useState<SidebarPage>('home');
  const [projectView, setProjectView] = useState<ProjectView>('home');
  const [projectModal, setProjectModal] = useState<ProjectModal>(null);
  const [selectedFolderIndex, setSelectedFolderIndex] = useState(0);
  const [selectedFileIndex, setSelectedFileIndex] = useState(0);
  const [skillView, setSkillView] = useState<SkillView>('market');
  const [skillModal, setSkillModal] = useState<SkillModal>(null);
  const [skillModalData, setSkillModalData] = useState<SkillLibraryItem | null>(null);
  const [activeSkillCategory, setActiveSkillCategory] = useState<SkillCategory>('全部');
  const [expertExpanded, setExpertExpanded] = useState(false);
  const [imageLibraryOpen, setImageLibraryOpen] = useState(false);
  const [imageModelOpen, setImageModelOpen] = useState(false);
  const [imageSizeOpen, setImageSizeOpen] = useState(false);
  const [videoLibraryOpen, setVideoLibraryOpen] = useState(false);
  const [videoModelOpen, setVideoModelOpen] = useState(false);
  const [videoSettingOpen, setVideoSettingOpen] = useState(false);
  const [codingMode, setCodingMode] = useState<'preview' | 'code'>('preview');
  const [codingModelOpen, setCodingModelOpen] = useState(false);
  const [previewImageIndex, setPreviewImageIndex] = useState<number | null>(null);
  const [referenceImageIndexes, setReferenceImageIndexes] = useState<number[]>([]);
  const [openHistoryMenu, setOpenHistoryMenu] = useState<number | null>(null);
  const [conversationOpen, setConversationOpen] = useState(false);
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const [rechargeModalOpen, setRechargeModalOpen] = useState(false);
  const [rechargeView, setRechargeView] = useState<'credits' | 'plans'>('credits');
  const [convHistory, setConvHistory] = useState<ConvHistory[]>([]);
  const [currentConvId, setCurrentConvId] = useState<number | null>(null);
  const [projectImages, setProjectImages] = useState<{ name: string; url: string; size: number; modified: string }[]>([]);
  const [realProjectFiles, setRealProjectFiles] = useState<{ name: string; folder: string; type: string; size: number; modified: string; url: string }[]>([]);
  const [codingPreviewUrl, setCodingPreviewUrl] = useState<string>('');
  const [imageRatio, setImageRatio] = useState<string>('1:1');
  const [imageCount, setImageCount] = useState<number>(1);
  const [ratioOpen, setRatioOpen] = useState(false);
  const [countOpen, setCountOpen] = useState(false);
  const [isImageMode, setIsImageMode] = useState(false);
  const [suggestedQuestions, _setSuggestedQuestions] = useState<string[]>([]);
  const suggestedQuestionsRef = useRef<string[]>([]);
  const setSuggestedQuestions = (val: string[]) => { suggestedQuestionsRef.current = val; _setSuggestedQuestions(val); };
  const [activeNodeId, setActiveNodeId] = useState('');
  const [inputText, setInputText] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<{name:string,size:number}[]>([]);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationTitle, setConversationTitle] = useState('新对话');
  const [nodeStatus, setNodeStatus] = useState<{ nodeId: string; nodeName: string; nodeIcon: string; progress: number; message: string } | null>(null);
  const [workflowPhase, setWorkflowPhase] = useState<'idle' | 'analyzing' | 'executing' | 'responding'>('idle');

  const {
    enabledSkillIds,
    installedSkillIds,
    installSkill,
    saveCustomSkill,
    setSkillSearchQuery,
    skillItems,
    skillSearchQuery,
    toggleSkillEnabled,
    uninstallSkill,
  } = useSkillLibrary();

  // ---- Refs ----
  const homeTextareaRef = useRef<HTMLTextAreaElement>(null);
  const convTextareaRef = useRef<HTMLTextAreaElement>(null);
  const convIdRef = useRef<number | null>(null);
  const followupNodeRef = useRef<string | null>(null);
  const isComposingRef = useRef(false);
  const sseConvIdRef = useRef<number | null>(null);
  const convCacheRef = useRef<Map<number, ConversationTaskCacheEntry>>(new Map());

  const quickSkills = quickSkillsByDirection[activeDirection];
  const { handleSend, stopGeneration } = useConversationTask({
    homeTextareaRef,
    convTextareaRef,
    convIdRef,
    followupNodeRef,
    sseConvIdRef,
    suggestedQuestionsRef,
    convCacheRef,
    inputText,
    isLoading,
    messages,
    activeNodeId,
    conversationTitle,
    imageRatio,
    imageCount,
    modelId: modelOptions[modelIndex].id,
    setInputText,
    setSuggestedQuestions,
    setMessages,
    setConversationOpen,
    setConversationTitle,
    setIsLoading,
    setWorkflowPhase,
    setNodeStatus,
    setActiveNodeId,
    setCurrentConvId,
    setConvHistory,
    setProjectImages,
    setActivePage,
    setCodingMode,
  });
  const {
    deleteConversation,
    loadConversation,
    openHomeConversation,
    renameConversation,
    resetConversation,
  } = useConversation({
    activePage,
    currentConvId,
    messages,
    isLoading,
    workflowPhase,
    nodeStatus,
    conversationTitle,
    convIdRef,
    sseConvIdRef,
    suggestedQuestionsRef,
    convCacheRef,
    setMessages,
    setIsLoading,
    setWorkflowPhase,
    setNodeStatus,
    setConversationOpen,
    setConversationTitle,
    setCurrentConvId,
    setIsImageMode,
    setSuggestedQuestions,
    setActiveNodeId,
    setActivePage,
    setInputText,
    setConvHistory,
    setOpenHistoryMenu,
  });

  // ---- Effects ----
  // Auto-scroll to bottom
  useEffect(() => {
    const el = document.getElementById('doubao-messages');
    if (!el) return;
    const selection = window.getSelection();
    if (selection && selection.toString().length > 0) return;
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
    if (isNearBottom) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages]);

  // Close history menu on outside click
  useEffect(() => {
    if (openHistoryMenu === null) return;
    const handler = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('.history-menu-popover') && !target.closest('.history-menu-button')) {
        setOpenHistoryMenu(null);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [openHistoryMenu]);

  // Close popovers on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('.picker-popover') && !target.closest('.toolbar-select')) {
        setOpenPicker(null);
        setRatioOpen(false);
        setCountOpen(false);
      }
    };
    document.addEventListener('click', handler);
    return () => document.removeEventListener('click', handler);
  }, []);

  // Load uploaded files on mount
  useEffect(() => {
    fetch('http://localhost:5001/api/uploaded-files')
      .then(r => r.json()).then(d => d.files && setUploadedFiles(d.files)).catch(()=>{});
  }, []);

  const removeUploadedFile = (name: string) => {
    fetch(`http://localhost:5001/api/uploaded-files/${encodeURIComponent(name)}`, {method:'DELETE'})
      .then(r => r.json()).then(() => setUploadedFiles(prev => prev.filter(f => f.name !== name))).catch(()=>{});
  };

  // Load project images
  useEffect(() => {
    fetch('http://localhost:5001/api/project-images')
      .then((r) => r.json())
      .then((data) => setProjectImages(data))
      .catch(() => {});
  }, [messages.length]);

  // Load real project files
  useEffect(() => {
    fetch('http://localhost:5001/api/project-files')
      .then((r) => r.json())
      .then((data) => setRealProjectFiles(data))
      .catch(() => {});
  }, [messages.length, projectModal]);

  // Typing effect for hero text
  useEffect(() => {
    let index = 0;
    let deleting = false;
    let timeoutId: number | undefined;

    const tick = () => {
      if (!deleting) {
        index += 1;
        setTypedHeroText(heroText.slice(0, index));
        if (index === heroText.length) {
          deleting = true;
          timeoutId = window.setTimeout(tick, 1600);
          return;
        }
        timeoutId = window.setTimeout(tick, heroText[index - 1] === '\n' ? 260 : 58);
        return;
      }

      index -= 1;
      setTypedHeroText(heroText.slice(0, index));
      if (index === 0) {
        deleting = false;
        timeoutId = window.setTimeout(tick, 480);
        return;
      }
      timeoutId = window.setTimeout(tick, 24);
    };

    timeoutId = window.setTimeout(tick, 520);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, []);

  const openProjectFile = (file: { name: string; folder: string; type: string; url: string }) => {
    if (file.type === 'HTML') {
      setCodingPreviewUrl(file.url);
      setCodingMode('preview');
      setActivePage('coding');
      setProjectModal(null);
    } else {
      window.open(file.url, '_blank');
    }
  };

  // =============================================================================
  // Render
  // =============================================================================

  return (
    <div className="desktop-app">
      <div className={sidebarCollapsed ? 'shell sidebar-collapsed' : 'shell'}>
        {!sidebarCollapsed && (
          <AppSidebar
            accountMenuOpen={accountMenuOpen}
            activePage={activePage}
            convHistory={convHistory}
            deleteConversation={deleteConversation}
            expertExpanded={expertExpanded}
            loadConversation={loadConversation}
            openHistoryMenu={openHistoryMenu}
            openHomeConversation={openHomeConversation}
            renameConversation={renameConversation}
            resetConversation={resetConversation}
            setAccountMenuOpen={setAccountMenuOpen}
            setActivePage={setActivePage}
            setConversationOpen={setConversationOpen}
            setExpertExpanded={setExpertExpanded}
            setOpenHistoryMenu={setOpenHistoryMenu}
            setRechargeModalOpen={setRechargeModalOpen}
            setSidebarCollapsed={setSidebarCollapsed}
          />
        )}

        <MainStage
          activeDirection={activeDirection}
          activeNodeId={activeNodeId}
          activePage={activePage}
          activeSettingsSection={activeSettingsSection}
          activeSkillCategory={activeSkillCategory}
          codingMode={codingMode}
          codingModelOpen={codingModelOpen}
          codingPreviewUrl={codingPreviewUrl}
          conversationOpen={conversationOpen}
          conversationTitle={conversationTitle}
          convTextareaRef={convTextareaRef}
          countOpen={countOpen}
          enabledSkillIds={enabledSkillIds}
          fileIndex={fileIndex}
          followupNodeRef={followupNodeRef}
          handleSend={handleSend}
          homeTextareaRef={homeTextareaRef}
          imageCount={imageCount}
          imageLibraryOpen={imageLibraryOpen}
          imageModelOpen={imageModelOpen}
          imageRatio={imageRatio}
          imageSizeOpen={imageSizeOpen}
          inputText={inputText}
          installedSkillIds={installedSkillIds}
          isComposingRef={isComposingRef}
          isImageMode={isImageMode}
          isLoading={isLoading}
          libraryModal={libraryModal}
          messages={messages}
          modelIndex={modelIndex}
          nodeStatus={nodeStatus}
          openPicker={openPicker}
          openProjectFile={openProjectFile}
          projectImages={projectImages}
          projectView={projectView}
          quickSkills={quickSkills}
          ratioOpen={ratioOpen}
          realProjectFiles={realProjectFiles}
          referenceImageIndexes={referenceImageIndexes}
          removeUploadedFile={removeUploadedFile}
          resetConversation={resetConversation}
          selectedFolderIndex={selectedFolderIndex}
          setActiveDirection={setActiveDirection}
          setActivePage={setActivePage}
          setActiveSettingsSection={setActiveSettingsSection}
          setActiveSkillCategory={setActiveSkillCategory}
          setCodingMode={setCodingMode}
          setCodingModelOpen={setCodingModelOpen}
          setConversationOpen={setConversationOpen}
          setCountOpen={setCountOpen}
          setImageCount={setImageCount}
          setImageLibraryOpen={setImageLibraryOpen}
          setImageModelOpen={setImageModelOpen}
          setImageRatio={setImageRatio}
          setImageSizeOpen={setImageSizeOpen}
          setInputText={setInputText}
          setLibraryModal={setLibraryModal}
          setModelIndex={setModelIndex}
          setOpenPicker={setOpenPicker}
          setPreviewImageIndex={setPreviewImageIndex}
          setProjectModal={setProjectModal}
          setProjectView={setProjectView}
          setRatioOpen={setRatioOpen}
          setReferenceImageIndexes={setReferenceImageIndexes}
          setSelectedFileIndex={setSelectedFileIndex}
          setSelectedFolderIndex={setSelectedFolderIndex}
          setSkillModal={setSkillModal}
          setSkillModalData={setSkillModalData}
          setSkillSearchQuery={setSkillSearchQuery}
          setSkillView={setSkillView}
          setSidebarCollapsed={setSidebarCollapsed}
          setSuggestedQuestions={setSuggestedQuestions}
          setVideoLibraryOpen={setVideoLibraryOpen}
          setVideoModelOpen={setVideoModelOpen}
          setVideoSettingOpen={setVideoSettingOpen}
          sidebarCollapsed={sidebarCollapsed}
          skillItems={skillItems}
          skillSearchQuery={skillSearchQuery}
          skillView={skillView}
          stopGeneration={stopGeneration}
          suggestedQuestions={suggestedQuestions}
          typedHeroText={typedHeroText}
          uploadedFiles={uploadedFiles}
          videoLibraryOpen={videoLibraryOpen}
          videoModelOpen={videoModelOpen}
          videoSettingOpen={videoSettingOpen}
        />
      </div>

      <AppModals
        enabledSkillIds={enabledSkillIds}
        fileIndex={fileIndex}
        installSkill={installSkill}
        installedSkillIds={installedSkillIds}
        libraryModal={libraryModal}
        openProjectFile={openProjectFile}
        previewImageIndex={previewImageIndex}
        projectImages={projectImages}
        projectModal={projectModal}
        realProjectFiles={realProjectFiles}
        rechargeModalOpen={rechargeModalOpen}
        rechargeView={rechargeView}
        selectedFileIndex={selectedFileIndex}
        selectedFolderIndex={selectedFolderIndex}
        saveCustomSkill={saveCustomSkill}
        setFileIndex={setFileIndex}
        setLibraryModal={setLibraryModal}
        setPreviewImageIndex={setPreviewImageIndex}
        setProjectModal={setProjectModal}
        setRechargeModalOpen={setRechargeModalOpen}
        setRechargeView={setRechargeView}
        setReferenceImageIndexes={setReferenceImageIndexes}
        setSkillIndex={setSkillIndex}
        setSkillModal={setSkillModal}
        setSkillModalData={setSkillModalData}
        skillIndex={skillIndex}
        skillModal={skillModal}
        skillModalData={skillModalData}
        toggleSkillEnabled={toggleSkillEnabled}
        uninstallSkill={uninstallSkill}
      />
    </div>
  );
}


