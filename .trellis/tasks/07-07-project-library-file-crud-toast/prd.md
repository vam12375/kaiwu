# 项目库文件增删改查和提示

## Goal

补齐 Kaiwu 项目库中文件和文件夹的真实增删改查能力，让用户可以在现有项目库界面中创建、查看、重命名、删除文件夹，上传、查看、重命名、删除文件，并且所有轻量反馈统一使用公共 Toast，破坏性操作统一使用应用内确认弹层。

## Requirements

* 文件夹支持创建、查看、重命名、删除；创建和删除保留现有流程，新增重命名能力。
* 文件支持上传、查看详情、重命名、删除；上传和详情查看保留现有流程，新增重命名和删除能力。
* 所有成功/失败反馈使用 `ToastProvider` 暴露的公共 `showToast`，不使用浏览器原生 `alert()`。
* 删除文件夹和删除文件必须先通过 `ConfirmProvider` 的应用内确认弹层确认。
* 重命名后前端刷新项目库文件夹/文件列表，并保持用户在合理的当前视图中。
* 在项目库首页点击上传时需要选择保存到哪个文件夹；进入具体文件夹后点击上传时自动保存到当前文件夹，不再显示文件夹选择下拉。
* 后端接口继续限制项目库操作在 `PROJECT_LIB` / `IMG_STORE` 边界内，非法名称返回 `{"error": "..."}`。
* 保留 AI 生成文件双归档规则，不改 `/api/tasks`、SSE、对话保存链路。

## Acceptance Criteria

* [ ] 在项目库首页点击“新建文件夹”后，成功/失败均有公共 toast 提示，成功后文件夹列表刷新。
* [ ] 在项目库文件夹卡片上可触发重命名，提交后后端目录和元数据同步更新，前端刷新并提示成功。
* [ ] 删除文件夹先出现应用内确认弹层；确认后删除目录或清空/隐藏虚拟库，文件夹与文件列表刷新并提示成功。
* [ ] 在文件详情页可重命名当前文件，提交后文件名、URL、元数据刷新并提示成功。
* [ ] 在文件详情页可删除当前文件；确认后回到项目库列表并提示成功。
* [ ] 文件上传成功/失败继续使用公共 toast。
* [ ] 在文件夹详情页点击“上传文件”时，上传弹窗显示当前保存目标且不提供文件夹下拉选择。
* [ ] `npm run build` 通过，后端 `python -m compileall kaiwuback/server` 通过。

## Definition of Done

* 前端 API 调用集中在 `src/api/projectFiles.ts`。
* 项目库 UI 复用现有 `MainStage`/`AppModals`/全局样式，不引入新的全局状态库。
* 后端文件接口保持 `routes_files.py` 的薄 API 风格和 `{"error": "..."}` 错误形状。
* 破坏性操作不使用浏览器原生确认框。

## Technical Approach

后端在 `kaiwuback/server/api/routes_files.py` 增加文件重命名、文件删除、文件夹重命名接口，并复用现有名称校验、路径解析和 `.folder-meta.json` / `.file-meta.json` 元数据读写。前端在 `kaiwu/src/api/projectFiles.ts` 增加对应 API helper；`App.tsx` 持有项目库刷新、确认和 toast 串联；`MainStage.tsx` 增加项目库详情页动作入口；`AppModals.tsx` 复用项目库 modal 处理重命名表单。

## Decision (ADR-lite)

**Context**: 当前项目库已有列表、搜索、创建文件夹、上传文件、文件夹批量删除、文件详情页和公共 toast/confirm，但缺少完整的改/删文件能力以及重命名能力。

**Decision**: 采用薄后端 API + 前端刷新状态的方式补齐 CRUD，不引入数据库或新的状态管理。

**Consequences**: 文件系统仍是项目库事实来源，接口简单且便于本地开发；未来如需权限、回收站、协作审计，再把这些 API 下沉到专门 service。

## Out of Scope

* 权限管理、回收站、版本历史、批量文件操作。
* 改造 AI 产物保存逻辑或对话任务/SSE 流程。
* 将项目库数据迁移到数据库。

## Technical Notes

* 前端项目库主界面：`kaiwu/src/features/layout/MainStage.tsx`。
* 前端项目库弹窗：`kaiwu/src/features/layout/AppModals.tsx`。
* 前端 API helper：`kaiwu/src/api/projectFiles.ts`。
* 前端公共提示：`kaiwu/src/features/toast/ToastProvider.tsx`、`ConfirmProvider.tsx`。
* 后端文件路由：`kaiwuback/server/api/routes_files.py`。
* 相关规范已阅读：`.trellis/spec/frontend/*`、`.trellis/spec/backend/directory-structure.md`、`.trellis/spec/backend/error-handling.md`、`.trellis/spec/backend/quality-guidelines.md`。
