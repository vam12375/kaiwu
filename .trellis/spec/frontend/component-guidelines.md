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

The current app uses global class-based CSS plus CSS variables declared in `:root`. `src/styles.css` is the foundational/shared entrypoint; domain styles live under `src/styles/` and should be imported by the owning component when possible.

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

When adding durable CSS, choose the closest domain file under `src/styles/` (for example chat/conversation, project library, modals, home, settings, coding) and import it from the owning component. Only edit `src/styles.css` for base variables, shared controls, global animations, or legacy fallbacks, and treat import order as part of the cascade contract.

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

### Scenario: AI Markdown Table Rendering

#### 1. Scope / Trigger

- Trigger: any change to AI Markdown table rendering in `src/utils.ts`, table CSS under `src/styles/conversation/`, or backend exported report table rendering.
- This is a cross-layer contract because live chat uses `renderMarkdown()` while exported HTML reports use `kaiwuback/server/utils/markdown.py` plus `kaiwuback/server/utils/report_html.py`.

#### 2. Signatures

- Frontend renderer: `renderMarkdown(content: string): string`.
- Frontend table CSS classes: `.md-table`, `.md-table-cols-<n>`, `.md-td-right`, `.md-td-rich`, `.md-td-compact`.
- Backend renderer parity points: `markdown_to_html(text: str) -> str`, backend table classes `table-cols-<n>`, `cell-right`, `cell-rich`, `cell-compact`.

#### 3. Contracts

- Markdown tables must emit a `colgroup` with percentage widths derived from header semantics and body content length.
- Short/numeric columns such as `序号`, `年份`, `同比增速`, `市占率`, and `市场规模` should occupy less width than descriptive columns such as `核心特征`, `机会点`, `解决方案`, `痛点`, `说明`, `文案`, and `脚本`.
- Cells default to left alignment. Apply right alignment only via semantic classes for numeric/compact columns; never right-align the final column just because it is last.
- Table headers follow the same semantic alignment as their body column: left for descriptive/year/source fields, right for numeric/percentage fields, and centered only for compact categorical/comparison columns.
- Short categorical body columns such as `类目`, `维度`, `项目`, and `方式` may center-align when their values are compact; long descriptive and source/label fields stay left-aligned.
- Two-column compact comparison tables such as `竞争者 / 市占率(估)` center-align both body columns so short values do not drift to opposite table edges.
- First-column labels, year columns (`年份`/`年度`), and source/label fields such as `收入来源` and `数据来源` stay left-aligned even when their content is short.
- 2/3/4-column tables should fill the message content width; avoid shrinking short tables to a partial-width block.
- Rows with too many cells should merge overflow cells into the last column instead of dropping content.
- Keep frontend live chat and backend report export width/alignment rules materially consistent.

#### 4. Validation & Error Matrix

- `|---|---|` separator rows -> skipped, not rendered as content.
- Body row shorter than header -> pad missing cells as empty strings.
- Body row longer than header -> merge extra cells into the final cell with ` | `.
- Story/content-library tables with story IDs plus script/copy/platform fields -> render as accordion cards, not cramped wide tables.

#### 5. Good/Base/Bad Cases

- Good: `| 年份 | 市场规模（年份/口径） | 同比增速 | 数据来源 |` keeps `年份` and `数据来源` left-aligned while right-aligning only the market-size and growth columns.
- Base: a two-column `维度/说明` table gives the label column compact width and the explanation column most width.
- Base: table headers such as `年份` and `预测增速` sit above their own data because they use the same left/right alignment as body cells.
- Base: compact table headers such as `类目` and their compact body values can center-align together.
- Base: a two-column `竞争者/市占率(估)` table keeps competitor names and percentages centered under their headers rather than pinned to the left and right edges.
- Base: a two-column `方式/节奏` table still spans the full message width, not a half-width block.
- Bad: CSS such as `.md-table td:last-child { text-align: right; }`, because source/description/opportunity columns become hard to read.

#### 6. Tests Required

- Run `npm run build` from `kaiwu/`.
- For backend parity changes, also run `python -m compileall kaiwuback/server`.
- Smoke at least one 4-column market table and confirm generated HTML contains `colgroup`, a `*-cols-4` class, and no unconditional last-column right alignment.

#### 7. Wrong vs Correct

Wrong:

```css
.md-table td:last-child {
  text-align: right;
}
```

Correct:

```typescript
if (isRightAlignedTableColumn(header, bodyRows, index)) {
  classes.push('md-td-right');
}
```

---

## High-Volume Image Lists

For project-library grids or thumbnail strips that can render many stored images, do not assign original image URLs directly to every `<img>` at render time. Use `ProjectLazyImage` from `src/features/layout/ProjectLazyImage.tsx` or an equivalent IntersectionObserver-based component that only unlocks `src` near the viewport and limits concurrent image loads.

```tsx
<ProjectLazyImage src={image.url} alt={image.name} />
```

`ProjectImage.url` is a display URL and may point to a WebP preview. Download actions should prefer `image.original_url || image.url`, so users receive the original generated image when the backend provides one.

This prevents the browser from queueing dozens of original image requests at once, which can leave the visible gallery blank while offscreen images compete for network slots.

---

## Project File Detail Previews

Project library file entries expose `ProjectFile.type` as the backend file suffix uppercased without the dot, for example `.jpg` becomes `JPG`. Detail-page preview logic should branch by that type instead of assuming all inline previews can use the same renderer.

Use `<img>` for image file types and keep `iframe` for document-like file types such as HTML/PDF/TXT/MD/CSV/JSON:

```tsx
const PROJECT_FILE_FRAME_PREVIEW_TYPES = new Set(['HTML', 'HTM', 'PDF', 'TXT', 'MD', 'CSV', 'JSON']);
const PROJECT_FILE_IMAGE_PREVIEW_TYPES = new Set(['JPG', 'JPEG', 'PNG', 'WEBP', 'GIF', 'BMP', 'AVIF', 'SVG']);

const type = selectedProjectFile?.type?.toUpperCase() || '';
const isImagePreview = PROJECT_FILE_IMAGE_PREVIEW_TYPES.has(type);
const isFramePreview = PROJECT_FILE_FRAME_PREVIEW_TYPES.has(type);
```

Images should be rendered with `object-fit: contain` inside a stable preview container so large generated images do not stretch or resize the project detail layout. Unsupported file types should continue to show the existing unsupported-preview empty state.

---

## Project Folder Detail Editing

Project library folder summaries may include stable `id` and semantic `kind` fields. Use `folder.id || folder.name` for backend mutations, selection state, and refresh calls. Use `folder.kind === 'image_library'` to detect the image library, with `folder.name === '图片库'` only as a backward-compatible fallback.

Folder detail pages should keep the current folder controls in the same top row as “返回项目库”:

- normal mode: `重命名` opens the existing folder rename modal for the active folder, and `编辑` enters item selection mode.
- edit mode: `取消` clears selection, and `删除所选（n）` performs one confirmed batch delete.

For 图片库, item deletion should call the project image API so the backend removes the original image, preview cache, metadata, and 图片库 archive copy. For normal folders, batch deletion can reuse the project file delete API, but the UI should show one destructive confirmation for the whole selection rather than one per row.

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
