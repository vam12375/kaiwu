import { useState, useRef, useEffect, useCallback } from 'react';
import { Plus, Mic, MicOff, ArrowUp, Bot, ChevronDown, Sparkles, X } from 'lucide-react';
import { modelOptions } from '../../data';
import type { SkillLibraryItem } from '../../types';

type ChatInputProps = {
  activeDirection: string;
  quickSkills: string[];
  presetImage?: string;
  onPresetConsumed?: () => void;
  selectedSkill?: SkillLibraryItem | null;
  onSelectedSkillRemove?: () => void;
  // kaiwu integration
  homeTextareaRef: React.RefObject<HTMLTextAreaElement | null>;
  inputText: string;
  setInputText: (v: string) => void;
  isComposingRef: React.MutableRefObject<boolean>;
  handleSend: () => void;
  isLoading: boolean;
  modelIndex: number;
  setModelIndex: (v: number) => void;
};

export function ChatInput({
  activeDirection,
  quickSkills,
  presetImage,
  onPresetConsumed,
  selectedSkill,
  onSelectedSkillRemove,
  homeTextareaRef,
  inputText,
  setInputText,
  isComposingRef,
  handleSend,
  isLoading,
  modelIndex,
  setModelIndex,
}: ChatInputProps) {
  const [modelOpen, setModelOpen] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [previewImage, setPreviewImage] = useState<string | undefined>();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);
  const modelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (presetImage) {
      setPreviewImage(presetImage);
    }
  }, [presetImage]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (modelRef.current && !modelRef.current.contains(e.target as HTMLElement)) {
        setModelOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleVoice = useCallback(() => {
    const SpeechRecognitionCtor = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognitionCtor) {
      alert('当前浏览器不支持语音输入');
      return;
    }
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }
    const recognition = new SpeechRecognitionCtor();
    recognition.lang = 'zh-CN';
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.onresult = (event: any) => {
      const transcript = event.results[0]?.[0]?.transcript || '';
      if (transcript) setInputText(inputText ? `${inputText} ${transcript}` : transcript);
      setIsListening(false);
    };
    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);
    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  }, [isListening, inputText, setInputText]);

  const onSend = () => {
    if (!inputText.trim()) return;
    handleSend();
    setPreviewImage(undefined);
  };

  return (
    <section className="chat-input-section">
      <div className="chat-input-wrapper">
        <div className="chat-input-card">
          <textarea
            ref={homeTextareaRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onCompositionStart={() => { isComposingRef.current = true; }}
            onCompositionEnd={() => { isComposingRef.current = false; }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey && !isComposingRef.current) { e.preventDefault(); onSend(); }
              else if (e.key === 'Enter' && e.ctrlKey) { e.preventDefault(); onSend(); }
            }}
            placeholder="描述你的创业想法、目标用户、当前卡点，开物会帮你拆成可执行方案..."
            className="chat-input-textarea"
            rows={3}
          />

          {previewImage && (
            <div className="chat-preview-thumb">
              <img src={previewImage} alt="" />
              <button className="chat-preview-remove" onClick={() => setPreviewImage(undefined)} aria-label="移除图片">
                <X size={12} />
              </button>
            </div>
          )}

          {selectedSkill && (
            <div className="chat-skill-card">
              <span className="chat-skill-card-icon">
                <Sparkles size={15} />
              </span>
              <div>
                <strong>{selectedSkill.name}</strong>
                <span>{selectedSkill.category} · {selectedSkill.description}</span>
              </div>
              <button className="chat-skill-card-remove" onClick={onSelectedSkillRemove} type="button" aria-label="移除技能">
                <X size={13} />
              </button>
            </div>
          )}

          {quickSkills.length > 0 && (
            <div className="skill-row in-composer">
              {quickSkills.map((skill: string) => (
                <button key={skill} className="skill-chip">{skill}</button>
              ))}
            </div>
          )}

          <div className="chat-input-toolbar">
            <div className="toolbar-left">
              <div className="picker-wrap" ref={modelRef}>
                <button
                  className={modelOpen ? 'toolbar-select model-select is-active' : 'toolbar-select model-select'}
                  onClick={() => setModelOpen(!modelOpen)}
                >
                  <Bot size={14} />
                  <span>{modelOptions[modelIndex].name}</span>
                  <ChevronDown size={13} />
                </button>
                {modelOpen && (
                  <div className="picker-popover">
                    {modelOptions.map((item, index) => (
                      <button
                        key={item.name}
                        className={modelIndex === index ? 'model-menu-row selected' : 'model-menu-row'}
                        onClick={() => { setModelIndex(index); setModelOpen(false); }}
                      >
                        <span className="model-icon">✦</span>
                        <span className="model-name">{item.name}</span>
                        <span className="model-desc">{item.desc}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <button className="toolbar-select">
                <span>📂</span>
                <span>参考历史文件</span>
                <ChevronDown size={13} />
              </button>
            </div>

            <div className="toolbar-right">
              <input ref={fileInputRef} type="file" className="hidden-input" onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) alert(`已选择文件：${file.name}`);
              }} />
              <button className="icon-action" onClick={() => fileInputRef.current?.click()} aria-label="添加附件">
                <Plus size={16} />
              </button>
              <button
                className={isListening ? 'icon-action voice-active' : 'icon-action'}
                onClick={handleVoice}
                aria-label={isListening ? '停止语音输入' : '语音输入'}
              >
                {isListening ? <MicOff size={16} /> : <Mic size={16} />}
              </button>
              <button
                className={`icon-action send-action ${isLoading ? 'send-disabled' : ''}`}
                onClick={onSend}
                disabled={isLoading}
                aria-label="发送"
              >
                <ArrowUp size={17} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
