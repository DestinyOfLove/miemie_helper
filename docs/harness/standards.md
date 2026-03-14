# Standards

## Tooling And Commands

- Python 相关命令统一用 `uv` 执行。
- 前端命令在 `frontend/` 目录执行，默认跟随仓库脚本使用 `npm`。
- 不要凭 README prose 猜命令；优先读 `pyproject.toml`、`frontend/package.json`、`install.py`、`start.py`。

## Source Of Truth

- Agent 工作流和验证要求以 `docs/harness/` 为准。
- 不再新增额外的 provider-specific 根说明文件；仓库级 agent ground truth 统一放在 `AGENTS.md` 与 `docs/harness/`。
- 前端视觉与交互方向优先遵循 `docs/harness/design-context.md`。
- 产品背景可以看 `README.md`，但它可能滞后；涉及行为时先核对代码。
- 当前 Web 入口是 `main.py` 挂载 Next.js 导出的 `frontend/out/`，不是 `src/ui/` 的 NiceGUI。

## Editing Boundaries

- 不要直接编辑 `frontend/out/` 生成文件；前端改动应修改 `frontend/` 下源码后重新构建。
- 运行时目录 `.miemie_helper/` 不属于源码。
- 修改 `src/ui/` 前先确认任务是否真的针对兼容层。

## Product Constraints

- 项目定位是本地离线工具；避免引入必须联网的运行时依赖。
- Windows 部署仍是主要场景之一；涉及路径、子进程、安装脚本时要考虑跨平台行为。
- 当前前端按桌面浏览器体验设计，不以手机端适配为目标。
- 前端优先复用成熟开源 UI 库；除非库无法满足需求，否则不要先造基础轮子。
- 搜索能力是否包含“语义 / 向量”不能只看旧文案；变更前先核对 `src/api/search_routes.py` 与当前前端调用链。

## Change Discipline

- 跨模块行为变更先写计划，规则见 `docs/harness/execution-plans.md`。
- 任何完成声明都要附带实际执行过的验证命令和结果。
- 如果没有自动化覆盖，明确写出缺口和手工验证步骤，不要默认“应该没问题”。
