# 修复图片库预览元数据信息缺失

## Goal

图片库预览弹层右侧参考信息区域应展示图片生成时的提示词、模型、比例和画质；当前这些字段显示为“暂无提示词信息 / 未知模型 / 未知比例 / 未知画质”，用户无法基于图库图片复用或判断生成参数。

## What I Already Know

* 用户截图显示问题发生在图片库预览弹层右侧详情栏，红框区域缺少图片提示词、模型、比例、画质信息。
* 同一详情栏仍能展示大小、更新时间、来源，说明弹层已拿到基础文件信息，但缺少生成元数据或映射失败。
* 项目要求 AI 生成文件保留双归档：对应分类文件夹 + `AI 对话产出`。
* `kaiwu/src/features/layout/ProjectImagePreviewModal.tsx` 已读取 `ProjectImage.prompt/model/ratio/resolution` 并提供兜底文案。
* `kaiwuback/server/api/routes_files.py` 的 `/api/project-images` 源码会把 `get_project_image_metadata_map()` 合并到图片列表项。
* `kaiwuback/project-images/.image-meta.json` 已包含截图中 2026-07-07 10:57 图片的提示词、模型、比例、画质。
* 本地源码直接组装图片列表时能返回元数据；运行中的 `localhost:5001` 服务重启前未返回元数据，重启后已返回。

## Assumptions

* 图片生成任务在前端或后端某处已经持有提示词、模型、比例、画质，修复优先复用现有数据链路。
* 如果历史图片本身没有保存这些元数据，前端应继续使用清晰的兜底文案，新生成图片应展示完整信息。

## Requirements

* 图片库预览弹层应优先展示真实提示词、模型、比例、画质。
* 数据字段命名在前后端之间保持一致，避免只在 UI 层硬编码兜底。
* 没有历史元数据时保持稳定兜底，不影响预览、切换、下载。

## Acceptance Criteria

* [x] 选中包含生成元数据的图片时，接口返回真实提示词、模型、比例、画质。
* [x] 选中缺少生成元数据的历史图片时，现有弹层仍显示兜底信息且无运行错误。
* [x] 图片预览弹层缩略图切换后，详情信息跟随当前图片更新（由现有 `image = images[safeIndex]` 渲染链路保证）。
* [ ] 相关前端构建或后端语法检查通过。

## Definition of Done

* 相关代码遵循 `.trellis/spec/` 中前端/后端约定。
* 必要的 lint / typecheck / build / compile 检查通过，或明确说明未运行原因。
* 不改动无关未提交文件，不回退用户已有改动。

## Out of Scope

* 不重做图片库弹层视觉设计。
* 不批量回填历史文件元数据，除非现有存储中已经可无损推导。
* 不改变普通对话按钮和 AI 生图按钮的业务区分。

## Technical Notes

* 检查过：图片库弹层组件、`ProjectImage` 类型、`/api/project-images`、`.image-meta.json`、AI 生图保存与归档链路。
* 2026-07-07 运行时处理：停止旧 `kaiwuback/main.py` 进程并重新启动后端，重新请求 `http://localhost:5001/api/project-images`，首张 `AI生图_97245487_20260707105727.jpg` 返回 `prompt=true`、`model=doubao-seedream-4-5-251128`、`ratio=9:16`、`resolution=4K`、`source=AI 生图`。
* 本次没有新增业务代码；问题是服务进程未加载当前后端元数据合并逻辑。前端可能需要刷新页面或重新打开图片库以拉取新响应。
