import type { AgentTaskEvent } from '../api/tasks';

export type ReportResultCard = {
  title: string;
  fileName: string;
  fileType: string;
  generatedAt?: string;
  folders: string[];
  sourceLabel?: string;
  url?: string;
};

export type AgentMessage = {
  role: 'user' | 'ai';
  content: string;
  nodeId?: string;
  images?: { style: string; url: string; original_url?: string; prompt: string }[];
  svgLogos?: { style: string; code: string }[];
  reportCards?: ReportResultCard[];
};

export type AgentEventState = {
  aiContent: string;
  images: { style: string; url: string; original_url?: string; prompt: string }[];
  svgLogos: { style: string; code: string }[];
  reportCards: ReportResultCard[];
  messages: AgentMessage[];
  conversationId?: number | null;
  conversationTitle?: string;
  nodeId?: string;
};

export type AgentEventResult = {
  state: AgentEventState;
  handled: boolean;
};

function replaceLastAiMessage(state: AgentEventState): AgentEventState {
  const messages = [...state.messages];
  const lastIndex = messages.length - 1;
  if (lastIndex < 0) return state;

  messages[lastIndex] = {
    role: 'ai',
    content: state.aiContent,
    nodeId: state.nodeId || messages[lastIndex]?.nodeId,
    images: [...state.images],
    svgLogos: [...state.svgLogos],
    reportCards: [...state.reportCards],
  };
  return { ...state, messages };
}

function readString(source: Record<string, unknown>, ...keys: string[]) {
  for (const key of keys) {
    const value = source[key];
    if (typeof value === 'string' && value.trim()) return value.trim();
  }
  return '';
}

function readStringArray(value: unknown) {
  if (!Array.isArray(value)) return [];
  const result: string[] = [];
  value.forEach((item) => {
    if (typeof item !== 'string') return;
    const clean = item.trim();
    if (clean && !result.includes(clean)) result.push(clean);
  });
  return result;
}

export function normalizeReportResultCard(payload: unknown): ReportResultCard | null {
  if (!payload || typeof payload !== 'object') return null;

  const source = payload as Record<string, unknown>;
  const fileName = readString(source, 'fileName', 'file_name', 'filename');
  const title = readString(source, 'title', 'reportTitle', 'report_title') || fileName || '报告文件';
  const folders = readStringArray(source.folders);
  const fallbackFolder = readString(source, 'folder');
  if (fallbackFolder && !folders.includes(fallbackFolder)) folders.push(fallbackFolder);

  return {
    title,
    fileName: fileName || title,
    fileType: readString(source, 'fileType', 'file_type') || 'HTML',
    generatedAt: readString(source, 'generatedAt', 'generated_at') || undefined,
    folders,
    sourceLabel: readString(source, 'sourceLabel', 'source_label') || undefined,
    url: readString(source, 'url', 'fileUrl', 'file_url') || undefined,
  };
}

function reportCardFromEvent(event: AgentTaskEvent): ReportResultCard | null {
  const artifactType = typeof event.artifact_type === 'string' ? event.artifact_type : '';
  const hasReportTitle = typeof event.report_title === 'string' && event.report_title.trim().length > 0;
  const isReport = artifactType === 'report' || hasReportTitle || event.report_card === true;
  if (!isReport) return null;

  return normalizeReportResultCard({
    title: event.report_title || event.title,
    fileName: event.file_name || event.filename,
    fileType: event.file_type,
    generatedAt: event.generated_at,
    folders: event.folders,
    folder: event.folder,
    sourceLabel: event.source_label,
    url: event.file_url || event.url,
  });
}

function appendReportCard(cards: ReportResultCard[], card: ReportResultCard) {
  const key = card.url || card.fileName || card.title;
  if (cards.some((item) => (item.url || item.fileName || item.title) === key)) {
    return cards;
  }
  return [...cards, card];
}

export function reduceAgentEvent(state: AgentEventState, event: AgentTaskEvent): AgentEventResult {
  if (event.type === 'content') {
    return {
      handled: true,
      state: replaceLastAiMessage({
        ...state,
        aiContent: state.aiContent + (event.content || ''),
      }),
    };
  }

  if (event.type === 'svg') {
    return {
      handled: true,
      state: replaceLastAiMessage({
        ...state,
        svgLogos: [...state.svgLogos, { style: event.style, code: event.code }],
      }),
    };
  }

  if (event.type === 'image') {
    return {
      handled: true,
      state: replaceLastAiMessage({
        ...state,
        images: [...state.images, { style: event.style, url: event.url, original_url: event.original_url, prompt: event.prompt }],
      }),
    };
  }

  if (event.type === 'file_saved') {
    const reportCard = reportCardFromEvent(event);
    if (reportCard) {
      return {
        handled: true,
        state: replaceLastAiMessage({
          ...state,
          reportCards: appendReportCard(state.reportCards, reportCard),
        }),
      };
    }

    const msg = event.message || '';
    const isReport = msg.includes('报告') || msg.includes('方案') || msg.includes('手册') || msg.includes('文案');
    const prefix = isReport ? '\n\n✅ ' : '\n\n📁 ';
    const suffix = isReport ? '\n\n📁 文件已保存至「编程文件库」+「AI 对话产出」' : '';
    return {
      handled: true,
      state: replaceLastAiMessage({
        ...state,
        aiContent: `${state.aiContent}${prefix}${msg}${suffix}`,
      }),
    };
  }

  if (event.type === 'conversation_saved') {
    return {
      handled: true,
      state: {
        ...state,
        conversationId: event.conversation_id || state.conversationId,
        conversationTitle: event.title || state.conversationTitle,
        nodeId: event.node_id || state.nodeId,
      },
    };
  }

  return { handled: false, state };
}

export function stopAgentEventState(state: AgentEventState): AgentEventState {
  if (state.aiContent) return state;
  return replaceLastAiMessage({ ...state, aiContent: '⏹ 已停止生成' });
}

export function errorAgentEventState(state: AgentEventState, message: string): AgentEventState {
  return replaceLastAiMessage({ ...state, aiContent: message });
}
