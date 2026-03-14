"""共享布局：导航栏。"""

from nicegui import ui


def create_header() -> None:
    """顶部导航栏。"""
    with ui.header().classes("bg-blue-8 text-white items-center"):
        ui.label("MieMie Helper").classes("text-h6 q-mr-md")
        ui.link("首页", "/").classes("text-white text-subtitle1 q-mx-sm")
        ui.link("文档搜索", "/search").classes("text-white text-subtitle1 q-mx-sm")
