import { API_BASE_URL, apiJson } from './client';

export type AgentTaskStatus =
  | 'created'
  | 'queued'
  | 'routing'
  | 'running'
  | 'streaming'
  | 'saving'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type AgentTask = {
  id: string;
  conversation_id?: number | null;
  status: AgentTaskStatus;
  node_id?: string | null;
  input?: Record<string, unknown>;
  result?: string | null;
  error?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type AgentTaskDebug = {
  id: string;
  status: AgentTaskStatus;
  node_id?: string | null;
  conversation_id?: number | null;
  event_count: number;
  last_seq: number;
  error?: string | null;
};

export type ImageReferenceInput = {
  name: string;
  mime_type: string;
  size: number;
  data_url: string;
};

export type CreateTaskPayload = {
  message: string;
  history?: unknown[];
  task_type?: 'chat' | 'image_generation';
  image_model?: string;
  image_ratio?: string;
  image_resolution?: string;
  image_count?: number;
  reference_images?: ImageReferenceInput[];
  followup_node?: string | null;
  model?: string;
  conversation_id?: number | null;
  stream?: boolean;
};

export type CreateTaskResponse = {
  task_id: string;
  task: AgentTask;
};

export type AgentTaskEvent = {
  type: string;
  task_id?: string;
  seq?: number;
  [key: string]: any;
};

export function createTask(payload: CreateTaskPayload, signal?: AbortSignal) {
  return apiJson<CreateTaskResponse>('/api/tasks', {
    method: 'POST',
    body: JSON.stringify(payload),
    signal,
  });
}

export function getTask(taskId: string) {
  return apiJson<AgentTaskDebug>(`/api/tasks/${taskId}`);
}

export function cancelTaskRequest(taskId: string) {
  return apiJson<{ status: string; task: AgentTask }>(`/api/tasks/${taskId}/cancel`, {
    method: 'POST',
  });
}

export function retryTaskRequest(taskId: string) {
  return apiJson<CreateTaskResponse>(`/api/tasks/${taskId}/retry`, {
    method: 'POST',
  });
}

export function taskEventsUrl(taskId: string, afterSeq = 0) {
  return `${API_BASE_URL}/api/tasks/${taskId}/events?after=${afterSeq}`;
}
