"""Excel 导出工具。"""

from pathlib import Path

import pandas as pd

from src.config import EXCEL_CELL_MAX

# 基础列定义
BASE_COLUMNS = [
    "序号", "发文字号", "发文标题", "发文日期", "发文机关",
    "主送单位", "公文种类", "密级", "来源年份",
    "文件名", "文件路径", "文件哈希", "提取方式",
]

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
    cols = {}
    for i in range(0, len(text), EXCEL_CELL_MAX):
        chunk = text[i:i + EXCEL_CELL_MAX]
        suffix = f"_{i // EXCEL_CELL_MAX + 1}" if i > 0 else ""
        cols[f"提取文本{suffix}"] = chunk
    return cols


def export_records_to_excel(
    records: list[dict],
    output_path: Path,
    existing_df: pd.DataFrame | None = None,
) -> Path:
    """将记录列表导出为 Excel 文件。支持与已有 DataFrame 合并。"""
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

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        merged_df.to_excel(writer, sheet_name="公文汇总", index=False)

    return output_path
