# MieMie Helper

工作与生活辅助工具集合项目。前后端分离架构，本地离线运行。

## 功能特性

- **文档全文搜索** — jieba 中文分词 + SQLite FTS5 全文检索
- **向量语义搜索** — BAAI/bge-small-zh-v1.5 编码 + ChromaDB 余弦相似度
- **增量索引** — mtime+size 预过滤 → MD5 确认，只处理变更文件
- **公文归档导出** — 自动提取发文字号、标题、日期等字段，导出 Excel
- **多格式支持** — PDF / Word / WPS / OFD / 图片 OCR

## 支持的文件格式

| 格式 | 扩展名 | 提取方式 |
|---|---|---|
| PDF | `.pdf` | PyMuPDF 嵌入文本 / OCR 回退 |
| Word | `.docx` | python-docx |
| Word 97-2003 | `.doc` | LibreOffice → docx → python-docx |
| 金山 WPS | `.wps` | LibreOffice → docx → python-docx |
| OFD 版式文件 | `.ofd` | ZIP + XML 解析（零依赖） |
| 图片 | `.jpg` `.jpeg` `.png` `.tiff` `.tif` `.bmp` | OpenCV 预处理 + RapidOCR |

---

## Windows 安装部署

### 1. 安装 Python 3.13+

从 [Python 官网](https://www.python.org/downloads/) 下载安装包。

> **安装时务必勾选「Add Python to PATH」**。

安装后验证：

```powershell
python --version
# Python 3.13.x
```

### 2. 安装 uv 包管理器

在 PowerShell 中执行：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

安装完成后**重新打开 PowerShell**，验证：

```powershell
uv --version
```

> 如果提示找不到命令，将 `%USERPROFILE%\.local\bin` 添加到系统 PATH。

### 3. 安装 LibreOffice（处理 .doc / .wps 文件需要）

从 https://www.libreoffice.org/download/ 下载安装。

配置以下任一方式让程序找到 `soffice.exe`：

- **方式 A（推荐）**：安装到默认路径 `C:\Program Files\LibreOffice\`，程序会自动检测
- **方式 B**：设置环境变量 `LIBREOFFICE_PATH` 指向完整路径：
  ```
  LIBREOFFICE_PATH=D:\LibreOffice\program\soffice.exe
  ```
- **方式 C**：将 LibreOffice 的 `program` 目录添加到系统 PATH

查找优先级：`LIBREOFFICE_PATH` 环境变量 → 系统 PATH → 平台默认路径。

> 如果只处理 `.pdf` / `.docx` / `.ofd` / 图片，可以跳过此步。

### 4. 安装 Node.js（构建前端需要）

从 [Node.js 官网](https://nodejs.org/) 下载 **LTS** 版本安装。

安装后验证：

```powershell
node --version
npm --version
```

### 5. 获取项目代码

```powershell
git clone https://github.com/DestinyOfLove/miemie_helper.git
cd miemie_helper
```

### 6. 一键安装

双击 `install.bat`，自动完成：检查环境 → 安装 Python 依赖 → 构建前端。

或者手动执行：

```powershell
uv sync
cd frontend && npm install && npm run build && cd ..
```

### 7. 启动应用

双击 `start.bat`，自动启动后端并打开浏览器。

或者手动执行：

```powershell
uv run python main.py
```

浏览器访问 http://localhost:4001

> 首次启动会下载 Embedding 模型（~100MB），之后缓存到本地。如果机器无法联网，需要提前准备模型文件（见下方离线部署说明）。

---

## macOS 安装部署

```bash
# 1. 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 安装 LibreOffice（可选，处理 .doc/.wps 需要）
brew install --cask libreoffice

# 3. 安装 Node.js（构建前端需要）
brew install node

# 4. 安装依赖
uv sync

# 5. 构建前端
cd frontend && npm install && npm run build && cd ..

# 6. 启动
uv run python main.py
```

---

## 运行

```bash
# Web 应用（FastAPI + React，端口 4001）
uv run python main.py

# 热加载开发模式（后端）
uv run uvicorn main:app --host 0.0.0.0 --port 4001 --reload

# 前端开发模式（自动代理 /api 到后端）
cd frontend && npm run dev

# CLI 直接处理
uv run python -m src.doc_archive.main <公文目录> [-o 输出.xlsx]
```

## 离线部署

本项目设计为本地离线运行。在无网络的部署机器上：

1. **Python 依赖**：在联网机器上 `uv sync` 后，将整个项目目录（含 `.venv/`）拷贝到目标机器
2. **前端资源**：在联网机器上 `npm run build` 后，`static/` 目录已包含所有前端文件
3. **Embedding 模型**：首次启动时会下载到 `.miemie_helper/doc_search/models/`。可在联网机器上先运行一次，再将该目录拷贝到目标机器相同路径

## 环境变量

| 变量名 | 默认值 | 说明 |
|---|---|---|
| `MIEMIE_DATA_DIR` | `<项目根>/.miemie_helper/doc_search` | 运行时数据目录 |
| `LIBREOFFICE_PATH` | 自动检测 | LibreOffice `soffice` 可执行文件路径 |
| `MIEMIE_OCR_DPI` | `200` | OCR 渲染 DPI |
| `MIEMIE_INDEXING_WORKERS` | `0`（自动） | 索引并行 worker 数，0 = CPU 核数 - 2 |

## 项目结构

```
├── main.py                # 应用入口（FastAPI + 静态文件）
├── frontend/              # React + Vite 前端源码
│   └── package.json
├── static/                # 前端构建产物（git-ignored）
├── src/
│   ├── config.py          # 集中配置
│   ├── core/              # 共享核心逻辑
│   │   ├── extractor.py   # 文本提取（OCR / PDF / docx / LibreOffice）
│   │   ├── parser.py      # 字段解析（发文字号、标题、日期等）
│   │   ├── file_scanner.py# 目录扫描 + 年份推断
│   │   ├── text_utils.py  # 文本处理工具
│   │   └── excel_exporter.py
│   ├── search/            # 搜索引擎层
│   │   ├── models.py      # Pydantic 数据模型
│   │   ├── document_db.py # SQLite 文档元数据 + 目录管理
│   │   ├── fulltext_store.py # FTS5 全文检索
│   │   ├── embedding.py   # 向量编码
│   │   ├── vector_store.py# ChromaDB 向量存储
│   │   └── indexer.py     # 增量索引编排
│   ├── api/               # FastAPI REST 路由
│   │   ├── index_routes.py
│   │   ├── search_routes.py
│   │   ├── export_routes.py
│   │   └── archive_routes.py
│   ├── ui/                # NiceGUI 页面（保留兼容）
│   └── doc_archive/       # CLI 入口（保留兼容）
└── .miemie_helper/        # 运行时数据（git-ignored）
    └── doc_search/
        ├── db/            # SQLite 数据库
        ├── vector/chroma/ # ChromaDB 向量持久化
        └── models/        # Embedding 模型缓存
```
