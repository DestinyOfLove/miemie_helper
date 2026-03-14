# Remove CLAUDE.md And Consolidate Agent Ground Truth

## Goal

- 删除仓库中的 `CLAUDE.md`
- 移除所有对 `CLAUDE.md` 的依赖和引用
- 把仍需长期维护的 agent 指引统一收口到 `AGENTS.md` 与 `docs/harness/`

## Impact

- 根目录 agent 入口会从 “AGENTS + CLAUDE” 收敛为 “AGENTS + docs/harness”
- 仓库级 ground truth 明确为 harness 文档，不再维护 Claude 专用说明文件
- 不影响运行时代码、构建流程或用户功能

## Files

- `CLAUDE.md`
- `AGENTS.md`
- `docs/harness/repo-map.md`
- `docs/harness/standards.md`

## Risks

- 如果 `CLAUDE.md` 里有仍然有效但尚未迁入 harness 的约束，删除后可能造成信息丢失
- 需要在删除前确认保留信息已经被 `docs/harness/` 覆盖

## Verification

```bash
rg -n "CLAUDE\\.md|\\.claude|Claude" AGENTS.md README.md docs evals src frontend . --glob '!node_modules' --glob '!dist'
git diff --check
uv run /Users/sulan/work_space/projects/dot_files/config/agent_config/commands/harness-engineering-repo/scripts/harness_repo.py audit --repo .
```

## Done Criteria

- 仓库内不再存在 `CLAUDE.md`
- `AGENTS.md` 与 `docs/harness/` 不再引用 `CLAUDE.md`
- harness audit 仍然通过，且没有新增 fail
