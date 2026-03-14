"""首页：工具集入口。"""

from nicegui import ui

from src.ui.layout import create_header


@ui.page("/", title="MieMie Helper")
def home_page():
    create_header()

    with ui.column().classes("w-full max-w-5xl mx-auto p-8"):
        ui.label("工具集").classes("text-h4 q-mb-lg")
        ui.label("所有数据本地处理，不上传任何内容").classes("text-subtitle1 text-grey q-mb-lg")

        with ui.row().classes("w-full gap-4"):
            # 文档搜索
            with ui.card().classes("cursor-pointer flex-1").on("click", lambda: ui.navigate.to("/search")):
                with ui.card_section():
                    ui.icon("search", size="2rem").classes("text-blue-8 q-mb-sm")
                    ui.label("文档搜索").classes("text-h6")
                    ui.label(
                        "在公文文件中搜索关键词。"
                        "支持全文精确匹配，并可按字段范围检索。"
                    ).classes("text-body2 text-grey-8")
                    ui.label("PDF / DOCX / JPG / PNG / TIFF / BMP").classes(
                        "text-caption text-grey q-mt-sm"
                    )

            # 更多工具
            with ui.card().classes("flex-1 opacity-50"):
                with ui.card_section():
                    ui.icon("more_horiz", size="2rem").classes("text-grey q-mb-sm")
                    ui.label("更多工具").classes("text-h6")
                    ui.label("即将推出...").classes("text-body2 text-grey")
