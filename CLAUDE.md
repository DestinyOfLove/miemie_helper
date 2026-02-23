# MieMie Helper

工作与生活辅助工具集合项目。采用模块化设计，每个工具作为独立模块，按需扩展。

## 项目定位

- 以 Python 为主要开发语言
- 本地离线运行，不依赖网络服务
- 跨平台：macOS 开发，Windows 部署
- 使用 `uv` 管理 Python 项目和依赖

## 当前工具模块

### 1. 发文档案整理工具（doc_archive）

**背景**：将 1993-2025 年历年发文文件统一整理到结构化表格中，集中管理。

**文件范围**：
- 目录结构：按年份文件夹 → 子文件夹 → 发文文件
- 文件类型：扫描件图片（JPG/PNG/TIFF）、Word 文档（.doc/.docx）、PDF（扫描型 + 文本型）

**约束条件**：
- 必须本地离线处理（涉密内容）
- 脚本自动化批量处理
- 输出为统一 Excel 表格

**核心技术栈**：
- OCR 引擎：RapidOCR（基于 ONNX，跨平台零障碍，中文识别质量好）
- PDF 处理：PyMuPDF（PDF 转图片 + 文本提取）
- Word 处理：python-docx（.docx），LibreOffice 命令行转换（.doc）
- 图像预处理：Pillow + OpenCV
- 数据输出：pandas + openpyxl

## 开发规范

- 使用 `uv` 初始化和管理项目
- 模块化结构，每个工具独立目录
- 响应语言：中文
