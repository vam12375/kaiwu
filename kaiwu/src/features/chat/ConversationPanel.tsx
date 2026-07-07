import { useEffect, useState, type Dispatch, type RefObject, type SetStateAction } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ArrowUp, Bookmark, Bot, Box, ChevronDown, ChevronLeft, Copy, Download, ImagePlus, Square, X } from 'lucide-react';

import { imageModelOptions, imageRatioOptions, imageResolutionOptions, modelOptions, projectFolders } from '../../data';
import { API_BASE_URL, apiJson } from '../../api/client';
import type { Direction, ImageModelId, ImageRatio, ImageResolution, LibraryModalType, PickerType, ShowToast } from '../../types';
import { renderMarkdown } from '../../utils';
import type { AgentMessage } from '../../hooks/agentEventReducer';
import type { SendMessageOptions } from '../../hooks/useConversationTask';
import type { ImageReferenceInput } from '../../api/tasks';

type NodeStatus = {
  nodeId: string;
  nodeName: string;
  nodeIcon: string;
  progress: number;
  message: string;
};

type MutableRef<T> = {
  current: T;
};

type UploadedFile = {
  name: string;
  size: number;
};

type ReferenceImagePreview = ImageReferenceInput & {
  url: string;
};

type GeneratedImagePreview = {
  style: string;
  url: string;
};

type ConversationPanelProps = {
  activeDirection: Direction;
  activeNodeId: string;
  conversationTitle: string;
  convTextareaRef: RefObject<HTMLTextAreaElement | null>;
  countOpen: boolean;
  fileIndex: number | null;
  followupNodeRef: MutableRef<string | null>;
  handleSend: (options?: SendMessageOptions) => Promise<void>;
  imageCount: number;
  imageModel: ImageModelId;
  imageRatio: ImageRatio;
  imageResolution: ImageResolution;
  inputText: string;
  isComposingRef: MutableRef<boolean>;
  isImageMode: boolean;
  isLoading: boolean;
  libraryModal: LibraryModalType;
  messages: AgentMessage[];
  modelIndex: number;
  nodeStatus: NodeStatus | null;
  openPicker: PickerType;
  ratioOpen: boolean;
  removeUploadedFile: (name: string) => void;
  resetConversation: () => void;
  setCountOpen: Dispatch<SetStateAction<boolean>>;
  setImageCount: Dispatch<SetStateAction<number>>;
  setImageModel: Dispatch<SetStateAction<ImageModelId>>;
  setImageRatio: Dispatch<SetStateAction<ImageRatio>>;
  setImageResolution: Dispatch<SetStateAction<ImageResolution>>;
  setInputText: Dispatch<SetStateAction<string>>;
  setLibraryModal: Dispatch<SetStateAction<LibraryModalType>>;
  setModelIndex: Dispatch<SetStateAction<number>>;
  setOpenPicker: Dispatch<SetStateAction<PickerType>>;
  setRatioOpen: Dispatch<SetStateAction<boolean>>;
  setSelectedFolderIndex: Dispatch<SetStateAction<number>>;
  setSuggestedQuestions: (items: string[]) => void;
  stopGeneration: () => void;
  suggestedQuestions: string[];
  uploadedFiles: UploadedFile[];
  showToast: ShowToast;
};

const MAX_REFERENCE_IMAGES = 4;
const MAX_REFERENCE_IMAGE_SIZE = 8 * 1024 * 1024;

function stripRenderedMarkdownImages(content: string) {
  return content
    .replace(/!\[[^\]]*]\([^)]+\)/g, '')
    .split('\n')
    .filter((line) => !/^\s*图片生成(完成|#?\d*)\s*$/.test(line.trim()))
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function imageDownloadUrl(imageUrl: string) {
  return `${API_BASE_URL}/api/download-image?url=${encodeURIComponent(imageUrl)}`;
}

const NODE_ACTIONS: Record<string, { label: string; prompt: string }> = {
  node1: { label: '📄 生成深度商业调研报告', prompt: '生成深度商业调研报告' },
  node2: { label: '📋 生成品牌商业计划书', prompt: '帮我生成品牌商业计划书' },
  node3: { label: '📦 生成产品手册', prompt: '生成产品手册' },
  node4: { label: '📊 生成系统化内容营销解决方案', prompt: '生成系统化内容营销解决方案' },
};

function saveToProject(content: string, title: string, showToast: ShowToast) {
  apiJson<{ status: string; message?: string }>('/api/save-to-project', {
    method: 'POST',
    body: JSON.stringify({ content, title }),
  })
    .then((data) => {
      if (data.status === 'ok') {
        showToast({ message: data.message || '已保存到项目库', variant: 'success' });
        return;
      }
      showToast({ message: data.message || '保存失败，请稍后重试', variant: 'error' });
    })
    .catch(() => {
      showToast({ message: '保存失败，请稍后重试', variant: 'error' });
    })
}

function readImageAsDataUrl(file: File): Promise<ReferenceImagePreview> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = typeof reader.result === 'string' ? reader.result : '';
      if (!dataUrl) {
        reject(new Error('图片读取失败'));
        return;
      }
      resolve({
        name: file.name,
        mime_type: file.type || 'image/png',
        size: file.size,
        data_url: dataUrl,
        url: dataUrl,
      });
    };
    reader.onerror = () => reject(new Error('图片读取失败'));
    reader.readAsDataURL(file);
  });
}

export function ConversationPanel({
  activeDirection,
  activeNodeId,
  conversationTitle,
  convTextareaRef,
  countOpen,
  fileIndex,
  followupNodeRef,
  handleSend,
  imageCount,
  imageModel,
  imageRatio,
  imageResolution,
  inputText,
  isComposingRef,
  isImageMode,
  isLoading,
  libraryModal,
  messages,
  modelIndex,
  nodeStatus,
  openPicker,
  ratioOpen,
  removeUploadedFile,
  resetConversation,
  setCountOpen,
  setImageCount,
  setImageModel,
  setImageRatio,
  setImageResolution,
  setInputText,
  setLibraryModal,
  setModelIndex,
  setOpenPicker,
  setRatioOpen,
  setSelectedFolderIndex,
  setSuggestedQuestions,
  stopGeneration,
  suggestedQuestions,
  uploadedFiles,
  showToast,
}: ConversationPanelProps) {
  const [referenceImages, setReferenceImages] = useState<ReferenceImagePreview[]>([]);
  const [previewImage, setPreviewImage] = useState<GeneratedImagePreview | null>(null);

  useEffect(() => () => {
    referenceImages.forEach((image) => {
      if (image.url.startsWith('blob:')) URL.revokeObjectURL(image.url);
    });
  }, [referenceImages]);

  const openReferenceImagePicker = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.multiple = true;
    input.onchange = async (event) => {
      const files = Array.from((event.target as HTMLInputElement).files || []);
      const validFiles = files
        .filter((file) => file.type.startsWith('image/'))
        .slice(0, MAX_REFERENCE_IMAGES);
      const oversized = validFiles.find((file) => file.size > MAX_REFERENCE_IMAGE_SIZE);
      if (oversized) {
        showToast({ message: '参考图单张不能超过 8MB', variant: 'error' });
        return;
      }
      if (files.length > MAX_REFERENCE_IMAGES) {
        showToast({ message: `最多上传 ${MAX_REFERENCE_IMAGES} 张参考图`, variant: 'info' });
      }
      try {
        setReferenceImages(await Promise.all(validFiles.map(readImageAsDataUrl)));
      } catch {
        showToast({ message: '参考图读取失败，请重新选择', variant: 'error' });
      }
    };
    input.click();
  };

  const clearReferenceImages = () => {
    setReferenceImages([]);
  };

  const downloadImage = (image: GeneratedImagePreview) => {
    window.open(imageDownloadUrl(image.url), '_blank');
  };

  const sendImageGeneration = () => {
    void handleSend({
      fallbackMessage: referenceImages.length > 0 ? '根据参考图生成图片' : undefined,
      referenceImages: referenceImages.map(({ name, mime_type, size, data_url }) => ({
        name,
        mime_type,
        size,
        data_url,
      })),
      taskType: 'image_generation',
    });
  };

  const runPrompt = (prompt: string, followupNode: string | null) => {
    if (convTextareaRef.current) convTextareaRef.current.value = prompt;
    setInputText(prompt);
    setSuggestedQuestions([]);
    followupNodeRef.current = followupNode;
    window.setTimeout(() => {
      void handleSend();
    }, 80);
  };

  const nodeAction = NODE_ACTIONS[activeNodeId];

  return (
    <section className="doubao-conversation">
      <header className="doubao-conversation-header">
        <button className="doubao-back" onClick={() => resetConversation()} type="button">
          <ChevronLeft size={18} />
        </button>
        <div className="doubao-header-center">
          <h2>{conversationTitle}</h2>
          <span>{isImageMode ? '图片生成' : activeDirection !== '通用' ? activeDirection : '通用咨询'}</span>
        </div>
        <div className="doubao-header-spacer" aria-hidden="true" />
      </header>

      <div className="doubao-messages" id="doubao-messages">
        <AnimatePresence>
          {messages.length === 0 && (
            <motion.div
              className="doubao-empty"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
            >
              <motion.div
                className="doubao-empty-icon"
                initial={{ scale: 0, rotate: -15 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ type: 'spring', stiffness: 300, damping: 18, delay: 0.1 }}
              >
                <Box size={24} />
              </motion.div>
              <motion.h3 initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}>
                开物
              </motion.h3>
              <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
                基于 {activeDirection} 赛道，我能帮你做什么？
              </motion.p>
            </motion.div>
          )}
        </AnimatePresence>
        <AnimatePresence>
          {messages.map((message, messageIndex) => (
            <motion.div
              key={messageIndex}
              initial={{ opacity: 0, y: 16, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] }}
              className={message.role === 'user' ? 'doubao-message doubao-user' : 'doubao-message doubao-ai'}
            >
              <div className="doubao-message-inner">
                {message.role === 'ai' && !isImageMode && (
                  <motion.div
                    className="doubao-ai-avatar"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', stiffness: 400, damping: 20, delay: 0.1 }}
                  >
                    曜
                  </motion.div>
                )}

                <div className={`doubao-bubble ${message.role === 'user' ? 'doubao-bubble-user' : 'doubao-bubble-ai'}`}>
                  {message.role === 'ai' && message.content === '' && isLoading ? (
                    <div className="doubao-node-progress">
                      {nodeStatus && nodeStatus.nodeName ? (
                        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
                          <div className="node-progress-card-head">
                            <motion.div
                              className="node-badge"
                              initial={{ scale: 0.8, opacity: 0 }}
                              animate={{ scale: 1, opacity: 1 }}
                              transition={{ type: 'spring', stiffness: 500, damping: 25 }}
                            >
                              <span className="node-badge-icon">{nodeStatus.nodeIcon}</span>
                              <span className="node-badge-label">{nodeStatus.nodeName}</span>
                            </motion.div>
                            <motion.span
                              className="node-pct-ring"
                              key={nodeStatus.progress}
                              initial={{ scale: 1.3 }}
                              animate={{ scale: 1 }}
                              transition={{ duration: 0.2 }}
                            >
                              {nodeStatus.progress}%
                            </motion.span>
                          </div>
                          <div className="node-progress-bar-wrap">
                            <motion.div
                              className="node-progress-bar-glow"
                              animate={{ width: `${nodeStatus.progress}%` }}
                              transition={{ duration: 0.4, ease: 'easeOut' }}
                            />
                            <motion.div
                              className="node-progress-bar-fill"
                              animate={{ width: `${nodeStatus.progress}%` }}
                              transition={{ duration: 0.4, ease: 'easeOut' }}
                            />
                          </div>
                          <motion.p
                            className="node-progress-msg"
                            key={nodeStatus.message}
                            initial={{ opacity: 0, x: -8 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.25 }}
                          >
                            {nodeStatus.message}
                          </motion.p>
                        </motion.div>
                      ) : (
                        <motion.div className="node-analyzing" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                          <div className="node-analyzing-dots">
                            <span />
                            <span />
                            <span />
                            <span />
                          </div>
                          <p>正在分析您的需求意图...</p>
                        </motion.div>
                      )}
                    </div>
                  ) : (
                    <motion.div
                      className="doubao-bubble-content"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.4 }}
                      dangerouslySetInnerHTML={{ __html: renderMarkdown(message.images?.length ? stripRenderedMarkdownImages(message.content) : message.content) }}
                    />
                  )}
                </div>
              </div>

              {message.role === 'ai' && message.svgLogos && message.svgLogos.length > 0 && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '12px', padding: '8px 0 0 42px' }}>
                  {message.svgLogos.map((logo, logoIndex) => {
                    const image = message.images?.find((item) => item.style === logo.style);
                    const saveImage = () => {
                      if (image) {
                        downloadImage(image);
                        return;
                      }

                      const svgEl = document.getElementById(`svg-logo-${messageIndex}-${logoIndex}`);
                      if (svgEl) {
                        const svg = svgEl.outerHTML;
                        const blob = new Blob([svg], { type: 'image/svg+xml' });
                        const anchor = document.createElement('a');
                        anchor.href = URL.createObjectURL(blob);
                        anchor.download = `logo-${logo.style}.svg`;
                        anchor.click();
                        URL.revokeObjectURL(anchor.href);
                      }
                    };

                    return (
                      <div key={logoIndex} className="md-svg-container">
                        {image ? (
                          <button
                            className="generated-image-thumb"
                            onClick={() => setPreviewImage(image)}
                            type="button"
                            title="预览图片"
                          >
                            <img src={image.url} alt={logo.style} />
                          </button>
                        ) : (
                          <div id={`svg-logo-${messageIndex}-${logoIndex}`} dangerouslySetInnerHTML={{ __html: logo.code }} />
                        )}
                        {!image && (
                          <button className="md-svg-save-btn" onClick={saveImage} title="保存图片" type="button">
                            <Download size={15} />
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {message.role === 'ai' && message.images && message.images.length > 0 && (!message.svgLogos || message.svgLogos.length === 0) && (
                <div className="doubao-images-grid">
                  {message.images.map((image, imageIndex) => (
                    <div key={imageIndex} className="md-svg-container generated-image-card">
                      <button
                        className="generated-image-thumb"
                        onClick={() => setPreviewImage(image)}
                        type="button"
                        title="预览图片"
                      >
                        <img src={image.url} alt={image.style} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {message.role === 'ai' && message.content && !isLoading && (
                <motion.div className="doubao-actions" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}>
                  <button
                    type="button"
                    onClick={() => {
                      navigator.clipboard
                        .writeText(message.content)
                        .then(() => {
                          const el = document.activeElement as HTMLElement;
                          el?.blur();
                          showToast({ message: '已复制到剪贴板', variant: 'success' });
                        })
                        .catch(() => {
                          showToast({ message: '复制失败，请稍后重试', variant: 'error' });
                        });
                    }}
                    title="复制到剪贴板"
                  >
                    <Copy size={14} />
                  </button>
                  <button onClick={() => saveToProject(message.content, conversationTitle, showToast)} type="button" title="保存到AI对话产出">
                    <Bookmark size={14} />
                  </button>
                </motion.div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {suggestedQuestions.length > 0 && !isLoading && (
        <div className="suggested-questions-bar">
          {suggestedQuestions.map((question, index) => (
            <button
              key={index}
              className="suggested-question-chip"
              onClick={() => runPrompt(question, activeNodeId)}
              type="button"
            >
              {question}
            </button>
          ))}
        </div>
      )}

      {nodeAction && !isLoading && messages.length > 0 && (
        <div className="suggested-questions-bar">
          <button
            className="suggested-question-chip"
            style={{ background: 'var(--brand-accent)', color: '#fff', borderColor: 'var(--brand-accent)', fontWeight: 600 }}
            onClick={() => runPrompt(nodeAction.prompt, null)}
            type="button"
          >
            {nodeAction.label}
          </button>
        </div>
      )}

      {uploadedFiles.length > 0 && (
        <div className="uploaded-files-bar">
          {uploadedFiles.map((file, index) => (
            <span key={index} className="uploaded-file-tag">
              <span className="file-tag-icon">📄</span>
              <span className="file-tag-name">{file.name}</span>
              <button className="file-tag-close" onClick={() => removeUploadedFile(file.name)} type="button" title="移除文件">
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      <div className={isImageMode ? 'doubao-composer image-generation-composer' : 'doubao-composer'}>
        <div className={isImageMode ? 'doubao-composer-inner image-generation-inner' : 'doubao-composer-inner'}>
          {isImageMode && (
            <div className="image-reference-shell">
              <button className="image-reference-button" onClick={openReferenceImagePicker} type="button" title="上传参考图">
                {referenceImages.length > 0 ? (
                  <>
                    <img src={referenceImages[0].url} alt={referenceImages[0].name} />
                    <span className="image-reference-count">{referenceImages.length} 张</span>
                  </>
                ) : (
                  <>
                    <ImagePlus size={24} />
                    <span>参考图</span>
                  </>
                )}
              </button>
              {referenceImages.length > 0 && (
                <button className="image-reference-remove" onClick={clearReferenceImages} type="button" aria-label="删除参考图" title="删除参考图">
                  <X size={13} />
                </button>
              )}
            </div>
          )}
          <textarea
            ref={convTextareaRef}
            value={inputText}
            placeholder={isImageMode ? '上传参考图、输入文字或 @ 主体，描述你想生成的图片。' : '继续追问，或让开物把结果保存为阶段产物...'}
            onChange={(event) => setInputText(event.target.value)}
            onCompositionStart={() => {
              isComposingRef.current = true;
            }}
            onCompositionEnd={() => {
              isComposingRef.current = false;
            }}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey && !isComposingRef.current) {
                event.preventDefault();
                if (isImageMode) {
                  sendImageGeneration();
                } else {
                  void handleSend();
                }
              } else if (event.key === 'Enter' && event.ctrlKey) {
                event.preventDefault();
                if (isImageMode) {
                  sendImageGeneration();
                } else {
                  void handleSend();
                }
              }
            }}
          />
          <div className="doubao-composer-foot">
            <div className="toolbar-left">
              {isImageMode ? (
                <>
                  <div className="picker-wrap">
                    <button
                      className={openPicker === 'image-mode' ? 'toolbar-select image-mode-select is-active' : 'toolbar-select image-mode-select'}
                      onClick={() => {
                        setOpenPicker(openPicker === 'image-mode' ? null : 'image-mode');
                        setRatioOpen(false);
                        setCountOpen(false);
                      }}
                      type="button"
                    >
                      <ImagePlus size={14} />
                      <span>图片生成</span>
                      <ChevronDown size={13} />
                    </button>
                    {openPicker === 'image-mode' && (
                      <div className="picker-popover image-compact-popover">
                        <button className="model-menu-row selected" onClick={() => setOpenPicker(null)} type="button">
                          <span className="model-icon">✦</span>
                          <span className="model-name">图片生成</span>
                        </button>
                        <button className="model-menu-row muted" disabled type="button">
                          <span className="model-icon">＋</span>
                          <span className="model-name">图片编辑</span>
                        </button>
                      </div>
                    )}
                  </div>
                  <div className="picker-wrap">
                    <button
                      className={openPicker === 'image-model' ? 'toolbar-select image-model-select is-active-soft' : 'toolbar-select image-model-select'}
                      onClick={() => {
                        setOpenPicker(openPicker === 'image-model' ? null : 'image-model');
                        setRatioOpen(false);
                        setCountOpen(false);
                      }}
                      type="button"
                    >
                      <Box size={14} />
                      <span className="image-model-label">{imageModel}</span>
                    </button>
                    {openPicker === 'image-model' && (
                      <div className="picker-popover image-model-choice-popover">
                        {imageModelOptions.map((modelName) => (
                          <button
                            key={modelName}
                            className={imageModel === modelName ? 'model-menu-row selected' : 'model-menu-row'}
                            onClick={() => {
                              setImageModel(modelName);
                              setOpenPicker(null);
                            }}
                            type="button"
                          >
                            <span className="model-icon">✦</span>
                            <span className="model-name">{modelName}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="picker-wrap">
                    <button
                      className={ratioOpen ? 'toolbar-select is-active-soft image-size-select' : 'toolbar-select image-size-select'}
                      onClick={() => {
                        setRatioOpen(!ratioOpen);
                        setCountOpen(false);
                        setOpenPicker(null);
                      }}
                      type="button"
                    >
                      <span>{imageRatio}</span>
                      <span className="image-size-divider" />
                      <span>{imageResolution}</span>
                    </button>
                    {ratioOpen && (
                      <div className="picker-popover image-size-popover-chat">
                        <strong>画面比例</strong>
                        <div className="image-ratio-grid-chat">
                          {imageRatioOptions.map((ratio) => (
                            <button
                              key={ratio}
                              className={imageRatio === ratio ? 'selected' : ''}
                              onClick={() => setImageRatio(ratio)}
                              type="button"
                            >
                              {ratio}
                            </button>
                          ))}
                        </div>
                        <strong>分辨率</strong>
                        <div className="image-resolution-row-chat">
                          {imageResolutionOptions.map((resolution) => (
                            <button
                              key={resolution}
                              className={imageResolution === resolution ? 'selected' : ''}
                              onClick={() => {
                                setImageResolution(resolution);
                                setRatioOpen(false);
                              }}
                              type="button"
                            >
                              {resolution}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <>
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
                        const aiIndex = projectFolders.findIndex((folder) => folder.name === 'AI 对话产出');
                        if (aiIndex >= 0) setSelectedFolderIndex(aiIndex);
                      }}
                      type="button"
                    >
                      <span>📂</span>
                      <span>参考历史文件</span>
                      <ChevronDown size={13} />
                    </button>
                  </div>
                  <div className="picker-wrap">
                    <button
                      className="toolbar-select"
                      onClick={() => {
                        const input = document.createElement('input');
                        input.type = 'file';
                        input.multiple = true;
                        input.onchange = (event) => {
                          const files = (event.target as HTMLInputElement).files;
                          if (files && files.length > 0) {
                            setInputText((prev) => `${prev} [已上传 ${files.length} 个文件]`);
                            showToast({ message: `已选择 ${files.length} 个文件`, variant: 'success' });
                          }
                        };
                        input.click();
                      }}
                      type="button"
                    >
                      <span>📎</span>
                      <span>上传文件</span>
                      <ChevronDown size={13} />
                    </button>
                  </div>
                </>
              )}
            </div>
            <div className="toolbar-right">
              {isImageMode && (
                <div className="picker-wrap">
                  <button
                    className={countOpen ? 'toolbar-select is-active-soft image-count-select' : 'toolbar-select image-count-select'}
                    onClick={() => {
                      setCountOpen(!countOpen);
                      setRatioOpen(false);
                      setOpenPicker(null);
                    }}
                    type="button"
                  >
                    <span>{imageCount}/张</span>
                    <ChevronDown size={13} />
                  </button>
                  {countOpen && (
                    <div className="picker-popover image-count-popover">
                      {[1, 2, 3, 4].map((count) => (
                        <button
                          key={count}
                          className={imageCount === count ? 'model-menu-row selected' : 'model-menu-row'}
                          onClick={() => {
                            setImageCount(count);
                            setCountOpen(false);
                          }}
                          type="button"
                        >
                          <span className="model-name">{count} 张</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
              <button
                className={`icon-action send-action ${
                  isLoading
                    ? 'send-stop-action'
                    : !inputText.trim() && (!isImageMode || referenceImages.length === 0)
                      ? 'send-disabled'
                      : ''
                }`}
                aria-label={isLoading ? '停止生成' : '发送'}
                title={isLoading ? '停止生成' : '发送'}
                onClick={() => {
                  if (isLoading) {
                    stopGeneration();
                    return;
                  }
                  if (isImageMode) {
                    sendImageGeneration();
                  } else {
                    void handleSend();
                  }
                }}
                disabled={!isLoading && !inputText.trim() && (!isImageMode || referenceImages.length === 0)}
                type="button"
              >
                {isLoading ? <Square size={12} fill="currentColor" strokeWidth={2.4} /> : <ArrowUp size={17} />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {previewImage && (
        <div className="modal-backdrop generated-image-preview-backdrop" onClick={() => setPreviewImage(null)}>
          <section
            className="generated-image-preview-modal"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="图片预览"
          >
            <header className="generated-image-preview-header">
              <strong>{previewImage.style}</strong>
              <button className="modal-close" onClick={() => setPreviewImage(null)} type="button" aria-label="关闭预览" title="关闭预览">
                <X size={17} />
              </button>
            </header>
            <div className="generated-image-preview-frame">
              <img src={previewImage.url} alt={previewImage.style} />
            </div>
            <div className="preview-actions">
              <button className="secondary-action" onClick={() => setPreviewImage(null)} type="button">关闭</button>
              <button className="primary-action generated-image-download-action" onClick={() => downloadImage(previewImage)} type="button">
                <Download size={14} />
                下载图片
              </button>
            </div>
          </section>
        </div>
      )}
    </section>
  );
}
