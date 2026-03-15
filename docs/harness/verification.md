# Verification

本仓库当前没有统一 `Makefile` 或 CI，验证以现有可执行命令为准。改动后至少运行与影响面匹配的命令，并在结果中给出证据。

## Baseline Setup

```bash
uv sync --group dev
cd frontend && npm install
```

## Common Commands

```bash
uv run python -m pytest tests/test_text_utils.py
cd frontend && npm run lint
cd frontend && npm run build
uv run python main.py
```

## Change Matrix

### Frontend UI / React 页面

至少运行：

```bash
cd frontend && npm run lint
cd frontend && npm run build
```

如果改动影响页面交互或路由，再补一次手工 smoke：

- 启动 `uv run python main.py`
- 打开 `/` 和相关页面
- 确认页面可加载、控制台无明显错误、关键操作可完成

### Backend Python 逻辑

至少运行：

```bash
uv run python -m pytest tests/test_text_utils.py
```

如果改动不在 `text_utils` 覆盖范围内，还要补目标功能的手工验证，并说明为什么没有自动化测试。

### 前后端接口 / 搜索与索引行为

运行：

```bash
uv run python -m pytest tests/test_text_utils.py
cd frontend && npm run lint
cd frontend && npm run build
uv run python main.py
```

然后手工验证对应流程，例如：

- 目录索引能启动并结束
- 搜索请求返回结果且页面能正常渲染
- 受影响字段在前后端展示一致

### Docs / Harness Only

至少检查：

```bash
git diff --check
```

如果文档声明了命令或路径，还要确认它们在仓库中真实存在。

## Evidence Rules

- 最终说明里写明实际执行过的命令。
- 如果某个命令失败，给出失败点，不要省略。
- 如果因环境原因无法运行，也要明确说明未验证项。
