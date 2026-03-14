# Repository Map

## Runtime Entry Points

- `main.py`
  - 当前 Web 应用入口。
  - 启动 FastAPI，并挂载 `static/` 下的 React 构建产物。
- `start.py`
  - 跨平台启动包装器。
  - 缺少 `.venv/` 或 `static/index.html` 时会自动补依赖 / 构建前端。
- `install.py`
  - 首次安装脚本。
  - 负责检查 Python / uv / Node.js，然后执行 `uv sync` 与前端构建。

## Frontend

- `frontend/src/pages/`
  - React 页面入口。
  - `HomePage.tsx` 是首页，`SearchPage.tsx` 是主要搜索界面，`ArchivePage.tsx` 是归档导出界面。
- `frontend/src/api/client.ts`
  - 前端对 `/api/*` 的 fetch 封装。
- `frontend/src/components/`
  - 共享前端组件。
- `static/`
  - 前端构建产物。
  - 视为生成目录，不要手改。

## Backend

- `src/api/`
  - FastAPI 路由层。
  - `index_routes.py` 负责索引管理，`search_routes.py` 负责搜索接口。
- `src/search/`
  - 搜索与索引实现。
  - `document_db.py` 管元数据和目录信息，`fulltext_store.py` 管 FTS5，`indexer.py` 做增量编排。
- `src/core/`
  - 与 Web 框架无关的核心逻辑。
  - 含文本提取、字段解析、扫描与文本标准化。

## Legacy / Compatibility Surfaces

- `src/ui/`
  - NiceGUI 页面，当前不是主入口。
  - 只有在明确处理兼容层时才修改。
- `README.md`
  - 作为用户背景资料可读，但部分描述可能落后于代码。
  - 涉及当前实现时，先核对 `main.py`、`frontend/`、`src/api/`。

## Tests And Scripts

- `tests/test_text_utils.py`
  - 当前唯一可见的自动化测试文件。
  - 覆盖 `normalize_text_for_indexing()`。
- `scripts/analyze_filenames.py`
  - 独立分析脚本，不是主应用流程的一部分。

## Local Data And Generated State

- `.miemie_helper/`
  - 运行时数据目录。
  - 可能包含 SQLite 数据库、模型缓存和索引数据，不应纳入源码变更。
- `__pycache__/`、`.pytest_cache/`
  - 本地缓存，忽略。
