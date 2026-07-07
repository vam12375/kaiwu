import { useCallback, useEffect } from 'react';
import type { Dispatch, MouseEvent, SetStateAction } from 'react';

import { apiJson } from '../api/client';
import type { ConvHistory, ShowToast, SidebarPage } from '../types';
import type { AgentMessage } from './agentEventReducer';
import type { ConversationTaskCacheEntry } from './useConversationTask';

type WorkflowPhase = 'idle' | 'analyzing' | 'executing' | 'responding';

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

type ConversationRecord = {
  id: number;
  title: string;
  node_id?: string | null;
  messages?: { role: string; content: string }[];
};

type ResetConversationOptions = {
  activePage?: SidebarPage;
  clearLoading?: boolean;
  imageMode?: boolean;
  inputText?: string;
  open?: boolean;
};

type UseConversationOptions = {
  activePage: SidebarPage;
  currentConvId: number | null;
  messages: AgentMessage[];
  isLoading: boolean;
  workflowPhase: WorkflowPhase;
  nodeStatus: NodeStatus | null;
  conversationTitle: string;
  convIdRef: MutableRef<number | null>;
  sseConvIdRef: MutableRef<number | null>;
  suggestedQuestionsRef: MutableRef<string[]>;
  convCacheRef: MutableRef<Map<number, ConversationTaskCacheEntry>>;
  setMessages: Dispatch<SetStateAction<AgentMessage[]>>;
  setIsLoading: Dispatch<SetStateAction<boolean>>;
  setWorkflowPhase: Dispatch<SetStateAction<WorkflowPhase>>;
  setNodeStatus: Dispatch<SetStateAction<NodeStatus | null>>;
  setConversationOpen: Dispatch<SetStateAction<boolean>>;
  setConversationTitle: Dispatch<SetStateAction<string>>;
  setCurrentConvId: Dispatch<SetStateAction<number | null>>;
  setIsImageMode: Dispatch<SetStateAction<boolean>>;
  setSuggestedQuestions: (items: string[]) => void;
  setActiveNodeId: Dispatch<SetStateAction<string>>;
  setActivePage: Dispatch<SetStateAction<SidebarPage>>;
  setInputText: Dispatch<SetStateAction<string>>;
  setConvHistory: Dispatch<SetStateAction<ConvHistory[]>>;
  setOpenHistoryMenu: Dispatch<SetStateAction<number | null>>;
  showToast?: ShowToast;
};

function parseConversationMessages(messages: { role: string; content: string }[] = []) {
  let loadedSuggestions: string[] = [];

  const parsedMessages = messages.map((message): AgentMessage => {
    let content = message.content;
    const suggestionsMatch = content.match(/<!--suggestions:(\[.*?\])-->/);
    if (suggestionsMatch) {
      try {
        loadedSuggestions = JSON.parse(suggestionsMatch[1]);
      } catch {
        loadedSuggestions = [];
      }
      content = content.replace(/<!--suggestions:\[.*?\]-->/, '').trim();
    }

    const images: { style: string; url: string; prompt: string }[] = [];
    const imageRegex = /!\[(.+?)\]\((.+?)\)/g;
    let match: RegExpExecArray | null;
    while ((match = imageRegex.exec(content)) !== null) {
      images.push({ style: match[1], url: match[2], prompt: '' });
    }

    return {
      role: message.role === 'user' ? 'user' : 'ai',
      content,
      images: images.length > 0 ? images : undefined,
    };
  });

  return { messages: parsedMessages, suggestedQuestions: loadedSuggestions };
}

export function useConversation(options: UseConversationOptions) {
  const refreshConversationHistory = useCallback(() => {
    apiJson<ConvHistory[]>('/api/conversations')
      .then((data) => options.setConvHistory(data))
      .catch(() => {});
  }, [options.setConvHistory]);

  useEffect(() => {
    refreshConversationHistory();
  }, [refreshConversationHistory]);

  const syncCurrentConversationToCache = useCallback(() => {
    const conversationId = options.sseConvIdRef.current || options.currentConvId;
    if (!conversationId) return;

    options.convCacheRef.current.set(conversationId, {
      messages: [...options.messages],
      isLoading: options.isLoading,
      workflowPhase: options.workflowPhase,
      nodeStatus: options.nodeStatus ? { ...options.nodeStatus } : null,
      conversationTitle: options.conversationTitle,
      suggestedQuestions: [...options.suggestedQuestionsRef.current],
    });
  }, [
    options.convCacheRef,
    options.conversationTitle,
    options.currentConvId,
    options.isLoading,
    options.messages,
    options.nodeStatus,
    options.sseConvIdRef,
    options.suggestedQuestionsRef,
    options.workflowPhase,
  ]);

  const restoreCachedConversation = useCallback((conversationId: number, cached: ConversationTaskCacheEntry) => {
    options.setMessages(cached.messages);
    options.setIsLoading(cached.isLoading);
    options.setWorkflowPhase(cached.workflowPhase);
    options.setNodeStatus(cached.nodeStatus);
    options.setConversationOpen(true);
    options.setConversationTitle(cached.conversationTitle);
    options.setCurrentConvId(conversationId);
    options.convIdRef.current = conversationId;
    options.sseConvIdRef.current = conversationId;
    options.setIsImageMode(false);
    options.setSuggestedQuestions(cached.suggestedQuestions || []);
    options.setActivePage('home');
  }, [
    options.convIdRef,
    options.sseConvIdRef,
    options.setActivePage,
    options.setConversationOpen,
    options.setConversationTitle,
    options.setCurrentConvId,
    options.setIsImageMode,
    options.setIsLoading,
    options.setMessages,
    options.setNodeStatus,
    options.setSuggestedQuestions,
    options.setWorkflowPhase,
  ]);

  const resetConversation = useCallback((resetOptions: ResetConversationOptions = {}) => {
    options.setConversationOpen(resetOptions.open ?? false);
    options.setMessages([]);
    options.setConversationTitle('新对话');
    options.setCurrentConvId(null);
    options.convIdRef.current = null;
    options.sseConvIdRef.current = null;
    if (resetOptions.clearLoading ?? true) {
      options.setIsLoading(false);
    }
    options.setWorkflowPhase('idle');
    options.setNodeStatus(null);
    options.setInputText(resetOptions.inputText ?? '');
    options.setIsImageMode(resetOptions.imageMode ?? false);
    options.setSuggestedQuestions([]);
    options.setActiveNodeId('');
    if (resetOptions.activePage) {
      options.setActivePage(resetOptions.activePage);
    }
  }, [
    options.convIdRef,
    options.sseConvIdRef,
    options.setActiveNodeId,
    options.setActivePage,
    options.setConversationOpen,
    options.setConversationTitle,
    options.setCurrentConvId,
    options.setInputText,
    options.setIsImageMode,
    options.setIsLoading,
    options.setMessages,
    options.setNodeStatus,
    options.setSuggestedQuestions,
    options.setWorkflowPhase,
  ]);

  const openHomeConversation = useCallback(() => {
    if (options.currentConvId && options.activePage !== 'home' && (options.messages.length > 0 || options.isLoading)) {
      syncCurrentConversationToCache();
    }

    const activeCached = options.currentConvId ? options.convCacheRef.current.get(options.currentConvId) : null;
    if (activeCached && activeCached.isLoading) {
      restoreCachedConversation(options.currentConvId as number, activeCached);
      return;
    }

    if (options.isLoading) {
      options.setConversationOpen(true);
      options.setIsImageMode(false);
      options.setActivePage('home');
      return;
    }

    resetConversation({ activePage: 'home', clearLoading: false });
  }, [
    options.activePage,
    options.convCacheRef,
    options.currentConvId,
    options.isLoading,
    options.messages.length,
    options.setActivePage,
    options.setConversationOpen,
    options.setIsImageMode,
    resetConversation,
    restoreCachedConversation,
    syncCurrentConversationToCache,
  ]);

  const loadConversation = useCallback((conversationId: number) => {
    if (options.currentConvId && (options.messages.length > 0 || options.isLoading)) {
      syncCurrentConversationToCache();
    }

    const cached = options.convCacheRef.current.get(conversationId);
    if (cached && cached.isLoading) {
      restoreCachedConversation(conversationId, cached);
      return;
    }

    apiJson<ConversationRecord>(`/api/conversations/${conversationId}`)
      .then((conversation) => {
        if (!conversation?.messages) return;

        const parsed = parseConversationMessages(conversation.messages);
        const cachedSuggestions = options.convCacheRef.current.get(conversation.id)?.suggestedQuestions;

        options.setMessages(parsed.messages);
        options.setConversationOpen(true);
        options.setConversationTitle(conversation.title);
        options.setCurrentConvId(conversation.id);
        options.convIdRef.current = conversation.id;
        options.sseConvIdRef.current = conversation.id;
        options.setIsLoading(false);
        options.setWorkflowPhase('idle');
        options.setNodeStatus(null);
        options.setIsImageMode(false);
        options.setSuggestedQuestions(cachedSuggestions || parsed.suggestedQuestions);
        options.setActiveNodeId(conversation.node_id || '');
        options.setActivePage('home');
      })
      .catch(() => {});
  }, [
    options.convCacheRef,
    options.convIdRef,
    options.currentConvId,
    options.isLoading,
    options.messages.length,
    options.setActiveNodeId,
    options.setActivePage,
    options.setConversationOpen,
    options.setConversationTitle,
    options.setCurrentConvId,
    options.setIsImageMode,
    options.setIsLoading,
    options.setMessages,
    options.setNodeStatus,
    options.setSuggestedQuestions,
    options.setWorkflowPhase,
    options.sseConvIdRef,
    restoreCachedConversation,
    syncCurrentConversationToCache,
  ]);

  const deleteConversation = useCallback((conversationId: number, event?: MouseEvent) => {
    event?.stopPropagation();
    apiJson<{ status: string }>(`/api/conversations/${conversationId}`, { method: 'DELETE' })
      .then(() => {
        options.setConvHistory((prev) => prev.filter((conversation) => conversation.id !== conversationId));
        options.convCacheRef.current.delete(conversationId);
        options.setOpenHistoryMenu(null);
        if (options.currentConvId === conversationId) {
          resetConversation({ activePage: 'home' });
        }
        options.showToast?.({ message: '对话已删除', variant: 'success' });
      })
      .catch(() => {
        options.showToast?.({ message: '删除对话失败', variant: 'error' });
      });
  }, [
    options.convCacheRef,
    options.currentConvId,
    options.setConvHistory,
    options.setOpenHistoryMenu,
    options.showToast,
    resetConversation,
  ]);

  const renameConversation = useCallback((conversationId: number, title: string) => {
    apiJson<{ status: string }>(`/api/conversations/${conversationId}/rename`, {
      method: 'POST',
      body: JSON.stringify({ title }),
    })
      .then(() => {
        refreshConversationHistory();
        options.showToast?.({ message: '对话已重命名', variant: 'success' });
      })
      .catch(() => {
        options.showToast?.({ message: '重命名失败，请稍后重试', variant: 'error' });
      });
    options.setOpenHistoryMenu(null);
  }, [options.setOpenHistoryMenu, options.showToast, refreshConversationHistory]);

  return {
    deleteConversation,
    loadConversation,
    openHomeConversation,
    refreshConversationHistory,
    renameConversation,
    resetConversation,
    syncCurrentConversationToCache,
  };
}
