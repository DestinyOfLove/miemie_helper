"""MieMie Helper — Web 入口。"""

import re
import sys
import tempfile
import time
from pathlib import Path

import gradio as gr
import pandas as pd

# 将 doc_archive 加入路径
sys.path.insert(0, str(Path(__file__).parent.parent / "doc_archive"))

from extractor import ALL_EXTENSIONS, compute_file_hash, extract_text  # noqa: E402
from parser import parse_document_fields  # noqa: E402

# ──────────────────────────────────────────────
# 公文档案整理 — 核心逻辑
# ──────────────────────────────────────────────

# 基础列（提取文本列在输出时动态生成）
BASE_COLUMNS = [
    "序号", "发文字号", "发文标题", "发文日期", "发文机关",
    "主送单位", "公文种类", "密级", "来源年份",
    "文件名", "文件路径", "文件哈希", "提取方式",
]

# Excel 单元格字符上限（实际 32767，留些余量）
EXCEL_CELL_MAX = 32000

EMPTY_FIELDS = {
    "发文字号": "", "发文标题": "", "发文日期": "",
    "发文机关": "", "主送单位": "", "公文种类": "",
    "密级": "", "来源年份": "",
}


def split_text_to_columns(text: str) -> dict:
    """将文本拆分到多个列，每列不超过 Excel 单元格限制。"""
    if not text:
        return {"提取文本": "(无法提取)"}
    if len(text) <= EXCEL_CELL_MAX:
        return {"提取文本": text}
    # 拆分到多列
    cols = {}
    for i in range(0, len(text), EXCEL_CELL_MAX):
        chunk = text[i:i + EXCEL_CELL_MAX]
        suffix = f"_{i // EXCEL_CELL_MAX + 1}" if i > 0 else ""
        cols[f"提取文本{suffix}"] = chunk
    return cols


def guess_year_from_path(file_path: Path, root_dir: Path) -> str:
    try:
        rel_path = file_path.relative_to(root_dir)
    except ValueError:
        rel_path = file_path
    for part in rel_path.parts:
        match = re.match(r"^(19\d{2}|20\d{2})$", part)
        if match:
            return match.group(1)
    return ""


def load_existing_excel(excel_path: str | None) -> tuple[pd.DataFrame | None, set, dict]:
    """加载已有 Excel，返回 (DataFrame, 已有哈希集合, 文件名→哈希映射)。"""
    if not excel_path:
        return None, set(), {}
    try:
        df = pd.read_excel(excel_path, sheet_name="公文汇总")
        existing_hashes = set()
        name_to_hash = {}
        if "文件哈希" in df.columns:
            for _, row in df.iterrows():
                h = str(row.get("文件哈希", "")).strip()
                name = str(row.get("文件名", "")).strip()
                if h:
                    existing_hashes.add(h)
                if name and h:
                    name_to_hash[name] = h
        return df, existing_hashes, name_to_hash
    except Exception:
        return None, set(), {}


def scan_directory(dir_path: str) -> tuple[list[Path], Path | None]:
    """扫描本地目录，返回 (文件列表, 根目录)。直接读取本地路径，保留原始路径。"""
    if not dir_path or not dir_path.strip():
        return [], None
    root = Path(dir_path.strip())
    if not root.is_dir():
        return [], None
    files = []
    for f in sorted(root.rglob("*")):
        if f.is_file() and f.suffix.lower() in ALL_EXTENSIONS and not f.name.startswith((".", "~")):
            files.append(f)
    return files, root


def process_files(
    dir_path: str,
    existing_excel,
    progress=gr.Progress(track_tqdm=True),
):
    """处理入口：扫描目录 + 已有 Excel 去重。"""

    # 1. 扫描目录
    all_files, root_dir = scan_directory(dir_path)

    if not all_files:
        if not dir_path or not dir_path.strip():
            gr.Warning("请输入目录路径")
            return None, None, "请输入目录路径"
        if not Path(dir_path.strip()).is_dir():
            gr.Warning(f"目录不存在: {dir_path}")
            return None, None, f"目录不存在: {dir_path}"
        exts = ", ".join(sorted(ALL_EXTENSIONS))
        return None, None, f"目录中没有找到支持的文件格式 ({exts})"

    # 2. 加载已有 Excel（去重基准）
    excel_path = None
    if existing_excel is not None:
        if isinstance(existing_excel, str):
            excel_path = existing_excel
        elif hasattr(existing_excel, "name"):
            excel_path = existing_excel.name
        else:
            excel_path = str(existing_excel)
    existing_df, existing_hashes, name_to_hash = load_existing_excel(excel_path)

    # 3. 处理文件（含去重）
    records = []
    errors = []
    log_lines = []
    skipped = 0
    processed = 0

    for i, file_path in enumerate(progress.tqdm(all_files, desc="处理文件")):
        file_hash = compute_file_hash(file_path)
        file_name = file_path.name

        # 去重：哈希已存在 → 跳过
        if file_hash in existing_hashes:
            skipped += 1
            log_lines.append(f"[{i+1}/{len(all_files)}] {file_name} ... 跳过 (已处理过)")
            continue

        # 重名警告：文件名相同但哈希不同
        if file_name in name_to_hash and name_to_hash[file_name] != file_hash:
            log_lines.append(f"[{i+1}/{len(all_files)}] {file_name} ... 警告: 文件名重复但内容不同!")

        log_lines.append(f"[{i+1}/{len(all_files)}] {file_name} ...")
        start = time.time()

        try:
            text, method = extract_text(file_path)
            year_hint = guess_year_from_path(file_path, root_dir) if root_dir else ""

            fields = parse_document_fields(text, str(file_path), year_hint) if text else dict(EMPTY_FIELDS)

            record = {
                **fields,
                "文件名": file_name,
                "文件路径": str(file_path),
                "文件哈希": file_hash,
                "提取方式": method,
                **split_text_to_columns(text),
            }
            records.append(record)
            processed += 1

            elapsed = time.time() - start
            status = "OK" if text else "无文本"
            log_lines[-1] += f" {status} ({elapsed:.1f}s, {method})"

        except Exception as e:
            elapsed = time.time() - start
            log_lines[-1] += f" 错误 ({elapsed:.1f}s): {e}"
            errors.append(str(e))
            records.append({
                **EMPTY_FIELDS,
                "文件名": file_name,
                "文件路径": str(file_path),
                "文件哈希": file_hash,
                "提取方式": "错误",
                "提取文本": f"错误: {e}",
            })
            processed += 1

    # 4. 合并已有数据和新数据
    new_df = pd.DataFrame(records) if records else pd.DataFrame(columns=BASE_COLUMNS + ["提取文本"])

    if existing_df is not None and not existing_df.empty:
        for col in BASE_COLUMNS:
            if col not in existing_df.columns:
                existing_df[col] = ""
        merged_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        merged_df = new_df

    # 重新编序号
    merged_df["序号"] = range(1, len(merged_df) + 1)

    for col in BASE_COLUMNS:
        if col not in merged_df.columns:
            merged_df[col] = ""

    # 动态收集所有 "提取文本" 列并排序
    text_cols = sorted([c for c in merged_df.columns if c.startswith("提取文本")])
    if not text_cols:
        merged_df["提取文本"] = ""
        text_cols = ["提取文本"]

    merged_df = merged_df[BASE_COLUMNS + text_cols]

    # 5. 输出 Excel
    tmp_dir = Path(tempfile.mkdtemp(prefix="miemie_"))
    output_path = tmp_dir / "公文汇总.xlsx"
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        merged_df.to_excel(writer, sheet_name="公文汇总", index=False)

    # 6. 汇总日志
    summary_parts = [f"处理完成: 新增 {processed} 个文件"]
    if skipped:
        summary_parts.append(f"跳过 {skipped} 个 (已处理过)")
    if existing_df is not None:
        summary_parts.append(f"已有记录 {len(existing_df)} 条")
    summary_parts.append(f"合计 {len(merged_df)} 条记录")
    if errors:
        summary_parts.append(f"{len(errors)} 个出错")

    summary = " | ".join(summary_parts)
    log_text = "\n".join(log_lines)

    return merged_df, str(output_path), f"{summary}\n\n{log_text}"


# ──────────────────────────────────────────────
# Gradio UI
# ──────────────────────────────────────────────

CUSTOM_CSS = """
.tool-card {
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 20px;
    margin: 8px;
    transition: box-shadow 0.2s;
    cursor: pointer;
}
.tool-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.header-text {
    text-align: center;
    margin-bottom: 8px;
}
"""

with gr.Blocks(title="MieMie Helper") as app:

    # ── 顶部标题 ──
    gr.Markdown(
        """
        # MieMie Helper
        **工作与生活辅助工具集** &nbsp;|&nbsp; 所有数据本地处理，不上传任何内容
        """,
        elem_classes="header-text",
    )

    # ── 工具入口 ──
    with gr.Tabs():

        # ──── Tab: 工具总览 ────
        with gr.Tab("工具总览", id="home"):
            gr.Markdown("### 可用工具")
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown(
                        """
                        #### 公文档案整理

                        批量解析公文文件（PDF / Word / 扫描图片），自动提取发文字号、标题、日期等信息，
                        汇总输出为 Excel 表格。支持增量处理和自动去重。

                        **支持格式**: PDF, DOCX, JPG, PNG, TIFF, BMP
                        """,
                        elem_classes="tool-card",
                    )
                with gr.Column(scale=1):
                    gr.Markdown(
                        """
                        #### 更多工具

                        即将推出...

                        """,
                        elem_classes="tool-card",
                    )

        # ──── Tab: 公文档案整理 ────
        with gr.Tab("公文档案整理", id="doc_archive"):
            gr.Markdown("### 公文档案整理")
            gr.Markdown("输入公文目录路径，自动递归扫描、提取关键信息并生成 Excel 汇总表。支持增量去重。")

            # ── 输入区域 ──
            with gr.Row():
                with gr.Column(scale=3):
                    dir_path_input = gr.Textbox(
                        label="公文目录路径（直接扫描本地目录，保留原始文件路径）",
                        placeholder="粘贴或输入目录路径，如 /Users/xxx/公文",
                        lines=1,
                    )
                with gr.Column(scale=2):
                    existing_excel_input = gr.File(
                        label="已有 Excel（可选，用于增量去重）",
                        file_count="single",
                        file_types=[".xlsx"],
                    )

            process_btn = gr.Button("开始处理", variant="primary", size="lg")

            # ── 结果区域 ──
            result_log = gr.Textbox(label="处理日志", lines=8, interactive=False)
            result_table = gr.Dataframe(label="提取结果", interactive=False, wrap=True)
            result_download = gr.File(label="下载 Excel 结果")

            gr.Markdown(
                """
                ---
                **说明**: 直接扫描本地目录，文件不会被复制或上传，路径保留原始位置。
                OCR 引擎为 RapidOCR (离线运行)。下载后可自行决定覆盖原文件或另存。
                """,
            )

            # ── 事件绑定 ──
            process_btn.click(
                fn=process_files,
                inputs=[dir_path_input, existing_excel_input],
                outputs=[result_table, result_download, result_log],
            )


if __name__ == "__main__":
    app.launch(server_port=4001, share=False, css=CUSTOM_CSS, theme=gr.themes.Soft())
