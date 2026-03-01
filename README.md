# MieMie Helper

工作与生活辅助工具集合项目。模块化设计，前后端分离架构。

## 环境要求

### Python 依赖

使用 [uv](https://github.com/astral-sh/uv) 管理：

```bash
uv sync
```

### LibreOffice（必需）

处理 `.doc`（Word 97-2003）和 `.wps`（金山 WPS）文件需要安装 LibreOffice。

**macOS：**

```bash
brew install --cask libreoffice
```

**Windows：**

1. 从 https://www.libreoffice.org/download/ 下载安装
2. 配置以下任一方式让程序找到 `soffice.exe`：
   - **方式 A（推荐）**：设置环境变量 `LIBREOFFICE_PATH` 指向 `soffice.exe` 的完整路径，例如：
     ```
     LIBREOFFICE_PATH=D:\LibreOffice\program\soffice.exe
     ```
   - **方式 B**：将 LibreOffice 的 `program` 目录添加到系统 `PATH`，例如：
     ```
     PATH 中添加 C:\Program Files\LibreOffice\program
     ```
   - **方式 C**：安装到默认路径 `C:\Program Files\LibreOffice\`，程序会自动检测

查找优先级：`LIBREOFFICE_PATH` 环境变量 → 系统 PATH → 平台默认路径。

## 运行

```bash
# Web 应用（FastAPI + React，端口 4001）
uv run python main.py

# 热加载开发模式
uv run uvicorn main:app --host 0.0.0.0 --port 4001 --reload

# CLI 直接处理
uv run python -m src.doc_archive.main <公文目录> [-o 输出.xlsx]
```

## 支持的文件格式

| 格式 | 扩展名 | 提取方式 |
|---|---|---|
| PDF | `.pdf` | PyMuPDF 嵌入文本 / OCR 回退 |
| Word | `.docx` | python-docx |
| Word 97-2003 | `.doc` | LibreOffice → docx → python-docx |
| 金山 WPS | `.wps` | LibreOffice → docx → python-docx |
| OFD 版式文件 | `.ofd` | ZIP + XML 解析（零依赖） |
| 图片 | `.jpg` `.jpeg` `.png` `.tiff` `.tif` `.bmp` | OpenCV 预处理 + RapidOCR |
