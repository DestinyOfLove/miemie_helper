"""MieMie Helper — 应用入口。"""

from nicegui import app, ui

from src.api.export_routes import router as export_router
from src.api.index_routes import router as index_router
from src.api.search_routes import router as search_router

# 挂载 FastAPI 路由
app.include_router(index_router)
app.include_router(search_router)
app.include_router(export_router)

# 导入 NiceGUI 页面（注册 @ui.page 装饰器）
import src.ui.archive_page  # noqa: F401, E402
import src.ui.home_page  # noqa: F401, E402
import src.ui.search_page  # noqa: F401, E402

if __name__ == "__main__":
    ui.run(
        title="MieMie Helper",
        port=4001,
        reload=False,
        show=False,
    )
