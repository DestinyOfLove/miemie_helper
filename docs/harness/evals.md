# Evals Strategy

本仓库目前没有独立 CI 或成熟的任务级 eval 平台，现阶段采用“自动化检查 + 手工回归步骤 + 任务留档”的轻量策略。

## Current Regression Surfaces

- Python 单测：`tests/test_text_utils.py`
- 前端静态检查：`frontend` 下的 `npm run lint`
- 前端构建检查：`frontend` 下的 `npm run build`
- 手工 smoke：启动应用后验证受影响页面或 API 流程

## When To Add Evals Material

在以下情况补充 `evals/` 材料：

- 修复过一次、以后容易回归的 bug
- 搜索结果字段、排序、过滤、展示规则发生变化
- 安装 / 启动 / 索引这类多步骤流程需要可重复回放
- 真实数据不能入库，但需要留下最小复现说明或脱敏样例

## Minimal Practice

- 在 `evals/README.md` 记录任务级回归用法
- 把可公开或脱敏的最小样例放到 `evals/fixtures/`
- 如果无法提交真实样例，就记录：
  - 触发条件
  - 期望结果
  - 手工验证步骤
  - 失败时观察到的症状

## Current Gaps

- 没有 API 自动化测试
- 没有搜索 / 索引 / 归档的端到端回归
- 没有 CI 帮助重复执行这些检查

因此，涉及这些区域的任务必须在结论里清楚写出手工验证范围和未覆盖风险。
