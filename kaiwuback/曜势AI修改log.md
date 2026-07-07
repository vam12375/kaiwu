# 开物AI产品左侧菜单栏改版方案

> 产品名变更：开物AI → **曜势科技**
> 改版范围：左侧菜单栏 + 创造模式节点绑定 + 文件存储规则
> 文档日期：2026-06-23

---

## 一、顶部产品名称修改

| 位置 | 当前值 | 修改为 |
|------|--------|--------|
| 侧边栏左上角标题 | `开物AI` | `曜势科技` |
| 对话页空状态标题 | `开物AI` | `曜势科技` |
| 对话页 AI 头像标识 | `K` | `曜` |
| HTML title | `Kaiwu Agent Workspace` | `曜势科技` |

**改动文件**：`src/App.tsx`

- 第 26 行附近：`sidebar-title-main` 文字从 `开物AI` → `曜势科技`
- 第 528 行附近：空状态 `h3` 从 `开物AI` → `曜势科技`
- 第 537 行附近：AI 头像 `K` → `曜`
- `index.html`：`<title>` 标签内容修改

---

## 二、左侧菜单栏修改

### 2.1 删除「自动任务」

| 操作 | 目标 |
|------|------|
| 删除 `sidebarItems` 中的 `{ key: 'automation', label: '自动任务', icon: FolderKanban }` | 整个栏目移除 |
| 删除相关 import 中的 `FolderKanban`（如不再被其他地方使用） | 清理引用 |

**改动文件**：`src/App.tsx`  第 25-31 行 `sidebarItems` 数组

**修改后菜单结构**：

```
曜势科技
├── 新对话        (home)       — 保留不变
├── 创造模式      (expert)     — 子功能重新绑定节点
├── 技能库        (skills)     — 保留不变
└── 项目库        (projects)   — 保留不变
```

---

### 2.2 「创造模式」子功能重新绑定节点

当前代码位置：`src/App.tsx` 第 445-450 行 `expert-subnav`

#### AI生图

| 维度 | 当前 | 修改为 |
|------|------|--------|
| 触发节点 | `setActivePage('image')` | 触发 **Node3**（Logo生成），即先打开对话页，自动发送生图请求到 Node3 |
| 点击行为 | 切换到独立的 image 页面 | `setConversationOpen(true)` + 自动填入「帮我设计品牌Logo」等 prompt，走 Node3 流程 |
| 输出内容 | 图片库展示 | Node3 输出 5 种风格 SVG + 通义万相效果图，结果存入项目库-图片库 |

**实现方式**：
```tsx
<button onClick={() => {
  setConversationOpen(false);
  setConversationOpen(true);
  setActivePage('home');
  // 预设 prompt 触发 Node3
  setInputText('');
  // 自动聚焦输入框
}} type="button">AI生图</button>
```

#### AI生视频

| 维度 | 当前 | 修改为 |
|------|------|--------|
| 触发节点 | `setActivePage('video')` | 触发 **Node3**（视频素材生成），复用 Logo 生成流程输出视频分镜/motion 素材 |
| 点击行为 | 切换到独立的 video 页面 | `setConversationOpen(true)` + 自动填入视频生成 prompt |

#### AI编程（拆分为两个入口）

| 当前 | 修改为 |
|------|--------|
| 单一 `AI编程` 按钮 | 拆分为 **预览** 和 **代码** 两个子入口 |

| 新入口 | 功能 | 点击行为 |
|--------|------|---------|
| **预览** | 查看 AI 生成的 HTML 网页效果 | 在新 tab 中打开项目库中存储的 HTML 文件，或 iframe 内嵌预览 |
| **代码** | 查看 HTML 源代码 | 在代码查看器中展示 HTML 源码，支持复制 |

**实现方式**：
```tsx
<div className="expert-subnav">
  <button onClick={() => { setConversationOpen(false); setActivePage('image'); }} type="button">AI生图</button>
  <button onClick={() => { setConversationOpen(false); setActivePage('video'); }} type="button">AI视频</button>
  <button onClick={() => { /* 预览 */ }} type="button">AI编程 · 预览</button>
  <button onClick={() => { /* 代码 */ }} type="button">AI编程 · 代码</button>
</div>
```

**HTML 自动生成规则**：
- 每次 Node3 / AI生图 / AI编程产出的内容，后端同步生成一份美化后的 HTML 文件
- HTML 文件自动保存到项目库 → 编程文件库
- 预览模式读取该 HTML 渲染；代码模式读取源码

---

## 三、技能库存储规则

| 维度 | 规则 |
|------|------|
| 存储位置 | `/Users/wangzijian/Desktop/差异性skills/`（保持不变） |
| UI 样式 | 不做任何修改 |
| 技能加载 | 后端 `list_skills()` 持续从该目录读取 SKILL.md |

无需改动前端代码。

---

## 四、项目库存储规则

### 4.1 文件夹分类

| 文件夹 | 存储内容 |
|--------|---------|
| **图片库** | Node3 生成的 SVG 文件、通义万相效果图 PNG、Node1 图表截图 |
| **视频库** | AI 生成的视频素材、分镜序列帧 |
| **编程文件库** | 所有 AI 产出的 HTML 网页文件（美化后版本）、CSS/JS 文件 |
| **创业资料** | Node1 需求洞察报告 .md、Node2 商业底层数据、Node1.5 品牌策略文档 |
| **AI 对话产出** | 对话自动生成的文档、表格、摘要 |
| **产品设计** | PRD、原型说明、功能清单 |
| **营销素材** | 脚本、选题、投放复盘 |

### 4.2 自动归档流程

```
用户触发 Node 生成
    │
    ├─ Node1 → .md 报告 → 创业资料 + 桌面
    ├─ Node2 → YAML 商业数据 → 创业资料
    ├─ Node1.5 → 品牌策略文档 → AI对话产出
    └─ Node3 → SVG + PNG → 图片库
             → HTML → 编程文件库
```

### 4.3 现有 projectFolders 需调整

**改动文件**：`src/App.tsx` 第 86-94 行

当前已有的文件夹保持不变，仅确认「编程文件库」的 `locked: true` 去掉（现在由系统自动写入，不再是锁定的 demo 数据）。

---

## 五、改动文件清单

| 文件 | 改动内容 |
|------|---------|
| `src/App.tsx` | 1) 产品名 `开物AI`→`曜势科技`，AI头像 `K`→`曜` |
| | 2) `sidebarItems` 删除 `automation` |
| | 3) `expert-subnav` 子功能：AI生图/视频 → 绑定 Node3 对话；AI编程 → 拆分预览/代码 |
| | 4) `projectFolders` 去掉编程文件库 `locked: true` |
| `src/styles.css` | 无 | 可能微调 subnav 样式（新增两个入口后高度适配） |
| `index.html` | `<title>` 改为 `曜势科技` |
| `server.py`（后端） | Node3 输出后自动生成 HTML 文件 + 存入项目库对应文件夹 |

---

## 六、实施优先级

| 优先级 | 条目 | 工作量 |
|--------|------|--------|
| P0 | 产品名改为曜势科技 | 3 处文字替换 |
| P0 | 删除自动任务 | 1 行删除 |
| P0 | AI生图/视频绑定 Node3 | expert-subnav 点击逻辑修改 |
| P1 | AI编程拆分预览/代码 | 新增子入口 + HTML 自动生成逻辑 |
| P1 | 项目库自动归档 HTML | 后端文件写入 + 前端文件夹展示 |
| P2 | Node3 生成 HTML 文件 | 后端新增 HTML 美化生成函数 |

---

*文档结束*
