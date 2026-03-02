"""文档搜索页：索引管理 + AG Grid 搜索结果。"""

import asyncio
import os
import re

from nicegui import ui

from src.search import document_db
from src.search.indexer import indexing_status, start_indexing_background
from src.ui.layout import create_header


@ui.page("/search", title="文档搜索 - MieMie Helper")
def search_page():
    # mark 高亮样式
    ui.add_head_html("""
        <style>
            mark { background: #FFF176; padding: 1px 2px; border-radius: 2px; }
            .ag-cell { align-items: flex-start !important; }
        </style>
    """)

    create_header()

    with ui.column().classes("w-full max-w-7xl mx-auto p-4"):
        ui.label("文档搜索").classes("text-h4 q-mb-md")

        # ── 索引管理区域 ──
        with ui.expansion("索引管理", icon="settings").classes("w-full q-mb-md"):
            with ui.row().classes("w-full items-end gap-4"):
                dir_input = ui.input(
                    label="目录路径",
                    placeholder="/path/to/documents",
                ).classes("flex-1")
                index_btn = ui.button("开始索引", icon="play_arrow", color="primary")

            status_label = ui.label("").classes("text-caption q-mt-sm")
            progress = ui.linear_progress(value=0, show_value=False).classes("w-full")
            progress.visible = False

            ui.separator().classes("q-my-sm")
            ui.label("已索引目录").classes("text-subtitle2")
            dir_table = ui.table(
                columns=[
                    {"name": "path",      "label": "目录",     "field": "directory_path", "align": "left"},
                    {"name": "files",     "label": "文件数",   "field": "file_count"},
                    {"name": "indexed",   "label": "已索引",   "field": "indexed_count"},
                    {"name": "status",    "label": "状态",     "field": "status"},
                    {"name": "last_scan", "label": "最后扫描", "field": "last_scan_at"},
                ],
                rows=[],
            ).classes("w-full")

        # ── 搜索区域 ──
        with ui.row().classes("w-full items-end gap-4 q-mb-sm"):
            query_input = ui.input(
                label="搜索内容",
                placeholder="输入关键词或描述你要找的内容...",
            ).classes("flex-1")
            search_btn = ui.button("搜索", icon="search", color="primary")

        results_count = ui.label("").classes("text-caption text-grey q-mb-xs")

        # ── AG Grid 搜索结果 ──
        results_grid = ui.aggrid({
            "columnDefs": [
                {
                    "field": "year",
                    "headerName": "年份",
                    "width": 80,
                    "sortable": True,
                    "filter": "agTextColumnFilter",
                },
                {
                    "field": "file_name",
                    "headerName": "文件名",
                    "flex": 1,
                    "minWidth": 160,
                    "sortable": True,
                    "filter": "agTextColumnFilter",
                    "floatingFilter": True,
                    "wrapText": True,
                    "autoHeight": True,
                },
                {
                    "field": "content",
                    "headerName": "内容",
                    "flex": 3,
                    "minWidth": 320,
                    "autoHeight": True,
                    "wrapText": True,
                },
            ],
            "rowData": [],
            "domLayout": "autoHeight",
            "defaultColDef": {"resizable": True},
            "theme": "quartz",
        }, html_columns=[2, 3]).classes("w-full")

        # ── 事件处理 ──

        async def on_start_indexing():
            directory = dir_input.value.strip()
            if not directory:
                ui.notify("请输入目录路径", type="warning")
                return

            started = start_indexing_background(directory)
            if not started:
                ui.notify("索引任务正在运行中", type="warning")
                return

            ui.notify(f"索引任务已启动: {directory}", type="positive")
            progress.visible = True
            index_btn.disable()

            await asyncio.sleep(0.2)

            while True:
                status = indexing_status.to_response()
                if status.phase in ("complete", "error") or not status.is_running:
                    break
                total = status.total_files or 1
                done = status.processed_files + status.skipped
                pct = int(done / total * 100)
                progress.set_value(done / total)
                status_label.text = (
                    f"[{done}/{total} {pct}%] {status.current_file} | "
                    f"新增 {status.added} / 更新 {status.updated} / "
                    f"跳过 {status.skipped} / 删除 {status.deleted}"
                )
                await asyncio.sleep(0.5)

            final = indexing_status.to_response()
            progress.set_value(1.0)
            status_label.text = (
                f"完成! 新增 {final.added}, 更新 {final.updated}, "
                f"删除 {final.deleted}, 跳过 {final.skipped}"
            )
            if final.errors:
                status_label.text += f", 错误 {len(final.errors)}"
            index_btn.enable()
            await refresh_dir_table()

        async def refresh_dir_table():
            dirs = document_db.get_all_directories()
            dir_table.rows = [d.model_dump() for d in dirs]
            dir_table.update()

        async def on_search():
            query = query_input.value.strip()
            if not query:
                ui.notify("请输入搜索内容", type="warning")
                return

            search_btn.disable()
            results_grid.options["rowData"] = []
            results_grid.update()
            results_count.text = "搜索中..."

            try:
                from src.api.search_routes import _fulltext_search

                # 仅使用全文检索（精准匹配），不启用向量检索
                fts_results = _fulltext_search(query)

                rows = []
                for r in fts_results:
                    # 从发文字号中提取年份
                    year = ""
                    if r.doc_number:
                        match = re.search(r"[〔\[【（(]\s*(\d{4})\s*[〕\]】）)]", r.doc_number)
                        if match:
                            year = match.group(1)

                    rows.append({
                        "year": year,
                        "file_name": r.file_name,
                        "content": r.snippet or "",
                    })

                results_grid.options["rowData"] = rows
                results_grid.update()
                results_count.text = f"共 {len(rows)} 条结果"

                if not rows:
                    ui.notify("无匹配结果", type="warning")

            except Exception as e:
                ui.notify(f"搜索出错: {e}", type="negative")
                results_count.text = ""
            finally:
                search_btn.enable()

        index_btn.on_click(on_start_indexing)
        search_btn.on_click(on_search)
        query_input.on("keydown.enter", on_search)

        ui.timer(0.1, refresh_dir_table, once=True)
