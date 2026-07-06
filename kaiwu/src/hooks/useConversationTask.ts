import { useCallback } from 'react';
import type { Dispatch, RefObject, SetStateAction } from 'react';

import { apiJson } from '../api/client';
import type { AgentTaskEvent } from '../api/tasks';
import type { ConvHistory, SidebarPage } from '../types';
import {
  type AgentEventState,
  type AgentMessage,
} from './agentEventReducer';
import { createAgentTaskController } from './agentTaskController';
import { useAgentTask } from './useAgentTask';

type WorkflowPhase = 'idle' | 'analyzing' | 'executing' | 'responding';

type NodeStatus = {
  nodeId: string;
  nodeName: string;
  nodeIcon: string;
  progress: number;
  message: string;
};

type ProjectImage = {
  name: string;
  url: string;
  size: number;
  modified: string;
};

export type ConversationTaskCacheEntry = {
  messages: AgentMessage[];
  isLoading: boolean;
  workflowPhase: WorkflowPhase;
  nodeStatus: NodeStatus | null;
  conversationTitle: string;
  suggestedQuestions?: string[];
};

type MutableRef<T> = {
  current: T;
};

type UseConversationTaskOptions = {
  homeTextareaRef: RefObject<HTMLTextAreaElement | null>;
  convTextareaRef: RefObject<HTMLTextAreaElement | null>;
  convIdRef: MutableRef<number | null>;
  followupNodeRef: MutableRef<string | null>;
  sseConvIdRef: MutableRef<number | null>;
  suggestedQuestionsRef: MutableRef<string[]>;
  convCacheRef: MutableRef<Map<number, ConversationTaskCacheEntry>>;
  inputText: string;
  isLoading: boolean;
  messages: AgentMessage[];
  activeNodeId: string;
  conversationTitle: string;
  imageRatio: string;
  imageCount: number;
  modelId: string;
  setInputText: Dispatch<SetStateAction<string>>;
  setSuggestedQuestions: (items: string[]) => void;
  setMessages: Dispatch<SetStateAction<AgentMessage[]>>;
  setConversationOpen: Dispatch<SetStateAction<boolean>>;
  setConversationTitle: Dispatch<SetStateAction<string>>;
  setIsLoading: Dispatch<SetStateAction<boolean>>;
  setWorkflowPhase: Dispatch<SetStateAction<WorkflowPhase>>;
  setNodeStatus: Dispatch<SetStateAction<NodeStatus | null>>;
  setActiveNodeId: Dispatch<SetStateAction<string>>;
  setCurrentConvId: Dispatch<SetStateAction<number | null>>;
  setConvHistory: Dispatch<SetStateAction<ConvHistory[]>>;
  setProjectImages: Dispatch<SetStateAction<ProjectImage[]>>;
  setActivePage: Dispatch<SetStateAction<SidebarPage>>;
  setCodingMode: Dispatch<SetStateAction<'preview' | 'code'>>;
};

const REPORT_COMMAND_KEYWORDS = [
  '调研报告',
  '调研',
  '市场调研',
  '商业方案',
  '品牌落地',
  '商业策划',
  '品牌手册',
  '商业计划书',
  '营销方案',
  '营销策划',
  '营销解决方案',
  '营销手册',
  '生成营销手册',
  '提炼品牌精神',
  '生成品牌屋',
  '生成logo',
  '设计logo',
  'logo',
  '做什么产品',
  '做哪些产品',
  '做产品',
  '产品规划',
  '设计产品',
  '生成产品手册',
  '产品手册',
  '产品落地手册',
  '生成系统化内容营销解决方案',
  '导出',
  '开始调研',
  '做商业方案',
  '产品设计',
  '营销素材',
  '品牌设计',
];

function scrollConversationToBottom() {
  window.setTimeout(() => {
    const el = document.getElementById('doubao-messages');
    if (el) el.scrollTop = el.scrollHeight;
  }, 50);
}

function getErrorMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  if (typeof error === 'string') return error;
  return '未知错误';
}

export function useConversationTask(options: UseConversationTaskOptions) {
  const agentTask = useAgentTask();

  const refreshHistory = useCallback(() => {
    apiJson<ConvHistory[]>('/api/conversations')
      .then((data) => options.setConvHistory(data))
      .catch(() => {});
  }, [options]);

  const refreshProjectImages = useCallback(() => {
    apiJson<ProjectImage[]>('/api/project-images')
      .then((data) => options.setProjectImages(data))
      .catch(() => {});
  }, [options]);

  const stopGeneration = useCallback(() => {
    void agentTask.cancelTask();
    options.setIsLoading(false);
    options.setWorkflowPhase('idle');
    options.setNodeStatus(null);
  }, [agentTask, options]);

  const handleSend = useCallback(async () => {
    const text = (
      options.homeTextareaRef.current?.value ||
      options.convTextareaRef.current?.value ||
      options.inputText
    ).trim();
    if (!text || options.isLoading) return;

    const isReportCommand = REPORT_COMMAND_KEYWORDS.some((keyword) => text.includes(keyword));
    if (isReportCommand) {
      options.followupNodeRef.current = null;
    } else if (!options.followupNodeRef.current && options.messages.length > 0 && options.activeNodeId) {
      options.followupNodeRef.current = options.activeNodeId;
    }

    if (options.homeTextareaRef.current) options.homeTextareaRef.current.value = '';
    if (options.convTextareaRef.current) options.convTextareaRef.current.value = '';
    options.setInputText('');
    // suggestedQuestions 由 runPrompt 按需清理——推进流程清，导出报告不清

    const nextConversationTitle = text.slice(0, 20) + (text.length > 20 ? '...' : '');
    const userMessage: AgentMessage = { role: 'user', content: text };
    const aiPlaceholder: AgentMessage = { role: 'ai', content: '' };
    let latestMessages: AgentMessage[] = [...options.messages, userMessage, aiPlaceholder];

    options.setMessages((prev) => [...prev, userMessage]);
    options.setConversationOpen(true);
    options.setConversationTitle(nextConversationTitle);
    options.setIsLoading(true);
    options.setWorkflowPhase('analyzing');
    options.setNodeStatus(null);
    options.setMessages((prev) => [...prev, aiPlaceholder]);

    let eventState: AgentEventState = {
      aiContent: '',
      images: [],
      svgLogos: [],
      messages: latestMessages,
      conversationId: options.convIdRef.current,
      conversationTitle: nextConversationTitle,
      nodeId: options.activeNodeId,
    };

    const controller = createAgentTaskController({
      getState: () => eventState,
      setState: (state) => {
        eventState = state;
        latestMessages = state.messages;
      },
      setMessages: options.setMessages,
      setWorkflowPhase: options.setWorkflowPhase,
      setNodeStatus: options.setNodeStatus,
      setActiveNodeId: options.setActiveNodeId,
      setSuggestedQuestions: options.setSuggestedQuestions,
      setCurrentConversationId: (conversationId) => {
        options.setCurrentConvId(conversationId);
        options.convIdRef.current = conversationId;
        options.sseConvIdRef.current = conversationId;
      },
      refreshHistory,
      refreshProjectImages,
      openCodingPreview: () => {
        options.setActivePage('coding');
        options.setCodingMode('preview');
      },
    });

    scrollConversationToBottom();
    options.sseConvIdRef.current = options.convIdRef.current;

    try {
      await agentTask.sendMessage(
        {
          message: text,
          history: options.messages.slice(-10),
          stream: true,
          image_ratio: options.imageRatio,
          image_count: options.imageCount,
          followup_node: options.followupNodeRef.current,
          model: options.modelId,
          conversation_id: options.convIdRef.current,
        },
        {
          onEvent: (data: AgentTaskEvent) => controller.handleEvent(data),
        },
      );
    } catch (error: unknown) {
      if (error instanceof Error && error.name === 'AbortError') {
        controller.stop();
      } else {
        controller.fail(`请求异常：${getErrorMessage(error)}`);
      }
      options.setWorkflowPhase('idle');
      options.setNodeStatus(null);
    } finally {
      options.setIsLoading(false);
      options.followupNodeRef.current = null;

      const cachedConversationId = options.sseConvIdRef.current;
      if (cachedConversationId) {
        options.convCacheRef.current.set(cachedConversationId, {
          messages: [...latestMessages],
          isLoading: false,
          workflowPhase: 'idle',
          nodeStatus: null,
          conversationTitle: eventState.conversationTitle || nextConversationTitle,
          suggestedQuestions: [...options.suggestedQuestionsRef.current],
        });
      }
    }
  }, [agentTask, options, refreshHistory, refreshProjectImages]);

  return {
    status: agentTask.status,
    taskId: agentTask.taskId,
    events: agentTask.events,
    retryTask: agentTask.retryTask,
    handleSend,
    stopGeneration,
  };
}
