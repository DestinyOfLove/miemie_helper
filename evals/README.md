# Evals

这个目录存放任务级回归材料，而不是通用源码文档。

## Use This Directory For

- 容易回归问题的最小复现说明
- 可公开或脱敏的测试样例
- 手工 smoke 脚本、检查清单、结果记录

## Suggested Layout

- `fixtures/`
  - 脱敏后的输入样例、截图、导出文件样本
- `YYYY-MM-DD-<topic>.md`
  - 单次任务的回归记录

## Minimal Eval Record Template

每条记录至少写清：

- 变更背景
- 复现步骤
- 期望结果
- 实际验证命令 / 操作
- 结论与剩余风险

如果真实文件不能提交，就记录可操作的脱敏步骤或伪造最小样例的方法。
