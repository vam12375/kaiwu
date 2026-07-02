import { useCallback } from 'react';

import type { AgentTaskEvent } from '../api/tasks';

export type SseStreamOptions = {
  signal?: AbortSignal;
  onEvent: (event: AgentTaskEvent) => void;
};

export function useSseEvents() {
  const stream = useCallback(async (url: string, options: SseStreamOptions) => {
    const response = await fetch(url, {
      method: 'GET',
      headers: { Accept: 'text/event-stream' },
      signal: options.signal,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No SSE reader');

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split('\n\n');
      buffer = frames.pop() || '';

      for (const frame of frames) {
        const dataLines = frame
          .split('\n')
          .filter((line) => line.startsWith('data: '))
          .map((line) => line.slice(6));
        if (!dataLines.length) continue;
        let event: AgentTaskEvent | null = null;
        try {
          event = JSON.parse(dataLines.join('\n'));
        } catch {}
        if (event) options.onEvent(event);
      }
    }

    if (buffer.trim()) {
      const dataLine = buffer.split('\n').find((line) => line.startsWith('data: '));
      if (dataLine) {
        let event: AgentTaskEvent | null = null;
        try {
          event = JSON.parse(dataLine.slice(6));
        } catch {}
        if (event) options.onEvent(event);
      }
    }
  }, []);

  return { stream };
}
