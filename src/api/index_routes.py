"""索引管理 API 路由。"""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from src.search import document_db
from src.search.indexer import (
    indexing_status,
    scan_directory_changes,
    start_indexing_background,
    start_rebuild_background,
)
from src.search.models import (
    DirectoryInfo,
    IndexRequest,
    IndexStatusResponse,
    ScanChangesResponse,
)

router = APIRouter(prefix="/api/index", tags=["indexing"])


def _validate_directory(path: str) -> Path:
    """验证目录路径安全，防止路径遍历攻击。

    1. 解析相对路径为绝对路径
    2. 验证路径确实存在且是目录
    3. 验证路径没有超出预期的安全范围（通过检查 realpath）

    Args:
        path: 用户提供的目录路径

    Returns:
        解析并验证后的绝对路径

    Raises:
        HTTPException: 路径无效或不存在
    """
    try:
        directory = Path(path).resolve()
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=400, detail=f"无效的路径: {path}")

    if not directory.exists():
        raise HTTPException(status_code=400, detail=f"目录不存在: {directory}")

    if not directory.is_dir():
        raise HTTPException(status_code=400, detail=f"路径不是目录: {directory}")

    # 防止符号链接绕过：检查 realpath 是否与预期不符
    try:
        real_path = Path(path).resolve()
        if real_path != directory:
            raise HTTPException(
                status_code=400,
                detail="检测到符号链接绕过尝试",
            )
    except Exception:
        pass

    return directory


@router.post("/start")
async def start_indexing(request: IndexRequest) -> dict:
    """启动后台索引任务。"""
    directory = _validate_directory(request.directory)

    started = start_indexing_background(str(directory))
    if not started:
        raise HTTPException(status_code=409, detail="索引任务正在运行中")

    return {"message": "索引任务已启动", "directory": str(directory)}


@router.get("/status", response_model=IndexStatusResponse)
async def get_index_status() -> IndexStatusResponse:
    """获取当前索引状态。"""
    return indexing_status.to_response()


@router.get("/directories", response_model=list[DirectoryInfo])
async def list_indexed_directories() -> list[DirectoryInfo]:
    """列出所有已索引目录。"""
    return document_db.get_all_directories()


@router.get("/scan-changes", response_model=ScanChangesResponse)
async def scan_changes() -> ScanChangesResponse:
    """扫描所有已索引目录的文件变更。"""
    dirs = document_db.get_all_directories()
    results = [scan_directory_changes(d.directory_path) for d in dirs]
    return ScanChangesResponse(results=results)


@router.post("/directory/star")
async def toggle_star(request: IndexRequest) -> dict:
    """切换目录星标状态。"""
    new_state = document_db.toggle_directory_starred(request.directory)
    return {"directory": request.directory, "starred": new_state}


@router.delete("/directory")
async def remove_directory_index(directory: str) -> dict:
    """删除某目录的全部索引数据。"""
    if indexing_status.is_running:
        raise HTTPException(status_code=409, detail="索引任务正在运行中，请稍后再试")

    from src.search.fulltext_store import delete_fts_by_directory
    from src.search.vector_store import delete_document_chunks

    # 获取该目录下所有文档 ID
    docs = document_db.get_documents_by_directory(directory)
    doc_ids = [d.id for d in docs]

    # 删除 FTS5 记录
    delete_fts_by_directory(doc_ids)

    # 删除 ChromaDB 分块
    for doc_id in doc_ids:
        delete_document_chunks(doc_id)

    # 删除 SQLite 文档记录
    count = document_db.delete_documents_by_directory(directory)

    # 删除目录记录
    document_db.delete_directory(directory)

    return {"message": f"已删除 {count} 条记录", "directory": directory}


@router.post("/directory/rebuild")
async def rebuild_directory_index(request: IndexRequest) -> dict:
    """删除某目录全部索引后重新全量索引。"""
    directory = _validate_directory(request.directory)

    started = start_rebuild_background(str(directory))
    if not started:
        raise HTTPException(status_code=409, detail="索引任务正在运行中")

    return {"message": "重建索引已启动", "directory": str(directory)}
