"""公文档案整理工具 — 主入口。

用法：
    uv run python src/doc_archive/main.py <公文根目录> [--output 输出文件.xlsx]

目录结构示例：
    公文根目录/
    ├── 1993/
    │   ├── 子目录/
    │   │   ├── 文件1.pdf
    │   │   └── 文件2.jpg
    ├── 2024/
    │   └── 文件3.docx
    └── ...
"""

import argparse
import re
import sys
import time
from pathlib import Path

import pandas as pd

from extractor import ALL_EXTENSIONS, extract_text
from parser import parse_document_fields


def scan_directory(root_dir: Path) -> list[Path]:
    """递归扫描目录，返回所有支持的文件路径。"""
    files = []
    for file_path in sorted(root_dir.rglob("*")):
        if file_path.is_file() and file_path.suffix.lower() in ALL_EXTENSIONS:
            # 跳过隐藏文件和临时文件
            if file_path.name.startswith((".", "~")):
                continue
            files.append(file_path)
    return files


def guess_year_from_path(file_path: Path, root_dir: Path) -> str:
    """从文件路径中推断年份。"""
    rel_path = file_path.relative_to(root_dir)
    parts = rel_path.parts
    for part in parts:
        match = re.match(r"^(19\d{2}|20\d{2})$", part)
        if match:
            return match.group(1)
    return ""


def process_files(root_dir: Path, output_path: Path) -> None:
    """处理所有文件并输出到 Excel。"""
    root_dir = root_dir.resolve()
    files = scan_directory(root_dir)

    if not files:
        print(f"在 {root_dir} 下未找到支持的文件")
        sys.exit(1)

    print(f"共找到 {len(files)} 个文件待处理")
    print(f"支持的格式：{', '.join(sorted(ALL_EXTENSIONS))}")
    print("-" * 60)

    records = []
    errors = []

    for i, file_path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] 处理: {file_path.name} ...", end=" ", flush=True)
        start = time.time()

        try:
            text, method = extract_text(file_path)
            year_hint = guess_year_from_path(file_path, root_dir)

            if text:
                fields = parse_document_fields(text, str(file_path), year_hint)
            else:
                fields = {
                    "发文字号": "",
                    "发文标题": "",
                    "发文日期": "",
                    "发文机关": "",
                    "主送单位": "",
                    "公文种类": "",
                    "密级": "",
                    "来源年份": year_hint,
                }

            record = {
                "序号": i,
                **fields,
                "文件名": file_path.name,
                "文件路径": str(file_path),
                "提取方式": method,
                "提取文本(前200字)": text[:200] if text else "(无法提取)",
            }
            records.append(record)

            elapsed = time.time() - start
            status = "OK" if text else "无文本"
            print(f"{status} ({elapsed:.1f}s, {method})")

        except Exception as e:
            elapsed = time.time() - start
            print(f"错误 ({elapsed:.1f}s): {e}")
            errors.append({"文件": str(file_path), "错误": str(e)})
            records.append({
                "序号": i,
                "发文字号": "",
                "发文标题": "",
                "发文日期": "",
                "发文机关": "",
                "主送单位": "",
                "公文种类": "",
                "密级": "",
                "来源年份": guess_year_from_path(file_path, root_dir),
                "文件名": file_path.name,
                "文件路径": str(file_path),
                "提取方式": "错误",
                "提取文本(前200字)": f"错误: {e}",
            })

    # 输出 Excel
    print("-" * 60)
    df = pd.DataFrame(records)

    # 定义列顺序
    columns = [
        "序号", "发文字号", "发文标题", "发文日期", "发文机关",
        "主送单位", "公文种类", "密级", "来源年份",
        "文件名", "文件路径", "提取方式", "提取文本(前200字)",
    ]
    df = df[columns]

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="公文汇总", index=False)

        # 如果有错误，单独写一个 sheet
        if errors:
            df_errors = pd.DataFrame(errors)
            df_errors.to_excel(writer, sheet_name="处理错误", index=False)

    print(f"处理完成！共 {len(records)} 条记录")
    if errors:
        print(f"其中 {len(errors)} 个文件处理出错，详见[处理错误]工作表")
    print(f"输出文件: {output_path}")


def main():
    argparser = argparse.ArgumentParser(
        description="公文档案整理工具 — 批量解析公文文件，输出结构化 Excel 表格"
    )
    argparser.add_argument("input_dir", type=Path, help="公文文件根目录")
    argparser.add_argument(
        "--output", "-o", type=Path, default=None,
        help="输出 Excel 文件路径（默认：<输入目录>/公文汇总.xlsx）"
    )
    args = argparser.parse_args()

    input_dir = args.input_dir.resolve()
    if not input_dir.is_dir():
        print(f"错误：目录不存在 - {input_dir}")
        sys.exit(1)

    output_path = args.output or (input_dir / "公文汇总.xlsx")

    print("=" * 60)
    print("公文档案整理工具")
    print("=" * 60)
    print(f"输入目录: {input_dir}")
    print(f"输出文件: {output_path}")
    print("=" * 60)

    process_files(input_dir, output_path)


if __name__ == "__main__":
    main()
