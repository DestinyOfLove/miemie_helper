"""归档导出页：保留原有 Excel 导出功能。"""

import tempfile
from pathlib import Path

from nicegui import ui

from src.core.excel_exporter import EMPTY_FIELDS, export_records_to_excel, split_text_to_columns
from src.core.extractor import compute_file_hash, extract_text
from src.core.file_scanner import guess_year_from_path, scan_directory
from src.core.parser import parse_document_fields
from src.config import ALL_EXTENSIONS
from src.ui.layout import create_header


@ui.page("/archive", title="归档导出 - MieMie Helper")
def archive_page():
    create_header()

    with ui.column().classes("w-full max-w-5xl mx-auto p-4"):
        ui.label("归档导出").classes("text-h4 q-mb-md")
        ui.label(
            "批量提取公文元数据并导出为 Excel 表格。"
            "直接扫描本地目录，文件不会被复制或上传。"
        ).classes("text-body1 text-grey-8 q-mb-md")

        dir_input = ui.input(
            label="公文目录路径",
            placeholder="/path/to/documents",
        ).classes("w-full q-mb-md")

        process_btn = ui.button("开始处理", icon="play_arrow", color="primary")

        log_area = ui.textarea(label="处理日志", value="").props("readonly outlined").classes(
            "w-full q-mt-md"
        )
        log_area.visible = False

        download_link = ui.link("", "").classes("q-mt-md")
        download_link.visible = False

        async def on_process():
            directory = dir_input.value.strip()
            if not directory:
                ui.notify("请输入目录路径", type="warning")
                return

            root = Path(directory)
            if not root.is_dir():
                ui.notify(f"目录不存在: {directory}", type="negative")
                return

            process_btn.disable()
            log_area.visible = True
            log_area.value = "扫描目录中...\n"

            files = scan_directory(root)
            if not files:
                log_area.value += f"未找到支持的文件格式 ({', '.join(sorted(ALL_EXTENSIONS))})\n"
                process_btn.enable()
                return

            log_area.value += f"找到 {len(files)} 个文件\n"

            records = []
            for i, file_path in enumerate(files, 1):
                log_area.value += f"[{i}/{len(files)}] {file_path.name} ... "
                try:
                    text, method = extract_text(file_path)
                    year_hint = guess_year_from_path(file_path, root)
                    fields = parse_document_fields(text, str(file_path), year_hint) if text else dict(EMPTY_FIELDS)
                    file_hash = compute_file_hash(file_path)

                    record = {
                        **fields,
                        "文件名": file_path.name,
                        "文件路径": str(file_path),
                        "文件哈希": file_hash,
                        "提取方式": method,
                        **split_text_to_columns(text),
                    }
                    records.append(record)
                    log_area.value += f"OK ({method})\n"
                except Exception as e:
                    log_area.value += f"错误: {e}\n"

            # 导出
            tmp_dir = Path(tempfile.mkdtemp(prefix="miemie_"))
            output_path = tmp_dir / "公文汇总.xlsx"
            export_records_to_excel(records, output_path)

            log_area.value += f"\n处理完成！共 {len(records)} 条记录\n"
            log_area.value += f"输出文件: {output_path}\n"

            download_link.visible = True
            download_link.text = "下载 Excel 结果"
            download_link.set_source(f"/download/{output_path.name}")

            # 注册下载路由
            from nicegui import app as nicegui_app
            from fastapi.responses import FileResponse

            @nicegui_app.get(f"/download/{output_path.name}")
            async def download():
                return FileResponse(
                    str(output_path),
                    filename="公文汇总.xlsx",
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            process_btn.enable()
            ui.notify("处理完成！", type="positive")

        process_btn.on_click(on_process)
