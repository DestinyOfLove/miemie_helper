# Migrate Frontend From Vite To Next.js First

## Goal

- 先把当前 `frontend/` 从 React + Vite 迁到 Next.js
- 保持当前 FastAPI 后端继续提供 `/api/*`
- 不在第一步引入 Next.js 独立 Node 服务依赖
- 为后续 UI 库接入和界面大修提供更稳定的前端框架基础

## First Principle

当前仓库的运行模型是：

- FastAPI 提供 API
- FastAPI 直接托管前端构建产物
- `start.py` / `install.py` 假设前端是“可构建为静态文件后再由 FastAPI 提供”

如果直接把前端切成“Next.js 独立服务端 + FastAPI API 双服务”，会同时打破：

- 启动链
- 安装链
- 静态托管模型
- 跨平台脚本

因此，最稳的迁移路径不是先追求 SSR，而是：

1. 先迁到 Next.js App Router
2. 先使用官方支持的 `output: 'export'`
3. 继续让 FastAPI 托管导出的静态文件
4. 等界面大修和结构稳定后，再决定要不要升级成 Next.js 独立运行模式

## Official Basis

基于 Next.js 官方文档，静态导出可通过 `output: 'export'` 实现，导出的产物可交由任意静态服务器托管。  
这正适合当前 “FastAPI 托管前端静态文件” 的架构。

同时，官方也提供从 Vite 风格应用迁到 App Router 的 client-only 包装方式：

- 保留现有 React App 作为 client-only 入口
- 在 `app/` 路由中通过 `dynamic(..., { ssr: false })` 承接

这允许迁移分阶段进行，而不是一次性重写所有页面。

## Recommended Architecture

### Phase 1 Target

- 前端框架：Next.js App Router
- 渲染模式：client-only shell + static export
- API：仍然请求 FastAPI `/api/*`
- 部署模型：FastAPI 继续托管导出的静态文件

### Not In Phase 1

- Next.js SSR / Server Actions
- Next.js API routes
- 独立 Next.js 生产服务进程
- BFF 架构改造

## Impact

### Affected Areas

- `frontend/package.json`
- `frontend/tsconfig*.json`
- `frontend/index.html` 将被 Next.js `app/` 结构替代
- `frontend/src/main.tsx` / `frontend/src/App.tsx` 的入口方式会变化
- `install.py`
- `start.py`
- `main.py` 的静态文件挂载逻辑可能需要适配 Next.js 导出目录结构

### Likely New Files

- `frontend/next.config.*`
- `frontend/app/layout.tsx`
- `frontend/app/[...slug]/page.tsx` 或等价 catch-all 路由
- `frontend/app/[...slug]/client.tsx`

## Migration Strategy

### Step 0: Freeze Current Frontend

- 保留现有 Vite 代码结构作为迁移源
- 不在迁移完成前继续做大规模 UI 重构

### Step 1: Install Next.js Toolchain

- 加入 `next`
- 调整脚本：
  - `dev`
  - `build`
  - `start`（如需要）

### Step 2: Add App Router Skeleton

- 建 `app/layout.tsx`
- 建 catch-all 页面
- 用 client-only wrapper 承接现有 `App.tsx`

### Step 3: Static Export Configuration

- 在 `next.config` 中设置 `output: 'export'`
- 选择合适的导出目录，最好继续与当前 `static/` 托管模型兼容

### Step 4: Route And Asset Adaptation

- 适配 React Router 现状
- 决定是：
  - 先保留 React Router 跑在 Next client-only shell 内
  - 还是同步迁到 Next file-system routing

推荐先保留 React Router，降低第一阶段迁移风险。

### Step 5: Build / Install / Start Integration

- 更新 `install.py`
- 更新 `start.py`
- 如需要，调整 `main.py` 的静态目录挂载逻辑

### Step 6: Verification

- Next.js 导出产物可被 FastAPI 正常提供
- `/`
- `/search`
- `/archive`
- `/api/*` 调用正常

## Recommendation

推荐采用：

### Option A: Next.js Static Export First

优点：

- 风险最低
- 不破坏当前单服务启动模型
- 更符合你现在“命令行桌面工具”的使用方式
- 对 macOS / Windows 桌面跨平台最稳

缺点：

- 暂时不能使用所有需要 Next.js server 的能力
- 第一阶段本质上是“框架迁移”，不是“能力升级”

### Option B: Next.js Full Server First

不推荐作为第一步。

原因：

- 会把前端迁移、启动链改造、部署模型改造、跨平台脚本改造绑在一起
- 返工面和故障面都明显更大

## Key Decision

本轮如果你坚持 “先换 Next.js”，我的建议是：

**先做 Option A：Next.js App Router + static export + FastAPI 继续托管静态产物。**

## Risks

- React Router 与 Next App Router 同时存在的过渡期会稍显别扭
- 一些 Next.js 特性在 `output: 'export'` 模式下不可用
- 导出目录与 FastAPI 静态托管的适配需要认真验证

## Verification

```bash
cd frontend && npm run build
python3 start.py
curl -s http://localhost:4001 | head -n 5
```

并手工验证：

- 首页
- 搜索页
- 归档页
- API 调用

## Done Criteria

- 前端不再依赖 Vite
- Next.js 构建成功
- FastAPI 仍可提供前端静态页面
- `python3 start.py` 仍然是可用的单命令入口
