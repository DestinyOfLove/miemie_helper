# Establish Design Context In Harness Docs

## Goal

- 使用 `teach-impeccable` 的探索与提问结果，建立项目级设计上下文
- 不重新引入 `CLAUDE.md`
- 把长期维护的设计 ground truth 放入 `docs/harness/`

## Impact

- 前端相关任务会有稳定的设计依据
- 设计偏好不再散落在对话中
- 后续 UI 改动可以直接引用同一份上下文

## Files

- `AGENTS.md`
- `docs/harness/design-context.md`
- `docs/harness/standards.md`

## Verification

```bash
git diff --check
rg -n "design-context|设计上下文|Design Context" AGENTS.md docs/harness
```

## Done Criteria

- 存在可维护的设计上下文文档
- `AGENTS.md` 与 `docs/harness/` 已把它接入工作流
- 没有重新创建 `CLAUDE.md`
