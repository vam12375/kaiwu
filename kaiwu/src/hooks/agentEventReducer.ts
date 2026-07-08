import type { AgentTaskEvent } from '../api/tasks';

export type AgentMessage = {
  role: 'user' | 'ai';
  content: string;
  images?: { style: string; url: string; original_url?: string; prompt: string }[];
  svgLogos?: { style: string; code: string }[];
};

export type AgentEventState = {
  aiContent: string;
  images: { style: string; url: string; original_url?: string; prompt: string }[];
  svgLogos: { style: string; code: string }[];
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
    images: [...state.images],
    svgLogos: [...state.svgLogos],
  };
  return { ...state, messages };
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
    return {
      handled: true,
      state: replaceLastAiMessage({
        ...state,
        aiContent: `${state.aiContent}\n\n📁 ${event.message}`,
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

