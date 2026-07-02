# 曜势科技 (Kaiwu) — AI创业智能体

## 启动

```bash
# 后端 (端口 5001)
cd kaiwuback && python3 main.py

# 前端 (端口 5177)
cd kaiwu && npm run dev
```

## 项目结构速查

```
kaiwu_All/
├── kaiwu/src/              前端 React+Vite
│   ├── App.tsx             侧边栏+对话引擎+页面路由 (731行，只读)
│   ├── context/AppContext.tsx  共享状态 (18 state + 6 ref)
│   ├── pages/              4个页面组件
│   │   ├── SkillsPage.tsx      技能库
│   │   ├── ProjectsPage.tsx    项目库
│   │   ├── SettingsPage.tsx    设置
│   │   └── CodingPage.tsx      编程台
│   ├── data.ts             静态数据(赛道/技能/文案)
│   ├── types.ts            TS类型
│   └── utils.ts            前端Markdown渲染
├── kaiwuback/              后端 FastAPI
│   ├── main.py             App创建+chat SSE (303行，只读)
│   ├── .env                API密钥 (gitignore)
│   ├── server/
│   │   ├── api/            REST路由
│   │   │   ├── routes_skills.py
│   │   │   ├── routes_files.py
│   │   │   └── routes_conv.py
│   │   ├── orchestrator/   编排层
│   │   │   ├── llm_engine.py   LLM调用+prompt组装 (DATA_INTEGRITY在此注入)
│   │   │   └── handlers.py     summary+export流处理
│   │   ├── nodes/          Node定义
│   │   │   ├── prompts.py      NODES + NODE_SYSTEM_PROMPTS (9个节点)
│   │   │   └── node2_archiver.py  品牌手册HTML构建
│   │   ├── llm_client/     LLM提供商
│   │   │   └── router.py       注册表模式 (新增提供商加函数+注册)
│   │   ├── intent/         意图识别
│   │   │   └── recognizer.py   四层匹配+DEPENDENCIES
│   │   ├── persistence/    数据库
│   │   │   └── database.py     对话CRUD
│   │   ├── utils/          工具
│   │   │   ├── markdown.py     Markdown→HTML
│   │   │   ├── svg.py         SVG Logo生成
│   │   │   ├── file_io.py     HTML生成+文件归档
│   │   │   ├── session.py     会话状态
│   │   │   └── common.py      兼容重导出 (只读)
│   │   ├── reports.py      报告生成
│   │   └── config.py       配置 (数据铁律+路径，不改密钥)
│   └── conversations/      对话MD文件
└── docs/                   规范文档
    ├── 00-文件索引-开发速查.md   场景→文件映射
    ├── 01-执行标准清单.md       21条规范
    ├── 02-Spec模板.md           Spec填写模板
    ├── 03-项目文档索引.md       所有文档检索入口
    ├── 04-AI-Review校验模板.md  功能完成后Review
    ├── specs/                   6份冻结决策Spec
    └── reviews/                 基线Review
```

## 开发规则

### 放对文件
- 新增Node → `prompts.py` + `recognizer.py`（不改main.py）
- 新增API → `server/api/routes_*.py`
- 新增页面 → `src/pages/NewPage.tsx` + App.tsx加一行路由
- 新增LLM提供商 → `llm_client/` 新建 + `router.py` 注册一行
- 换密钥 → `kaiwuback/.env`

### Spec 先行
新功能决策 → 复制 `docs/02-Spec模板.md` → 填因果链 → 冻结 → 更新 `docs/03-项目文档索引.md` → 写代码

### Review
功能完成 → 按 `docs/04-AI-Review校验模板.md` 四维度自查 → 出结论 → 归档 `docs/reviews/`

### 数据真实性
`config.py` 的 `DATA_INTEGRITY` 自动注入所有LLM调用的system prompt前缀。修改数据规则只改这一处。

## 当前 10 个 Node

| Node | 名称 | 依赖 |
|------|------|------|
| node0 | 用户诊断 | 无 |
| node1 | 市场调研 | node0 (soft) |
| node1.5 | 品牌设计 | node1+node2 (hard) |
| node2 | 商业方案 | node1 (hard) |
| node3 | 产品设计 | node2 (hard) |
| node3.1 | 图片生成 | 无 |
| node4 | 营销方案 | node1+node2 (hard), node1.5 (soft) |
| node5 | 营销文案 | 无 |
| export | 文件导出 | 无 |
| fallback | 兜底 | 无 |
