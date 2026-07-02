# Frontend State Management

> How state is owned and synchronized in the React app.

---

## Overview

The project does not use Redux, Zustand, React Query, or a global context store. `App.tsx` owns top-level UI state and passes state/setters into hooks and feature components.

This is the current reality, not necessarily the final ideal. Keep new state close to its owner and avoid adding a global store as part of unrelated feature work.

---

## State Categories

### Top-Level UI State

Owned by `App.tsx`:

- navigation: `activePage`, `activeDirection`, `sidebarCollapsed`
- modals/popovers: `skillModal`, `projectModal`, `libraryModal`, picker booleans
- conversation display: `messages`, `isLoading`, `conversationTitle`, `nodeStatus`, `workflowPhase`
- AI mode controls: `isImageMode`, `imageRatio`, `imageCount`
- project/skill data loaded from backend

### Task Transport State

Owned by `useAgentTask()`:

- `taskId`
- task `status`
- raw task `events`
- active abort controller

### Conversation Orchestration State

Owned across `useConversationTask()` and `useConversation()`:

- optimistic user/AI placeholder messages
- active conversation ID refs
- follow-up node ref
- per-conversation cache in `convCacheRef`
- suggested questions cache

### Server State

Fetched from the backend and stored in React state:

- conversation history from `/api/conversations`
- project images from `/api/project-images`
- project files from `/api/project-files`
- external skills from `/api/skills`
- uploaded files from `/api/uploaded-files`

### Skill Library State

`useSkillLibrary()` owns the usable skill-library workflow:

- Fetch repository-backed external skills through `src/api/skills.ts`.
- Merge external skills with static market skills from `data.ts`.
- Persist user-level installed, enabled, and custom skills in `localStorage`.
- Expose derived `skillItems`, `installedSkillIds`, `enabledSkillIds`, search query state, and install/manage/custom-skill actions to `App.tsx`.

Keep skill install/manage behavior out of `MainStage.tsx` and `AppModals.tsx`; those components should render state and call hook actions passed from `App.tsx`.

---

## Single Owner Rules

### Task Conversation Save

For task-driven AI conversations, backend `AgentRuntime` owns conversation saving. The frontend should update current conversation state only after receiving `conversation_saved`.

Do not call `/api/conversations/save` for the same task flow. That endpoint remains for manual/legacy save scenarios.

### Current Conversation ID

Keep `currentConvId`, `convIdRef`, and `sseConvIdRef` synchronized when loading, creating, or restoring conversations. Async event handlers should read refs, not stale closure values.

### Suggested Questions

Suggested questions are stored in React state and `suggestedQuestionsRef` so final conversation cache writes include the latest values.

### Image Mode

`isImageMode` controls composer button shape:

- `false`: normal conversation buttons (`参考历史文件`, `上传文件`).
- `true`: image ratio and image count controls.

Only AI image generation should enter image mode. Do not make AI video or AI coding reuse image-mode controls.

---

## Conversation Cache

`convCacheRef` stores live UI state by conversation ID:

- messages
- loading flag
- workflow phase
- node status
- title
- suggested questions

Use it when switching pages or conversations during an active task so the in-progress UI can be restored.

---

## Derived State

Prefer deriving from existing state inside render or hooks:

- `quickSkills` comes from `quickSkillsByDirection[activeDirection]`.
- `nodeAction` comes from `NODE_ACTIONS[activeNodeId]`.
- project folder counts derive from `projectImages` and `realProjectFiles`.

Avoid duplicating derived values into separate state unless async callbacks require a ref.

---

## Common Mistakes

- Promoting local component-only popover state into top-level state without need.
- Adding a second source of truth for conversation ID.
- Resetting `isLoading` without also resetting `workflowPhase` and `nodeStatus`.
- Breaking active task cache restore when navigating away from home.
- Treating backend server state as permanent frontend state without refreshing after `file_saved` or `conversation_saved`.
