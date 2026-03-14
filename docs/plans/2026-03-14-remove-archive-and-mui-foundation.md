# Remove Archive Feature And Establish MUI Foundation

## Goal

- 彻底移除 `/archive` 功能及其前端入口
- 清理 archive 相关的前端客户端代码与文档引用
- 在当前 Next.js 基础上接入 MUI，并建立 layout/theme 基础层

## Impact

- 主产品表面只保留首页与文档搜索
- `frontend/src/api/client.ts` 将移除 archive 相关类型与方法
- 前端路由、导航、首页入口会移除 archive
- Next.js 根布局会接入 MUI theme provider
- 剩余页面会开始消费统一的 MUI layout/theme，而不是完全依赖裸 inline styles

## Files

- `frontend/app/*`
- `frontend/src/components/*`
- `frontend/src/views/*`
- `frontend/src/api/client.ts`
- `frontend/package.json`
- `frontend/tsconfig.json`
- `AGENTS.md`
- `README.md`
- `docs/harness/*`
- `src/ui/*.py`

## Verification

```bash
cd frontend && npm install
cd frontend && npm run lint
cd frontend && npm run build
python3 start.py
curl -s http://localhost:4001 | head -n 5
curl -s http://localhost:4001/search | head -n 5
```

## Done Criteria

- `/archive` 页面与导航入口消失
- 前端不再保留 archive 客户端代码
- MUI theme provider 已接入 Next 根布局
- 至少首页、导航和搜索页开始使用 MUI layout/theme 基础层
