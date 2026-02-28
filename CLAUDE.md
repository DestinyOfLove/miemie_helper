# MieMie Helper

工作与生活辅助工具集合项目。模块化设计，每个工具独立目录，按需扩展。

## 项目约束

- 本地离线运行，不依赖网络服务（涉密内容）
- 跨平台：macOS 开发，Windows 部署
- 使用 `uv` 管理依赖和运行

## 运行命令

```bash
# Web UI（Gradio，端口 4001）
uv run python src/webapp/app.py

# CLI 直接处理
uv run python src/doc_archive/main.py <公文目录> [-o 输出.xlsx]
```

## 项目结构

```
src/
├── doc_archive/     # 公文档案整理 — 核心逻辑
│   ├── main.py      # CLI 入口：扫描目录 → 提取 → 解析 → 输出 Excel
│   ├── extractor.py # 文本提取：图片OCR / PDF文本+OCR / docx解析
│   └── parser.py    # 字段解析：从文本中用正则提取发文字号、标题、日期等
└── webapp/          # Web UI（Gradio）
    └── app.py       # 封装 doc_archive，增加增量去重、进度条、文件下载
```

## 模块详情

### doc_archive — 发文档案整理

将 1993-2025 年历年发文文件批量解析为结构化 Excel 表格。

**处理管道**：`文件扫描 → extractor.extract_text() → parser.parse_document_fields() → Excel`

**支持格式**：
- 图片（JPG/PNG/TIFF/BMP）→ OpenCV 预处理 + RapidOCR
- PDF → PyMuPDF 优先提取嵌入文本，文本不足 20 字则转图片 OCR
- .docx → python-docx 提取段落和表格文本
- .doc → **暂不支持自动处理**，需 LibreOffice 手动转换

**解析字段**：发文字号、发文标题、发文日期、发文机关、主送单位、公文种类、密级、来源年份

### webapp — Web 界面

基于 Gradio 的 Web UI，封装 doc_archive 核心逻辑。相比 CLI 额外支持：
- 增量处理：上传已有 Excel，通过文件 MD5 哈希去重
- 长文本拆分：超过 Excel 单元格限制（32000 字）时自动拆列
- webapp 通过 `sys.path.insert` 引用 doc_archive，非包导入

## 开发规范

- 使用 `uv` 初始化和管理项目
- 模块化结构，每个工具独立目录
- 新增工具时在 `src/` 下创建独立目录
- 响应语言：中文
