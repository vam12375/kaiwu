# 设置 favicon 使用 logo2

## Goal

将浏览器标签页 favicon 设置为 `kaiwu/public/logo2-800.webp`，让页面标签左侧显示项目提供的品牌图标，而不是浏览器默认图标。

## What I already know

* 用户指定使用 `kaiwu/public/logo2-800.webp` 作为 favicon。
* `kaiwu/index.html` 当前没有 favicon `link` 声明。
* `kaiwu/public/` 是 Vite 静态资源目录，资源可用根路径 `/logo2-800.webp` 引用。

## Assumptions

* 本任务只配置 favicon，不替换页面侧边栏 logo 或其他 UI 图片。
* 继续使用 PNG favicon；不新增转换后的 `.ico` 文件。

## Requirements

* 在前端 HTML 入口中声明 favicon。
* favicon 指向现有静态资源 `logo2-800.webp`。
* 不触碰无关后端配置和已有未提交改动。

## Acceptance Criteria

* [ ] `kaiwu/index.html` 包含指向 `/logo2-800.webp` 的 favicon 声明。
* [ ] 前端生产构建通过。
* [ ] 除必要任务文件和入口 HTML 外，不修改无关文件。

## Out of Scope

* 修复现有标题或其他中文 mojibake。
* 重新设计 logo、压缩图片或新增多尺寸 favicon 资产。

## Technical Notes

* 相关规范：`.trellis/spec/frontend/index.md`、`.trellis/spec/frontend/directory-structure.md`、`.trellis/spec/frontend/quality-guidelines.md`、`.trellis/spec/guides/index.md`。
