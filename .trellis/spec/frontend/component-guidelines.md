# Frontend Component Guidelines

> How React components are built in this project.

---

## Component Pattern

Use function components with typed props. Keep component files focused on rendering, UI event handlers, and composition.

Good references:

- `src/features/chat/ConversationPanel.tsx`
- `src/features/layout/AppSidebar.tsx`
- `src/features/chat/SidebarHistory.tsx`

`MainStage.tsx` currently uses `Record<string, any>` and contains several large inline screens. Treat this as transitional debt, not a pattern to expand. New substantial UI should be extracted into typed feature components rather than making `MainStage` larger.

---

## Props

Define prop types near the component when they are component-specific.

Local pattern:

- `ConversationPanelProps` captures UI state, setters, refs, and callbacks used by the chat panel.
- `AppSidebarProps` captures navigation and history actions.
- Small local types such as `NodeStatus`, `UploadedFile`, and `ResetConversationOptions` are defined near their component/hook owner.

Avoid adding broad `any` props. If a prop set becomes too large, extract a component or hook boundary.

---

## Styling

The current app uses global `src/styles.css` classes plus CSS variables declared in `:root`.

Use existing classes and CSS variables where possible:

- `--brand-deep`
- `--brand-accent`
- `--surface`
- `--surface-alt`
- `--border`
- `--text-primary`
- `--text-secondary`
- radius tokens such as `--radius-sm`, `--radius-md`, `--radius-lg`

Inline styles exist in a few generated preview/image sections, but new durable UI should prefer class names in `styles.css`. Use inline styles only for small dynamic values that are awkward to express as classes.

---

## Global Feedback

Use `ToastProvider` and the shared `ShowToast` type for lightweight app feedback such as save, delete, upload, copy, install, and generation-complete messages.

```tsx
showToast({ message: '文件已上传', variant: 'success' });
showToast({ message: '上传失败，请稍后重试', variant: 'error' });
```

Use `ConfirmProvider` for destructive confirmations when the user must explicitly approve an irreversible action. Do not use browser-native `alert()` or `window.confirm()` for product UI. Hooks should receive `showToast` as an option or callback and keep toast types imported from `src/types.ts`, not from feature component paths.

---

## Icons And Motion

Use existing dependencies:

- `lucide-react` for icon buttons and navigation icons.
- `framer-motion` for chat/message animations and transitions.

When adding icon-only buttons, include `title` and/or `aria-label`. Existing examples include sidebar collapse, send, save, copy, and stop buttons.

---

## Conversation UI Rules

Preserve these product rules from the memory document and current code:

- Normal conversations show `开物深思`, `参考历史文件`, and `上传文件` controls.
- Only AI image mode shows image ratio and image count controls.
- AI video and AI coding should use the normal conversation controls, not image-generation controls.
- User messages keep the user-side avatar behavior; only AI image generation may hide the AI avatar.
- Conversation three-dot/history menus must keep rename behavior.

References:

- `曜势科技项目・极简记忆唤醒文档.md`
- `src/features/chat/ConversationPanel.tsx`
- `src/features/chat/SidebarHistory.tsx`

---

## Rendering AI Content

Render AI markdown through `renderMarkdown()` from `src/utils.ts`, as `ConversationPanel` does. Do not manually parse markdown in components unless the renderer is being deliberately updated.

For task image/SVG events, use the `images` and `svgLogos` fields on `AgentMessage` produced by `agentEventReducer.ts`.

---

## Accessibility And Interaction

- Add `type="button"` to buttons that are not form submits.
- Add `aria-label` or `title` for icon-only controls.
- Preserve IME composition handling for Enter-to-send textareas.
- Keep stop/cancel controls reachable while `isLoading` is true.
- Avoid visible instructional text that explains obvious controls; use labels/tooltips and familiar icons.

---

## Common Mistakes

- Adding new API calls directly in JSX when an API helper/hook should own them.
- Expanding `MainStage.tsx` with another large untyped screen.
- Recreating SSE parsing in a component.
- Using emoji/text as the only affordance for a control that already has a lucide icon pattern.
- Breaking the image-mode-only ratio/count controls.
