"""MieMie Helper — 应用入口（FastAPI + Next.js 静态导出）。"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from src.api.index_routes import router as index_router
from src.api.search_routes import router as search_router, _cleanup_executor
from src.api.system_routes import router as system_router
from src.config import BUNDLE_ROOT, WEB_PORT


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。"""
    yield
    # 关闭时清理线程池
    _cleanup_executor()


app = FastAPI(title="MieMie Helper", lifespan=lifespan)

app.include_router(index_router)
app.include_router(search_router)
app.include_router(system_router)

ROOT = Path(__file__).parent.resolve()
FRONTEND_EXPORT_DIR = ROOT / "frontend" / "out"
if not FRONTEND_EXPORT_DIR.exists():
    FRONTEND_EXPORT_DIR = BUNDLE_ROOT / "frontend" / "out"


def _is_within_export_dir(path: Path) -> bool:
    """确保静态文件解析不会越过导出目录。"""
    try:
        path.resolve().relative_to(FRONTEND_EXPORT_DIR.resolve())
        return True
    except ValueError:
        return False


def _resolve_export_file(full_path: str) -> tuple[Path, int] | None:
    """按 Next.js static export 规则解析请求路径到实际文件。"""
    rel_path = Path(full_path.strip("/"))

    if not full_path or full_path == "/":
        candidate = FRONTEND_EXPORT_DIR / "index.html"
        return (candidate, 200) if candidate.is_file() else None

    candidates = [FRONTEND_EXPORT_DIR / rel_path]
    if not rel_path.suffix:
        candidates.extend([
            FRONTEND_EXPORT_DIR / f"{full_path}.html",
            FRONTEND_EXPORT_DIR / rel_path / "index.html",
        ])

    for candidate in candidates:
        if candidate.is_file() and _is_within_export_dir(candidate):
            return candidate, 200

    not_found = FRONTEND_EXPORT_DIR / "404.html"
    if not_found.is_file():
        return not_found, 404
    return None


def _setup_static() -> None:
    """挂载 Next.js static export 文件。"""
    if not FRONTEND_EXPORT_DIR.exists():
        return

    @app.get("/{full_path:path}")
    async def exported_frontend(full_path: str) -> FileResponse:
        resolved = _resolve_export_file(full_path)
        if resolved is None:
            raise HTTPException(status_code=404, detail="Not Found")
        file_path, status_code = resolved
        return FileResponse(str(file_path), status_code=status_code)


_setup_static()


def run_server(host: str = "0.0.0.0", port: int = WEB_PORT) -> None:
    """启动 Web 服务。"""
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    run_server()
