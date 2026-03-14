# Frontend Remediation Program

## Goal

基于本轮 `audit` 结果，对当前 React + Vite 前端做一次分阶段的大修，目标是同时解决：

- 设计系统缺失与 hard-coded style 泛滥
- 当前界面与 `docs/harness/design-context.md` 不一致的问题
- 桌面窄窗口与不同桌面尺寸下的布局问题
- 搜索页单文件过重、后续演进成本过高的问题
- 现有 bundle 体积与运行时交互粗糙度问题

本计划不是单点修补，而是把前端从“可用 MVP”升级为“现代、专业、高效”的桌面效率工具基线。

## First Principle

要让界面持续可维护，必须先建立稳定的库基础和主题规则，再改页面外观。

如果继续按页面逐个修，且继续自建基础控件：

- 会重复修 button / input / chip / panel / progress
- 会在没有主题系统的情况下重复写颜色和间距
- 会让 `SearchPage.tsx` 继续承担过多职责
- 会让 dark mode、桌面窗口适配和 modern 化互相打架
- 会制造更多自维护轮子

因此，正确顺序不是“先把页面做漂亮”，而是：

1. 先选定并接入成熟 UI 库
2. 再建立 light / dark 主题、shell、布局和桌面交互规则
3. 再改轻量页面
4. 最后集中处理最复杂的搜索页

## Scope

### In Scope

- `frontend/index.html`
- `frontend/src/index.css`
- `frontend/src/App.tsx`
- `frontend/src/components/*`
- `frontend/src/pages/*`

### Out Of Scope

- 后端业务逻辑重构
- 搜索算法与接口语义的大改
- 手机端适配
- 正式 WCAG 达标项目
- 非前端 CI 建设

## Constraints

- 设计方向以 `docs/harness/design-context.md` 为准
- 当前主要使用场景是 macOS 命令行启动后的桌面浏览器使用
- 仍需保留 Windows 桌面使用的可行性，但本轮不做操作系统分叉 UI
- 只考虑桌面端，不做手机端适配
- 不能重新走“旧式政务后台”风格
- 优先采用成熟开源 UI 库，避免自建大批基础组件

## Framework Fact

- 当前项目不是 Next.js
- 当前前端是 React + Vite

这会影响库选型、主题接入方式和路由集成方式。后续方案按 React + Vite 设计，不按 Next.js 假设。

## Recommended Library Direction

### Default Recommendation

- UI 基础层：`MUI`
- 数据结果表：继续保留 `AG Grid`

### Why

- `MUI` 足够成熟，桌面工具场景常见，light / dark、表单、按钮、对话框、导航、主题能力都完整
- 你已经明确偏好“成熟开源库优先”，允许组件更重
- `AG Grid` 继续保留可以避免搜索结果表的大迁移

### Non-Goal

- 不做“自研 Button / Input / Chip 全家桶”
- 只在必要时做很薄的项目封装层

## Current Findings Summary

来自当前审计和代码现状的高优先问题主要是：

1. 没有稳定的主题和 token 系统
2. 页面样式高度硬编码，后续 dark mode 与 modern 化成本高
3. 缺乏统一 shell，页面各写一套容器和间距
4. `SearchPage.tsx` 过重且样式硬编码最集中
5. 桌面窄窗口布局缺乏策略
6. 构建产物已出现 1.35 MB bundle 警告
7. 当前实现更适合“手写 MVP”，不适合长期维护

## Dependency Graph

### 必须先完成的基础依赖

- UI 库选型与接入策略
  - 推荐默认路径：`MUI`
  - `AG Grid` 保留
- 文档级基础
  - `lang="zh-CN"`
  - title / metadata 修正
- 全局主题与焦点策略
  - light / dark
  - focus-visible
- App shell / 页面容器规则

### 依赖基础层的共享层

- 优先直接复用 UI 库组件
- 仅保留很薄的项目封装层，例如：
  - `AppShell`
  - `PageContainer`
  - `SectionPanel`

### 依赖共享层的页面改造

- `NavBar`
- `HomePage`
- `ArchivePage`
- `SearchPage`

### 强依赖、不能并行乱改的区域

- `SearchPage.tsx`
  - 不能多个人同时大改同一文件
  - 必须等主题、共享层和 shell 先稳定
- dark mode 实现
  - 必须建立主题系统后再落地到页面
- 大规模桌面窗口适配
  - 应在 shell 和页面结构稳定后做

## Workstreams

### Stream A: Desktop Interaction Baseline

目标：建立稳定的桌面语义和交互基础，而不是追求正式无障碍认证。

任务：

- 修正文档语言和基础语义
- 把明显不稳定的 click-only 交互改成语义化控件
- 给关键输入和图标按钮补可靠名称
- 建立统一 `:focus-visible` 体系

对应技能：

- `/harden`
- `/clarify`

### Stream B: Library Foundation

目标：先引入成熟 UI 库，再在其上建立主题与 shell。

任务：

- 接入 `MUI`
- 建立 MUI theme
- 建立 light / dark 两套主题变量
- 在 `App.tsx` 接入 provider 与 app shell
- 重做 `NavBar` 作为全局视觉锚点

对应技能：

- `/normalize`
- `/colorize`
- `/bolder`

### Stream C: Thin Shared Layer

目标：减少页面复制样式，但不重复发明库里已有的基础控件。

任务：

- 封装 `AppShell`
- 封装 `PageContainer`
- 封装 `SectionPanel`
- 明确哪些场景直接使用库组件，哪些需要很薄的项目 wrapper

对应技能：

- `/normalize`
- `/polish`

### Stream D: Light Page Remediation

目标：先处理结构简单、回归面可控的页面。

任务：

- `HomePage`
  - 入口布局 modern 化
  - 桌面窄窗口重排
  - 接入 MUI / shell / theme
- `ArchivePage`
  - 表单与按钮接入库组件
  - 进度区、日志区、下载动作重构
  - 桌面窄窗口布局

对应技能：

- `/adapt`
- `/polish`

### Stream E: Search Page Remediation

目标：重构最复杂页面，消化本轮大部分结构和视觉问题。

任务：

- 先拆 SearchPage 结构边界
- 再接入共享层和 MUI theme
- 再做桌面交互、窗口适配和 modern 化改造
- 最后处理 AG Grid 周边与性能优化

建议拆分的复合组件：

- `SearchScopeSelector`
- `DirectorySelector`
- `TagInput`
- `IndexStatusPanel`
- `IndexedDirectoryTable`

对应技能：

- `/adapt`
- `/normalize`
- `/optimize`
- `/polish`

### Stream F: Performance & Final Polish

目标：在结构稳定后处理构建体积和交互精修。

任务：

- 检查 AG Grid 模块引入范围
- 评估 route-level code splitting
- 处理 polling 生命周期
- 替换浏览器原生 `alert` / `confirm`
- 统一状态反馈、hover / active / disabled 行为

对应技能：

- `/optimize`
- `/polish`
- `/clarify`

## Phase Plan

### Phase 0: Preflight

目标：冻结基线，避免把历史脏变更和大修混在一起。

任务：

- 确认当前未提交变更边界
- 以当前 `audit` 作为基线记录
- 确认 `docs/harness/design-context.md` 已可作为设计依据

验证：

```bash
git status --short
cd frontend && npm run lint
cd frontend && npm run build
```

### Phase 1: Library + Foundation

目标：一次性建立共享基础。

任务：

- 选定并接入 `MUI`
- `frontend/index.html`
  - `lang="zh-CN"`
  - title / metadata 校正
- `frontend/src/index.css`
  - 保留全局 reset
  - 接入主题基础与少量全局样式
- `frontend/src/App.tsx`
  - provider
  - app shell
  - theme 容器
- `frontend/src/components/NavBar.tsx`
  - 接入主题
  - modern 化
  - 桌面焦点与状态

依赖关系：

- 后续所有页面都依赖本阶段产物

并行性：

- 可把 `MUI + App.tsx + index.css` 与 `NavBar.tsx` 分给不同 worker，但需先约定主题结构

验证：

```bash
cd frontend && npm run lint
cd frontend && npm run build
```

手工：

- 导航正常
- light / dark 可切换
- 页面骨架稳定

### Phase 2: Thin Shared Layer

目标：建立后续页面消费的薄共享层，而不是自建大设计系统。

任务：

- 新增 `AppShell`
- 新增 `PageContainer`
- 新增 `SectionPanel`
- 明确哪些页面直接用 MUI，哪些通过薄 wrapper

依赖关系：

- 依赖 Phase 1

并行性：

- 可以由一个 worker 专门负责共享层，另一个线程同时规划轻量页重构

验证：

```bash
cd frontend && npm run lint
cd frontend && npm run build
```

### Phase 3: Light Pages Parallel Batch

目标：先拿简单页面验证新基础是否有效。

任务 A：

- `HomePage.tsx`
  - 入口布局 modern 化
  - 接入 MUI / shell / theme
  - 桌面窄窗口重排

任务 B：

- `ArchivePage.tsx`
  - 表单、进度、日志、下载动作接入 MUI / shell / theme
  - 桌面窄窗口布局

依赖关系：

- 依赖 Phase 2

并行性：

- 可并行
- 写集分离：
  - Worker 1 负责 `HomePage.tsx`
  - Worker 2 负责 `ArchivePage.tsx`

验证：

```bash
cd frontend && npm run lint
cd frontend && npm run build
```

手工：

- 首页入口工作正常
- 归档页输入、开始处理、下载保持可用

### Phase 4: Search Page Main Batch

目标：集中解决复杂页。

任务：

- 把 `SearchPage.tsx` 拆分为复合组件
- 接入共享层与 MUI
- 改造搜索工具条、目录选择、tag 输入、索引管理区、结果区
- 做桌面窄窗口适配
- 保持现有业务行为不回退

依赖关系：

- 强依赖 Phase 1 和 Phase 2
- 不建议与其他大规模 `SearchPage.tsx` 修改并行

并行性：

- 不拆成多人同时改同一文件
- 如要并行，只能在组件拆分后，把新拆出的子组件按文件边界分配

验证：

```bash
cd frontend && npm run lint
cd frontend && npm run build
```

手工：

- 搜索输入与标签录入
- 搜索范围切换
- 目录选择与星标
- 索引面板展开/收起
- 结果渲染与复制按钮

### Phase 5: Desktop Window Sweep

目标：在页面基本稳定后做 light / dark 与桌面窗口一致性收口。

任务：

- 全站 light / dark 主题一致性检查
- 桌面小窗口 / 窄窗口 reflow
- 状态色与 surface hierarchy 统一

依赖关系：

- 依赖所有页面已接入主题和共享层

并行性：

- 可以按页面 sweep，但必须由主线程做最终一致性 review

验证：

```bash
cd frontend && npm run lint
cd frontend && npm run build
```

手工：

- light / dark 逐页切换
- 首页 / 搜索页 / 归档页桌面窄窗口检查

### Phase 6: Performance And Final Polish

目标：在结构已稳的前提下做性能和完成度优化。

任务：

- 检查 AG Grid 模块裁剪
- 评估 code splitting
- 替换浏览器原生 `alert` / `confirm`
- 收口 hover / active / disabled / loading
- 校正 favicon / title / 文档细节

依赖关系：

- 应在大结构稳定后进行，避免重复优化

验证：

```bash
cd frontend && npm run lint
cd frontend && npm run build
```

补充：

- 记录 bundle 大小前后对比

## Parallelization Strategy

### 可并行批次

- Phase 1 内：
  - Worker A：`MUI` 接入 + `index.css` + `App.tsx`
  - Worker B：`NavBar.tsx`
- Phase 3 内：
  - Worker A：`HomePage.tsx`
  - Worker B：`ArchivePage.tsx`

### 不可并行批次

- `SearchPage.tsx` 在未拆组件前不适合多人同时改
- 主题系统未定前不适合大面积页面颜色 patch
- 共享层未定前不适合页面各自发明一套新控件

### 推荐分工

- 主线程
  - 持有整体主题系统与 `SearchPage` 主改造权
- Worker 1
  - 负责 library foundation / shell
- Worker 2
  - 负责轻量页面
- Worker 3
  - 在后期进入 performance / polish sweep

## Verification Matrix

### Mechanical Checks

每个批次至少跑：

```bash
cd frontend && npm run lint
cd frontend && npm run build
```

### Manual Regression

每个关键阶段都要覆盖：

1. 页面主流程
2. light / dark 切换
3. 桌面窄窗口 reflow
4. 搜索页复杂交互

### Feature Checks

- 首页
  - 入口卡片可点击
- 搜索页
  - 搜索、筛选、目录、星标、索引、结果渲染都可用
- 归档页
  - 输入目录、启动、进度、下载保持可用

## Exit Criteria

- 建立基于 UI 库的 light / dark 主题系统
- 首页、导航、归档页、搜索页都接入共享层和库组件
- 搜索页不再维持“大而全单文件”状态
- 桌面窄窗口下不出现主要流程阻断
- 构建继续通过，且性能警报至少有明确处理结论

## Recommended Execution Order

实际执行时按下面顺序推进：

0. 先执行 `docs/plans/2026-03-14-nextjs-migration.md`
1. Phase 0
2. Phase 1
3. Phase 2
4. Phase 3（并行）
5. Phase 4
6. Phase 5
7. Phase 6

## First Task To Start With

如果现在立刻开始做，第一批应该是：

1. 先完成 `docs/plans/2026-03-14-nextjs-migration.md`
2. 迁移完成后再进入 `MUI` 接入和 UI 大修

原因：

- 否则前端框架层会先改一次，后面 UI 大修又要重接一次
- 先把框架层稳定，后续主题、共享层和页面改造才不会返工
