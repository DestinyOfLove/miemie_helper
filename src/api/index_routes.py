"""索引管理 API 路由。"""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from src.search import document_db
from src.search.indexer import indexing_status, start_indexing_background
from src.search.models import DirectoryInfo, IndexRequest, IndexStatusResponse

router = APIRouter(prefix="/api/index", tags=["indexing"])


@router.post("/start")
async def start_indexing(request: IndexRequest) -> dict:
    """启动后台索引任务。"""
    directory = Path(request.directory).resolve()
    if not directory.is_dir():
        raise HTTPException(status_code=400, detail=f"目录不存在: {directory}")

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
