"""文档搜索页：索引管理 + 双栏搜索结果。"""

import asyncio

from nicegui import ui

from src.search import document_db
from src.search.indexer import indexing_status, start_indexing_background
from src.search.models import SearchResult
from src.ui.layout import create_header


@ui.page("/search", title="文档搜索 - MieMie Helper")
def search_page():
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
                    {"name": "path", "label": "目录", "field": "directory_path", "align": "left"},
                    {"name": "files", "label": "文件数", "field": "file_count"},
                    {"name": "indexed", "label": "已索引", "field": "indexed_count"},
                    {"name": "status", "label": "状态", "field": "status"},
                    {"name": "last_scan", "label": "最后扫描", "field": "last_scan_at"},
                ],
                rows=[],
            ).classes("w-full")

        # ── 搜索区域 ──
        with ui.row().classes("w-full items-end gap-4 q-mb-md"):
            query_input = ui.input(
                label="搜索内容",
                placeholder="输入关键词或描述你要找的内容...",
            ).classes("flex-1")
            search_btn = ui.button("搜索", icon="search", color="primary")

        # ── 双栏结果 ──
        with ui.row().classes("w-full gap-4"):
            with ui.column().classes("flex-1"):
                ui.label("全文检索结果").classes("text-h6")
                ui.label("精确关键词匹配").classes("text-caption text-grey q-mb-sm")
                fts_container = ui.column().classes("w-full")

            ui.separator().props("vertical")

            with ui.column().classes("flex-1"):
                ui.label("语义检索结果").classes("text-h6")
                ui.label("含义相似度匹配").classes("text-caption text-grey q-mb-sm")
                vec_container = ui.column().classes("w-full")

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

            # 等待后台线程开始
            await asyncio.sleep(0.2)

            # 轮询直到完成（不依赖 is_running 的精确时序）
            while True:
                status = indexing_status.to_response()
                if status.phase in ("complete", "error") or not status.is_running:
                    break
                total = status.total_files or 1
                done = status.processed_files + status.skipped
                progress.set_value(done / total)
                status_label.text = (
                    f"{status.phase} | 处理中: {status.current_file} | "
                    f"新增 {status.added} / 更新 {status.updated} / "
                    f"跳过 {status.skipped} / 删除 {status.deleted}"
                )
                await asyncio.sleep(0.5)

            # 读取最终状态
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
            fts_container.clear()
            vec_container.clear()

            try:
                # 动态导入避免循环依赖
                from src.api.search_routes import _fulltext_search, _vector_search

                fts_results = _fulltext_search(query, 20)
                vec_results = _vector_search(query, 20)

                _render_results(fts_container, fts_results, "全文")
                _render_results(vec_container, vec_results, "语义")

                if not fts_results and not vec_results:
                    with fts_container:
                        ui.label("无匹配结果").classes("text-grey q-pa-md")
                    with vec_container:
                        ui.label("无匹配结果").classes("text-grey q-pa-md")

            except Exception as e:
                ui.notify(f"搜索出错: {e}", type="negative")
            finally:
                search_btn.enable()

        index_btn.on_click(on_start_indexing)
        search_btn.on_click(on_search)
        query_input.on("keydown.enter", on_search)

        # 页面加载时刷新目录表
        ui.timer(0.1, refresh_dir_table, once=True)


def _render_results(container, results: list[SearchResult], label: str) -> None:
    """渲染搜索结果列表。"""
    with container:
        if not results:
            ui.label(f"无{label}匹配结果").classes("text-grey q-pa-md")
            return

        for i, r in enumerate(results):
            with ui.card().classes("w-full q-mb-sm"):
                with ui.card_section().classes("q-pb-none"):
                    # 标题行
                    title_text = r.title or r.file_name
                    ui.label(title_text).classes("text-subtitle1 text-weight-medium")

                    # 标签
                    with ui.row().classes("gap-1 q-mt-xs"):
                        if r.doc_number:
                            ui.badge(r.doc_number, color="blue-2", text_color="blue-9").classes("text-caption")
                        if r.source_year:
                            ui.badge(r.source_year, color="green-2", text_color="green-9").classes("text-caption")
                        if r.doc_type:
                            ui.badge(r.doc_type, color="orange-2", text_color="orange-9").classes("text-caption")
                        if r.score > 0:
                            score_text = f"{r.score:.2f}"
                            ui.badge(score_text, color="grey-3", text_color="grey-8").classes("text-caption")

                with ui.card_section().classes("q-pt-sm"):
                    # snippet
                    if r.snippet:
                        ui.html(r.snippet).classes("text-body2 text-grey-8")

                    # 文件路径
                    ui.label(r.file_path).classes("text-caption text-grey q-mt-xs")
