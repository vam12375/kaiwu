import { ArrowLeft, ArrowUp, Bot, Brain, ChevronDown, ChevronRight, Cpu, Download, ExternalLink, FileStack, FileText, HelpCircle, ImageIcon, Search, Settings2, UserRound } from 'lucide-react';

import { useEffect, useState } from 'react';
import { Check, Pencil, Trash2 } from 'lucide-react';
import { directions, modelOptions, settingsSections } from '../../data';
import { ConversationPanel } from '../chat/ConversationPanel';
import { SkillLibraryPage } from './SkillLibraryPage';
import { ProjectImagePreviewModal } from './ProjectImagePreviewModal';
import { ProjectLazyImage } from './ProjectLazyImage';
import { BrandHeader } from '../home/BrandHeader';
import { ChatInput } from '../home/ChatInput';
import { WorkflowSteps } from '../home/WorkflowSteps';
import { FeatureCards } from '../home/FeatureCards';
import { FreeMode } from '../home/FreeMode';
import type { ProjectImage } from '../../types';
import '../../styles/layout/main-stage.css';
import '../../styles/home/home-stage.css';
import '../../styles/project/project-gallery.css';
import '../../styles/project/project-file-detail.css';
import '../../styles/project/project-library.css';
import '../../styles/creative/creative-page.css';
import '../../styles/creative/creative-workspaces.css';
import '../../styles/coding/coding.css';
import '../../styles/settings/settings-page.css';
import '../../styles/settings/settings-workbench.css';

type MainStageProps = Record<string, any>;

const RECENT_PROJECT_FILES_LIMIT = 10;
const PROJECT_FILE_FRAME_PREVIEW_TYPES = new Set(['HTML', 'HTM', 'PDF', 'TXT', 'MD', 'CSV', 'JSON']);
const PROJECT_FILE_IMAGE_PREVIEW_TYPES = new Set(['JPG', 'JPEG', 'PNG', 'WEBP', 'GIF', 'BMP', 'AVIF', 'SVG']);

type ProjectFileLike = {
  name: string;
  folder: string;
  type: string;
  modified: string;
  url: string;
  source?: string;
  size?: number;
};

function formatProjectFileSize(size?: number) {
  if (typeof size !== 'number') return '未知大小';
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

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
    imageModel,
    imageModelOpen,
    imageRatio,
    imageResolution,
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
    deleteProjectFolders,
    deleteProjectFile,
    deleteProjectFiles,
    deleteProjectImages,
    projectFolders,
    projectImages,
    projectSearchQuery,
    projectView,
    quickSkills,
    ratioOpen,
    realProjectFiles,
    refreshProjectFiles,
    referenceImageIndexes,
    removeUploadedFile,
    resetConversation,
    selectedFolderIndex,
    selectedProjectFile,
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
    setImageModel,
    setImageModelOpen,
    setImageRatio,
    setImageResolution,
    setImageSizeOpen,
    setInputText,
    setLibraryModal,
    setModelIndex,
    setOpenPicker,
    setPreviewImageIndex,
    setProjectModal,
    setProjectFolderEditTarget,
    setProjectFileEditTarget,
    setProjectUploadTargetFolder,
    setProjectSearchQuery,
    setSelectedProjectFile,
    setProjectView,
    setRatioOpen,
    setReferenceImageIndexes,
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
    selectedCardImage,
    setSelectedCardImage,
    selectedComposerSkill,
    setSelectedComposerSkill,
    showToast,
  } = props;

  const [folderEditMode, setFolderEditMode] = useState(false);
  const [selectedProjectFolderNames, setSelectedProjectFolderNames] = useState<string[]>([]);
  const [folderDetailEditMode, setFolderDetailEditMode] = useState(false);
  const [selectedProjectImageNames, setSelectedProjectImageNames] = useState<string[]>([]);
  const [selectedProjectFileKeys, setSelectedProjectFileKeys] = useState<string[]>([]);
  const [projectImagePreviewIndex, setProjectImagePreviewIndex] = useState<number | null>(null);
  const activeProjectFolder = projectFolders[selectedFolderIndex] || projectFolders[0];
  const activeProjectFolderId = activeProjectFolder?.id || activeProjectFolder?.name;
  const isImageLibraryFolder = activeProjectFolder?.kind === 'image_library' || activeProjectFolderId === '图片库' || activeProjectFolder?.name === '图片库';
  const projectQuery = projectSearchQuery.trim().toLocaleLowerCase();
  const matchesProjectName = (name: string) => !projectQuery || name.toLocaleLowerCase().includes(projectQuery);
  const visibleProjectFolders = projectFolders.filter((folder: { name: string }) => matchesProjectName(folder.name));
  const visibleProjectFolderNames = visibleProjectFolders.map((folder: { name: string; id?: string }) => folder.id || folder.name);
  const visibleProjectFolderKey = visibleProjectFolderNames.join('|');
  const visibleRealProjectFiles = realProjectFiles
    .filter((file: { folder: string; name: string; source?: string }) => {
      if (projectView === 'folder') return activeProjectFolder && file.folder === activeProjectFolderId;
      if (projectView === 'ai') return file.source === 'ai' || file.folder === 'AI 对话产出';
      if (projectView === 'uploaded') return file.source === 'manual_upload';
      return true;
    })
    .filter((file: { name: string }) => matchesProjectName(file.name));
  const projectFileTableItems = projectView === 'home'
    ? visibleRealProjectFiles.slice(0, RECENT_PROJECT_FILES_LIMIT)
    : visibleRealProjectFiles;
  const visibleProjectImages = projectImages.filter((image: ProjectImage) => matchesProjectName(image.name));
  const visibleProjectImageKey = visibleProjectImages.map((image: ProjectImage) => image.name).join('|');
  const projectFileKey = (file: ProjectFileLike) => `${file.folder}/${file.name}`;
  const visibleProjectFileKey = visibleRealProjectFiles.map((file: ProjectFileLike) => projectFileKey(file)).join('|');
  const selectedFolderDetailItemCount = isImageLibraryFolder ? selectedProjectImageNames.length : selectedProjectFileKeys.length;
  const selectedProjectFileType = selectedProjectFile?.type?.toUpperCase() || '';
  const canPreviewSelectedProjectFileAsFrame = PROJECT_FILE_FRAME_PREVIEW_TYPES.has(selectedProjectFileType);
  const canPreviewSelectedProjectFileAsImage = PROJECT_FILE_IMAGE_PREVIEW_TYPES.has(selectedProjectFileType);
  const getProjectFileSourceLabel = (file: { source?: string; folder: string }) => {
    if (file.source === 'manual_upload') return '手动上传';
    if (file.source === 'ai' || file.folder === 'AI 对话产出') return 'AI 对话产出';
    return '项目文件';
  };
  const projectHeaderTitle = projectView === 'home'
    ? '项目库'
    : projectView === 'folder'
      ? activeProjectFolder?.name
      : projectView === 'ai'
        ? 'AI 产出文件'
        : projectView === 'uploaded'
          ? '我上传的文件'
          : selectedProjectFile?.name || '文件详情';
  const projectHeaderDescription = projectView === 'home'
    ? '集中管理 AI 对话产出的文件和你在项目中创建、上传的资料。'
    : projectView === 'detail'
      ? '查看文件预览、来源信息和快捷操作。'
      : '管理项目文件、文件夹和资料来源。';
  const returnToProjectLibrary = () => {
    setSelectedProjectFile?.(null);
    setProjectView('home');
  };
  const openSelectedProjectFile = () => {
    if (!selectedProjectFile) return;
    window.open(selectedProjectFile.url, '_blank', 'noopener,noreferrer');
  };
  const downloadSelectedProjectFile = () => {
    if (!selectedProjectFile) return;
    fetch(selectedProjectFile.url)
      .then((response) => response.blob())
      .then((blob) => {
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = selectedProjectFile.name;
        link.click();
        URL.revokeObjectURL(link.href);
        showToast?.({ message: '文件已开始下载', variant: 'success' });
      })
      .catch(() => {
        showToast?.({ message: '下载失败，已尝试新窗口打开', variant: 'error' });
        openSelectedProjectFile();
      });
  };
  const useSkillInComposer = (skill: any) => {
    setSelectedComposerSkill?.(skill);
    setConversationOpen(false);
    setActivePage('home');
    window.setTimeout(() => {
      homeTextareaRef.current?.focus();
    }, 0);
  };
  const toggleProjectFolderSelection = (folderName: string) => {
    setSelectedProjectFolderNames((current) => (
      current.includes(folderName)
        ? current.filter((name) => name !== folderName)
        : [...current, folderName]
    ));
  };
  const cancelProjectFolderEdit = () => {
    setFolderEditMode(false);
    setSelectedProjectFolderNames([]);
  };
  const handleDeleteSelectedProjectFolders = async () => {
    if (!deleteProjectFolders || selectedProjectFolderNames.length === 0) return;
    const deleted = await deleteProjectFolders(selectedProjectFolderNames);
    if (!deleted) return;
    cancelProjectFolderEdit();
  };
  const handleRenameSelectedProjectFolder = () => {
    if (selectedProjectFolderNames.length !== 1) return;
    const target = projectFolders.find((folder: { name: string; id?: string }) => (folder.id || folder.name) === selectedProjectFolderNames[0]);
    if (!target) return;
    setProjectFolderEditTarget?.(target);
    setProjectModal('rename-folder');
    cancelProjectFolderEdit();
  };
  const toggleProjectImageSelection = (imageName: string) => {
    setSelectedProjectImageNames((current) => (
      current.includes(imageName)
        ? current.filter((name) => name !== imageName)
        : [...current, imageName]
    ));
  };
  const toggleProjectFileSelection = (file: ProjectFileLike) => {
    const key = projectFileKey(file);
    setSelectedProjectFileKeys((current) => (
      current.includes(key)
        ? current.filter((item) => item !== key)
        : [...current, key]
    ));
  };
  const cancelProjectFolderDetailEdit = () => {
    setFolderDetailEditMode(false);
    setSelectedProjectImageNames([]);
    setSelectedProjectFileKeys([]);
  };
  const handleRenameActiveProjectFolder = () => {
    if (!activeProjectFolder) return;
    setProjectFolderEditTarget?.(activeProjectFolder);
    setProjectModal('rename-folder');
    cancelProjectFolderDetailEdit();
  };
  const handleDeleteSelectedProjectFolderItems = async () => {
    if (isImageLibraryFolder) {
      if (!deleteProjectImages || selectedProjectImageNames.length === 0) return;
      const deleted = await deleteProjectImages(selectedProjectImageNames);
      if (!deleted) return;
      setProjectImagePreviewIndex(null);
      cancelProjectFolderDetailEdit();
      return;
    }

    if (!deleteProjectFiles || selectedProjectFileKeys.length === 0) return;
    const selectedKeySet = new Set(selectedProjectFileKeys);
    const files = visibleRealProjectFiles.filter((file: ProjectFileLike) => selectedKeySet.has(projectFileKey(file)));
    const deleted = await deleteProjectFiles(files);
    if (!deleted) return;
    cancelProjectFolderDetailEdit();
  };
  const handleRenameSelectedProjectFile = () => {
    if (!selectedProjectFile) return;
    setProjectFileEditTarget?.(selectedProjectFile);
    setProjectModal('rename-file');
  };
  const handleDeleteSelectedProjectFile = () => {
    if (!selectedProjectFile) return;
    deleteProjectFile?.(selectedProjectFile);
  };
  const handleOpenProjectUpload = () => {
    setProjectUploadTargetFolder?.(projectView === 'folder' ? activeProjectFolder : null);
    setProjectModal('upload');
  };

  useEffect(() => {
    if (projectView !== 'home') {
      cancelProjectFolderEdit();
    }
    if (projectView !== 'folder') {
      cancelProjectFolderDetailEdit();
    }
  }, [projectView]);

  useEffect(() => {
    setSelectedProjectFolderNames((current) => {
      const next = current.filter((name) => visibleProjectFolderNames.includes(name));
      return next.length === current.length ? current : next;
    });
  }, [visibleProjectFolderKey]);

  useEffect(() => {
    setSelectedProjectImageNames((current) => {
      const visibleNames = new Set(visibleProjectImages.map((image: ProjectImage) => image.name));
      const next = current.filter((name) => visibleNames.has(name));
      return next.length === current.length ? current : next;
    });
  }, [visibleProjectImageKey]);

  useEffect(() => {
    setSelectedProjectFileKeys((current) => {
      const visibleKeys = new Set(visibleRealProjectFiles.map((file: ProjectFileLike) => projectFileKey(file)));
      const next = current.filter((key) => visibleKeys.has(key));
      return next.length === current.length ? current : next;
    });
  }, [visibleProjectFileKey]);

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
                  imageModel={imageModel}
                  imageRatio={imageRatio}
                  imageResolution={imageResolution}
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
                  setImageModel={setImageModel}
                  setImageRatio={setImageRatio}
                  setImageResolution={setImageResolution}
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
                  showToast={showToast}
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
                  onUseSkill={useSkillInComposer}
                />
              ) : activePage === 'projects' ? (
                <section className="library-page project-page">
                  <header className="library-header">
                    <div>
                      <div className="settings-kicker">Project Files</div>
                      <h2>{projectHeaderTitle}</h2>
                      <p>{projectHeaderDescription}</p>
                    </div>
                    {projectView !== 'detail' && (
                      <div className="project-actions">
                        <button className="secondary-action" onClick={() => setProjectModal('new-folder')} type="button">新建文件夹</button>
                        <button className="primary-action" onClick={handleOpenProjectUpload} type="button">上传文件</button>
                      </div>
                    )}
                  </header>
                  {projectView !== 'detail' && (
                    <div className="library-toolbar">
                      <label className="library-search">
                        <Search size={15} />
                        <input
                          value={projectSearchQuery}
                          onChange={(event) => setProjectSearchQuery(event.target.value)}
                          placeholder="按照名称搜索文件夹或文件"
                        />
                      </label>
                      <div className="library-tabs"><button className={projectView === 'home' ? 'active' : ''} onClick={() => setProjectView('home')} type="button">全部文件</button><button className={projectView === 'ai' ? 'active' : ''} onClick={() => setProjectView('ai')} type="button">AI 产出</button><button className={projectView === 'uploaded' ? 'active' : ''} onClick={() => setProjectView('uploaded')} type="button">我上传的</button></div>
                    </div>
                  )}
                  {projectView === 'detail' && (
                    <section className="project-section project-file-detail">
                      <div className="project-file-detail-top">
                        <button className="library-back-button project-detail-back" onClick={returnToProjectLibrary} type="button">
                          <ArrowLeft size={15} />
                          返回项目库
                        </button>
                        {selectedProjectFile && (
                          <div className="project-detail-actions">
                            <button onClick={handleRenameSelectedProjectFile} type="button">
                              <Pencil size={14} />
                              重命名
                            </button>
                            <button onClick={openSelectedProjectFile} type="button">
                              <ExternalLink size={14} />
                              新窗口打开
                            </button>
                            <button className="danger-action" onClick={handleDeleteSelectedProjectFile} type="button">
                              <Trash2 size={14} />
                              删除
                            </button>
                            <button className="primary-action" onClick={downloadSelectedProjectFile} type="button">
                              <Download size={14} />
                              下载文件
                            </button>
                          </div>
                        )}
                      </div>
                      {selectedProjectFile ? (
                        <div className="project-file-detail-shell">
                          <aside className="project-file-info-panel">
                            <div className="project-file-icon">
                              {canPreviewSelectedProjectFileAsImage ? <ImageIcon size={24} /> : <FileText size={24} />}
                            </div>
                            <div>
                              <span className="project-file-eyebrow">{selectedProjectFile.type || 'FILE'}</span>
                              <h3>{selectedProjectFile.name}</h3>
                              <p>{selectedProjectFile.folder} · {getProjectFileSourceLabel(selectedProjectFile)}</p>
                            </div>
                            <dl className="project-file-meta">
                              <div>
                                <dt>文件夹</dt>
                                <dd>{selectedProjectFile.folder}</dd>
                              </div>
                              <div>
                                <dt>来源</dt>
                                <dd>{getProjectFileSourceLabel(selectedProjectFile)}</dd>
                              </div>
                              <div>
                                <dt>更新时间</dt>
                                <dd>{selectedProjectFile.modified}</dd>
                              </div>
                              <div>
                                <dt>大小</dt>
                                <dd>{formatProjectFileSize(selectedProjectFile.size)}</dd>
                              </div>
                            </dl>
                          </aside>
                          <div className="project-file-preview-panel">
                            <div className="project-file-preview-head">
                              <div>
                                <span>文件预览</span>
                                <strong>{selectedProjectFile.name}</strong>
                              </div>
                              <span className="project-file-type-chip">{selectedProjectFile.type || 'FILE'}</span>
                            </div>
                            {canPreviewSelectedProjectFileAsImage ? (
                              <div className="project-file-image-preview">
                                <img src={selectedProjectFile.url} alt={selectedProjectFile.name} loading="lazy" decoding="async" />
                              </div>
                            ) : canPreviewSelectedProjectFileAsFrame ? (
                              <iframe src={selectedProjectFile.url} title={`预览 ${selectedProjectFile.name}`} />
                            ) : (
                              <div className="project-file-preview-empty">
                                <FileText size={32} />
                                <strong>此文件类型暂不支持内嵌预览</strong>
                                <p>可以使用新窗口打开或下载到本地查看。</p>
                              </div>
                            )}
                          </div>
                        </div>
                      ) : (
                        <div className="file-empty-state">未找到要查看的文件</div>
                      )}
                    </section>
                  )}
                  {projectView === 'folder' && activeProjectFolder && (
                    <section className="project-section folder-detail-panel">
                      <div className="folder-detail-topbar">
                        <button className="library-back-button" onClick={() => setProjectView('home')} type="button">
                          <ArrowLeft size={15} />
                          返回项目库
                        </button>
                        <div className="folder-detail-actions">
                          {folderDetailEditMode ? (
                            <>
                              <button className="folder-edit-button" onClick={cancelProjectFolderDetailEdit} type="button">取消</button>
                              <button
                                className="folder-delete-selected-button"
                                disabled={selectedFolderDetailItemCount === 0}
                                onClick={handleDeleteSelectedProjectFolderItems}
                                type="button"
                              >
                                <Trash2 size={14} />
                                删除所选{selectedFolderDetailItemCount > 0 ? `（${selectedFolderDetailItemCount}）` : ''}
                              </button>
                            </>
                          ) : (
                            <>
                              <button className="folder-edit-button" onClick={handleRenameActiveProjectFolder} type="button">
                                <Pencil size={14} />
                                重命名
                              </button>
                              <button className="folder-edit-button" onClick={() => setFolderDetailEditMode(true)} type="button">编辑</button>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="section-title-row">
                        <h3>{activeProjectFolder.name}</h3>
                        <span>{activeProjectFolder.desc}</span>
                      </div>
                      {isImageLibraryFolder ? (
                        visibleProjectImages.length > 0 ? (
                          <div className="project-image-grid">
                            {visibleProjectImages.map((img: ProjectImage, imageIndex: number) => {
                              const selected = selectedProjectImageNames.includes(img.name);
                              return (
                                <button
                                  key={img.name}
                                  className={`project-image-card${folderDetailEditMode ? ' is-selecting' : ''}${selected ? ' is-selected' : ''}`}
                                  onClick={() => {
                                    if (folderDetailEditMode) {
                                      toggleProjectImageSelection(img.name);
                                      return;
                                    }
                                    setProjectImagePreviewIndex(imageIndex);
                                  }}
                                  type="button"
                                  aria-pressed={folderDetailEditMode ? selected : undefined}
                                >
                                  {folderDetailEditMode && (
                                    <span className={selected ? 'project-image-select-box selected' : 'project-image-select-box'}>
                                      {selected && <Check size={13} />}
                                    </span>
                                  )}
                                  <ProjectLazyImage src={img.url} alt={img.name} />
                                  <span className="project-image-date">{img.modified}</span>
                                </button>
                              );
                            })}
                          </div>
                        ) : (
                          <div className="file-empty-state">暂无匹配图片</div>
                        )
                      ) : (
                        <div className="file-table">
                          {visibleRealProjectFiles.map((file: ProjectFileLike, i: number) => {
                            const fileSelected = selectedProjectFileKeys.includes(projectFileKey(file));
                            return (
                              <button
                                key={`folder-real-${i}`}
                                className={`file-row${folderDetailEditMode ? ' is-selecting' : ''}${fileSelected ? ' is-selected' : ''}`}
                                onClick={() => {
                                  if (folderDetailEditMode) {
                                    toggleProjectFileSelection(file);
                                    return;
                                  }
                                  openProjectFile(file);
                                }}
                                type="button"
                                aria-pressed={folderDetailEditMode ? fileSelected : undefined}
                              >
                                {folderDetailEditMode && (
                                  <span className={fileSelected ? 'file-select-box selected' : 'file-select-box'}>
                                    {fileSelected && <Check size={13} />}
                                  </span>
                                )}
                                <span className="file-type tone-slate">{file.type}</span>
                                <span className="file-main"><strong>{file.name}</strong><small>{file.folder} · {getProjectFileSourceLabel(file)}</small></span>
                                <span className="file-updated">{file.modified}</span>
                                <span className="file-action">{folderDetailEditMode ? (fileSelected ? '已选' : '选择') : '查看'}</span>
                              </button>
                            );
                          })}
                          {visibleRealProjectFiles.length === 0 && <div className="file-empty-state">暂无匹配文件</div>}
                        </div>
                      )}
                    </section>
                  )}
                  {projectView === 'home' && (
                    <section className="project-section">
                      <div className="section-title-row">
                        <h3>文件夹</h3>
                        <div className="folder-edit-toolbar">
                          {folderEditMode ? (
                            <>
                              <button className="folder-edit-button" onClick={cancelProjectFolderEdit} type="button">取消</button>
                              <button
                                className="folder-edit-button"
                                disabled={selectedProjectFolderNames.length !== 1}
                                onClick={handleRenameSelectedProjectFolder}
                                type="button"
                              >
                                <Pencil size={14} />
                                重命名
                              </button>
                              <button
                                className="folder-delete-selected-button"
                                disabled={selectedProjectFolderNames.length === 0}
                                onClick={handleDeleteSelectedProjectFolders}
                                type="button"
                              >
                                <Trash2 size={14} />
                                删除所选{selectedProjectFolderNames.length > 0 ? `（${selectedProjectFolderNames.length}）` : ''}
                              </button>
                            </>
                          ) : (
                            <>
                              <button className="folder-edit-button" onClick={() => setFolderEditMode(true)} type="button">编辑</button>
                              <span>点击文件夹查看文件</span>
                            </>
                          )}
                        </div>
                      </div>
                      {visibleProjectFolders.length > 0 ? (
                        <div className="folder-grid">
                          {visibleProjectFolders.map((folder: { id?: string; name: string; desc: string; tone: string; count?: string; kind?: string }, index: number) => {
                            const folderId = folder.id || folder.name;
                            const folderIndex = projectFolders.findIndex((item: { name: string; id?: string }) => (item.id || item.name) === folderId);
                            const count = folder.kind === 'image_library' || folderId === '图片库' ? `${projectImages.length} 个文件` : (folder.count || '0 个文件');
                            const selected = selectedProjectFolderNames.includes(folderId);
                            return (
                              <article key={folderId} className={`folder-card tone-${folder.tone}${folderEditMode ? ' is-editing' : ''}${selected ? ' is-selected' : ''}`}>
                                <button
                                  className="folder-open-button"
                                  onClick={() => {
                                    if (folderEditMode) {
                                      toggleProjectFolderSelection(folderId);
                                      return;
                                    }
                                    refreshProjectFiles?.(folderId);
                                    setSelectedFolderIndex(folderIndex);
                                    setProjectView('folder');
                                  }}
                                  type="button"
                                  aria-pressed={folderEditMode ? selected : undefined}
                                >
                                  {folderEditMode && (
                                    <span className={selected ? 'folder-select-box selected' : 'folder-select-box'}>
                                      {selected && <Check size={13} />}
                                    </span>
                                  )}
                                  <div className="folder-icon">▣</div>
                                  <div>
                                    <h3>{folder.name}</h3>
                                    <p>{folder.desc}</p>
                                    <span>{count}</span>
                                  </div>
                                </button>
                              </article>
                            );
                          })}
                        </div>
                      ) : (
                        <div className="file-empty-state">没有匹配的文件夹</div>
                      )}
                    </section>
                  )}
                  {projectView !== 'folder' && projectView !== 'detail' && (
                    <section className="project-section">
                      <div className="section-title-row"><h3>{projectView === 'ai' ? 'AI 产出文件' : projectView === 'uploaded' ? '我上传的文件' : '最近文件'}</h3><span>点击文件查看详情</span></div>
                      <div className="file-table">
                        {projectFileTableItems.map((file: ProjectFileLike, i: number) => (
                          <button key={`real-${i}`} className="file-row" onClick={() => openProjectFile(file)} type="button">
                            <span className="file-type tone-slate">{file.type}</span>
                            <span className="file-main"><strong>{file.name}</strong><small>{file.folder} · {getProjectFileSourceLabel(file)}</small></span>
                            <span className="file-updated">{file.modified}</span>
                            <span className="file-action">查看</span>
                          </button>
                        ))}
                        {projectFileTableItems.length === 0 && <div className="file-empty-state">暂无匹配文件</div>}
                      </div>
                    </section>
                  )}
                  {projectImagePreviewIndex !== null && (
                    <ProjectImagePreviewModal
                      images={visibleProjectImages}
                      currentIndex={projectImagePreviewIndex}
                      onChange={setProjectImagePreviewIndex}
                      onClose={() => setProjectImagePreviewIndex(null)}
                    />
                  )}
                </section>
              ) : (
                <>
                  <div className="main-stage-scroll">
                    <BrandHeader />

                    <ChatInput
                      activeDirection={activeDirection}
                      quickSkills={quickSkills}
                      selectedSkill={selectedComposerSkill}
                      onSelectedSkillRemove={() => setSelectedComposerSkill?.(null)}
                      presetImage={selectedCardImage}
                      onPresetConsumed={() => setSelectedCardImage?.(undefined)}
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

                    <section className="workflow-cards-section">
                      <div className="workflow-cards-relative">
                        <div className="workflow-steps-col">
                          <WorkflowSteps />
                        </div>
                        <div className="feature-cards-wrapper">
                          <FeatureCards onCardClick={(title, imageUrl) => {
                            setSelectedCardImage?.(imageUrl);
                          }} />
                        </div>
                      </div>
                    </section>

                    <div className="footer-note">内容由 AI 生成，请核实完整性</div>
                  </div>

                  <FreeMode />
                </>
              )}
            </main>
  );
}
