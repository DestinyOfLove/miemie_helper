# MieMie Helper

工作与生活辅助工具集合项目。模块化设计，前后端分离架构。

## 项目约束

- 本地离线运行，不依赖网络服务（涉密内容）
- 跨平台：macOS 开发，Windows 部署
- 使用 `uv` 管理依赖和运行

## 运行命令

```bash
# Web 应用（NiceGUI + FastAPI，端口 4001）
uv run python main.py

# CLI 直接处理（保留兼容）
uv run python -m src.doc_archive.main <公文目录> [-o 输出.xlsx]
```

## 项目结构

```
src/
├── config.py              # 集中配置（路径、模型名、参数）
├── core/                  # 共享核心逻辑（无 web 依赖）
│   ├── extractor.py       # 文本提取：图片OCR / PDF / docx
│   ├── parser.py          # 字段解析：正则提取发文字号、标题、日期等
│   ├── file_scanner.py    # 目录扫描 + 年份推断
│   └── text_utils.py      # 文本工具函数
├── search/                # 搜索引擎层
│   ├── models.py          # Pydantic 数据模型
│   ├── document_db.py     # SQLite 文档元数据 + 目录管理
│   ├── fulltext_store.py  # FTS5 全文检索（jieba 中文分词）
│   ├── embedding.py       # sentence-transformers 向量编码
│   ├── vector_store.py    # ChromaDB 向量存储 + 文档分块
│   └── indexer.py         # 增量索引编排器
├── api/                   # FastAPI REST 路由
│   ├── index_routes.py    # /api/index/* — 索引管理
│   └── search_routes.py   # /api/search/* — 双模式搜索
└── ui/                    # 前端页面
    ├── layout.py          # 共享导航栏
    ├── home_page.py       # / — 首页
    └── search_page.py     # /search — 文档搜索
└── doc_archive/           # CLI 入口（保留兼容）
    └── main.py

.miemie_data/              # 运行时数据（git-ignored）
├── db/documents.db        # SQLite（元数据 + FTS5）
├── vector/chroma/         # ChromaDB 向量持久化
└── models/                # Embedding 模型缓存
```

## 架构要点

**搜索管道**：
- 全文检索：jieba 分词 → SQLite FTS5 MATCH → snippet 高亮
- 向量检索：sentence-transformers 编码 → ChromaDB cosine 相似度 → 去重
- 结果双栏并列展示

**增量索引**：mtime+size 快速预过滤 → MD5 哈希确认 → 只处理变更文件

**文本提取**（`src/core/extractor.py`）：
- 图片 → OpenCV 预处理 + RapidOCR
- PDF → PyMuPDF 嵌入文本，不足 20 字则 OCR
- .docx → python-docx，.doc → 暂不支持

**Embedding 模型**：BAAI/bge-small-zh-v1.5（首次运行需下载 ~100MB）

## 开发规范

- 使用 `uv` 初始化和管理项目
- 模块化结构，每个工具独立目录
- 新增工具时在 `src/` 下创建独立目录
- 响应语言：中文
