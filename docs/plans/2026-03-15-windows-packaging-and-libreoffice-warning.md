# Windows Packaging And LibreOffice Warning

## Goal

- 提供一条可在 Windows runner 上产出发布包的稳定打包链路
- 避免 Windows 运行时继续依赖源码仓库、`uv sync` 和前端现构建
- 在缺少 LibreOffice 时提供前端强警告，并明确说明 `.doc/.wps` 的降级影响
- 直接修复索引文本规范化的历史回归，不再兼容旧索引数据库语义

## Impact

- 运行时数据目录默认行为会调整，Windows 下改为用户可写目录
- 后端会新增运行环境能力接口和失败文件查询接口
- 索引流程会持久化提取失败状态，前端会展示全局警告和失败文件列表
- 仓库会新增 Windows 打包入口、PyInstaller 规格文件和 GitHub Actions 工作流
- 文本存储会拆分为“原始提取文本”和“索引用规范化文本”，旧 SQLite 索引库将被直接重置
- 会补一个常规 CI 工作流，防止 `normalize_text_for_indexing()` 与测试再次漂移

## Files

- `src/config.py`
- `main.py`
- `launcher.py`
- `src/runtime_capabilities.py`
- `src/core/extractor.py`
- `src/search/models.py`
- `src/search/document_db.py`
- `src/search/indexer.py`
- `src/api/index_routes.py`
- `src/api/system_routes.py`
- `src/core/text_utils.py`
- `frontend/src/api/client.ts`
- `frontend/src/components/layout/AppShell.tsx`
- `frontend/src/components/runtime/RuntimeCapabilitiesProvider.tsx`
- `frontend/src/components/runtime/GlobalRuntimeAlert.tsx`
- `frontend/src/views/SearchPage.tsx`
- `packaging/windows.spec`
- `.github/workflows/ci.yml`
- `.github/workflows/windows-package.yml`

## Risks

- PyInstaller 对 OCR / ONNX / OpenCV 这类原生依赖较敏感，Windows 打包首轮可能还需要根据 CI 日志补收集规则
- 把失败文件写入数据库后，目录计数和重试逻辑必须同步调整，否则会出现“失败文件被当成已索引”的假象
- Windows 数据目录迁移到用户目录后，旧的仓库内 `.miemie_helper/` 数据不会自动迁移
- 旧索引库会被直接清空重建，用户需要重新执行索引

## Verification

```bash
uv run pytest tests/test_text_utils.py
cd frontend && npm run lint
cd frontend && npm run build
uv run python -m py_compile main.py launcher.py src/**/*.py
uv run python - <<'PY'
from src.runtime_capabilities import get_runtime_capabilities
print(get_runtime_capabilities().model_dump())
PY
```

## Done Criteria

- 仓库中存在可手动触发的 Windows 打包工作流和 PyInstaller 规格文件
- Windows 运行时默认数据目录不再依赖源码目录
- 前端会持续展示 LibreOffice 缺失的强警告，并说明对 `.doc/.wps` 检索的影响
- 索引失败文件可在前端被明确看到，缺少 LibreOffice 时对应文件显示红色失败状态和原因
- `normalize_text_for_indexing()` 的测试全部通过，原始展示文本与索引用文本不再混用
