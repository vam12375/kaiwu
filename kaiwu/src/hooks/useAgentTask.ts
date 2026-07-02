import { useCallback, useRef, useState } from 'react';

import {
  cancelTaskRequest,
  createTask,
  retryTaskRequest,
  taskEventsUrl,
  type AgentTaskEvent,
  type AgentTaskStatus,
  type CreateTaskPayload,
} from '../api/tasks';
import { useSseEvents } from './useSseEvents';

type TaskRunCallbacks = {
  onEvent?: (event: AgentTaskEvent) => void;
  onError?: (error: unknown) => void;
  onDone?: () => void;
};

const EVENT_STATUS: Record<string, AgentTaskStatus> = {
  task_created: 'queued',
  analyzing: 'routing',
  node_selected: 'running',
  progress: 'running',
  response_start: 'streaming',
  content: 'streaming',
  svg_gen_start: 'streaming',
  image_gen_start: 'streaming',
  file_saved: 'saving',
  done: 'completed',
  error: 'failed',
  cancelled: 'cancelled',
};

export function useAgentTask() {
  const { stream } = useSseEvents();
  const [status, setStatus] = useState<AgentTaskStatus>('created');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [events, setEvents] = useState<AgentTaskEvent[]>([]);
  const abortRef = useRef<AbortController | null>(null);

  const runTask = useCallback(
    async (payload: CreateTaskPayload, callbacks: TaskRunCallbacks = {}) => {
      const controller = new AbortController();
      abortRef.current = controller;
      setEvents([]);

      try {
        const created = await createTask(payload, controller.signal);
        setTaskId(created.task_id);
        setStatus(created.task.status);

        await stream(taskEventsUrl(created.task_id), {
          signal: controller.signal,
          onEvent: (event) => {
            setEvents((prev) => [...prev, event]);
            if (EVENT_STATUS[event.type]) {
              setStatus(EVENT_STATUS[event.type]);
            }
            callbacks.onEvent?.(event);
          },
        });
        callbacks.onDone?.();
      } catch (error) {
        callbacks.onError?.(error);
        throw error;
      } finally {
        abortRef.current = null;
      }
    },
    [stream],
  );

  const cancelTask = useCallback(async () => {
    const activeTaskId = taskId;
    if (activeTaskId) {
      await cancelTaskRequest(activeTaskId).catch(() => {});
    }
    abortRef.current?.abort();
    abortRef.current = null;
    setStatus('cancelled');
  }, [taskId]);

  const retryTask = useCallback(
    async (callbacks: TaskRunCallbacks = {}) => {
      if (!taskId) return;
      const response = await retryTaskRequest(taskId);
      setTaskId(response.task_id);
      setStatus(response.task.status);
      await stream(taskEventsUrl(response.task_id), {
        onEvent: (event) => {
          setEvents((prev) => [...prev, event]);
          if (EVENT_STATUS[event.type]) {
            setStatus(EVENT_STATUS[event.type]);
          }
          callbacks.onEvent?.(event);
        },
      });
      callbacks.onDone?.();
    },
    [stream, taskId],
  );

  return {
    status,
    taskId,
    events,
    sendMessage: runTask,
    cancelTask,
    retryTask,
  };
}

