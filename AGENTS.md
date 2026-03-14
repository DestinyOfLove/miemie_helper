# MieMie Helper Agent Guide

本文件是仓库根入口。保持简短；稳定工作流和规范放在 `docs/harness/`，不要把这里扩成手册。

## First Read

- Agent 工作流与验证：`docs/harness/verification.md`
- 仓库结构与边界：`docs/harness/repo-map.md`
- 编码约束与不变量：`docs/harness/standards.md`
- 前端设计上下文：`docs/harness/design-context.md`
- 回归策略：`docs/harness/evals.md` 与 `evals/README.md`
- 执行计划规则：`docs/harness/execution-plans.md`
- 用户文档：`README.md`

## Repository Summary

- 这是一个本地离线运行的文档搜索与归档工具，主入口是 `main.py`
- 启动包装脚本是 `start.py`，安装脚本是 `install.py`
- 前端源码在 `frontend/`，使用 Next.js App Router，静态导出产物在 `frontend/out/`
- 后端 API 在 `src/api/`，搜索与索引逻辑在 `src/search/`
- 文本提取与解析逻辑在 `src/core/`
- `src/ui/` 是保留兼容的 NiceGUI 页面，不是当前主入口

## Standard Commands

```bash
uv sync
uv run python main.py
uv run pytest tests/test_text_utils.py
cd frontend && npm install
cd frontend && npm run lint
cd frontend && npm run build
```

按改动类型补充验证，具体规则见 `docs/harness/verification.md`。

## Planning Rules

以下变更先写 `docs/plans/<date>-<topic>.md` 再实现：

- 修改搜索 / 索引 / 提取流程等跨模块行为
- 修改前后端接口契约或结果字段
- 修改安装、启动、数据目录、副作用行为
- 新增需要持久回归样例的功能或迁移
- 调整 harness 结构或仓库级工作流

## Working Norms

- 文档以中文为主；命令、路径、环境变量保留英文
- 不要直接编辑 `frontend/out/`；前端改动应在 `frontend/` 修改后重建
- 不要提交 `.miemie_helper/`、缓存、模型、数据库等运行时产物
- 不再新增额外的 provider-specific 根说明文件；agent 相关长期规则统一维护在 `AGENTS.md` 与 `docs/harness/`
- README 可能落后于实现；涉及实际行为时以代码和 `docs/harness/` 为准
- 变更完成不算结束，必须附上实际执行过的验证证据
