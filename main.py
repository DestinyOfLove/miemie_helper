"""MieMie Helper — 应用入口（FastAPI + React 静态文件）。"""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from src.api.archive_routes import router as archive_router
from src.api.export_routes import router as export_router
from src.api.index_routes import router as index_router
from src.api.search_routes import router as search_router

app = FastAPI(title="MieMie Helper")

app.include_router(index_router)
app.include_router(search_router)
app.include_router(export_router)
app.include_router(archive_router)

STATIC_DIR = Path(__file__).parent / "static"


def _setup_static() -> None:
    """挂载前端静态文件，SPA 路由回落到 index.html。"""
    if not STATIC_DIR.exists():
        return

    # 挂载静态资源（JS/CSS/图片等）
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    # 所有非 /api 路由返回 index.html（SPA 客户端路由）
    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str) -> FileResponse:
        return FileResponse(str(STATIC_DIR / "index.html"))


_setup_static()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=4001,
        reload=False,
    )
