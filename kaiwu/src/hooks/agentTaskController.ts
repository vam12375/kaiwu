import type { AgentTaskEvent } from '../api/tasks';
import type { ShowToast } from '../types';
import {
  errorAgentEventState,
  reduceAgentEvent,
  stopAgentEventState,
  type AgentEventState,
  type AgentMessage,
} from './agentEventReducer';

type WorkflowPhase = 'idle' | 'analyzing' | 'executing' | 'responding';

type NodeStatus = {
  nodeId: string;
  nodeName: string;
  nodeIcon: string;
  progress: number;
  message: string;
};

type AgentTaskControllerDeps = {
  getState: () => AgentEventState;
  setState: (state: AgentEventState) => void;
  setMessages: (messages: AgentMessage[]) => void;
  setWorkflowPhase: (phase: WorkflowPhase) => void;
  setNodeStatus: (status: NodeStatus | null | ((prev: NodeStatus | null) => NodeStatus | null)) => void;
  setActiveNodeId: (nodeId: string) => void;
  setSuggestedQuestions: (items: string[]) => void;
  setCurrentConversationId: (conversationId: number) => void;
  refreshHistory: () => void;
  refreshProjectImages: () => void;
  openCodingPreview: () => void;
  showToast?: ShowToast;
};

export function createAgentTaskController(deps: AgentTaskControllerDeps) {
  const syncMessageState = (state: AgentEventState) => {
    deps.setState(state);
    deps.setMessages(state.messages);
  };

  const handleReducedSideEffects = (event: AgentTaskEvent, state: AgentEventState) => {
    if (event.type === 'image') {
      deps.refreshProjectImages();
      return;
    }

    if (event.type === 'file_saved') {
      deps.refreshProjectImages();
      deps.showToast?.({ message: event.message || '文件已保存', variant: 'success' });
      if (event.auto_preview) {
        deps.openCodingPreview();
      }
      return;
    }

    if (event.type === 'conversation_saved') {
      if (state.conversationId) {
        deps.setCurrentConversationId(state.conversationId);
      }
      deps.refreshHistory();
      deps.showToast?.({ message: '对话已保存', variant: 'success' });
    }
  };

  const handleEvent = (event: AgentTaskEvent) => {
    const reduced = reduceAgentEvent(deps.getState(), event);
    if (reduced.handled) {
      syncMessageState(reduced.state);
      handleReducedSideEffects(event, reduced.state);
      return;
    }

    if (event.type === 'analyzing') {
      deps.setNodeStatus({ nodeId: '', nodeName: '', nodeIcon: '🔍', progress: 5, message: event.message });
      return;
    }

    if (event.type === 'node_selected') {
      deps.setWorkflowPhase('executing');
      deps.setNodeStatus({
        nodeId: event.node,
        nodeName: event.name,
        nodeIcon: event.icon,
        progress: 10,
        message: `已匹配「${event.name}」引擎`,
      });
      deps.setActiveNodeId(event.node);
      deps.setState({ ...deps.getState(), nodeId: event.node });
      return;
    }

    if (event.type === 'progress') {
      deps.setNodeStatus((prev) => (prev ? { ...prev, progress: event.percent, message: event.message } : null));
      return;
    }

    if (event.type === 'response_start') {
      deps.setWorkflowPhase('responding');
      deps.setNodeStatus(null);
      return;
    }

    if (event.type === 'image_gen_start') {
      deps.setNodeStatus({
        nodeId: '',
        nodeName: event.label || '图片生成',
        nodeIcon: '🎨',
        progress: 97,
        message: event.message || `正在生成 ${event.count} 张图片...`,
      });
      deps.setWorkflowPhase('executing');
      return;
    }

    if (event.type === 'suggestions') {
      deps.setSuggestedQuestions(event.items || []);
      return;
    }

    if (event.type === 'cancelled') {
      syncMessageState(stopAgentEventState(deps.getState()));
      deps.setWorkflowPhase('idle');
      deps.setNodeStatus(null);
      return;
    }

    if (event.type === 'error') {
      syncMessageState(errorAgentEventState(deps.getState(), `请求异常：${event.message || '任务执行失败'}`));
      deps.setWorkflowPhase('idle');
      deps.setNodeStatus(null);
      deps.showToast?.({ message: event.message || '任务执行失败', variant: 'error' });
      return;
    }

    if (event.type === 'done') {
      deps.showToast?.({ message: '生成完成', variant: 'success' });
    }
  };

  const stop = () => {
    syncMessageState(stopAgentEventState(deps.getState()));
  };

  const fail = (message: string) => {
    syncMessageState(errorAgentEventState(deps.getState(), message));
  };

  return { handleEvent, stop, fail };
}

