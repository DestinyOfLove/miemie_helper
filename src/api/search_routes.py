"""搜索 API 路由 - 仅全文检索（双引号精确匹配）。"""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter

from src.search import document_db, fulltext_store
from src.search.models import SearchRequest, SearchResult

router = APIRouter(prefix="/api/search", tags=["search"])

_executor = ThreadPoolExecutor(max_workers=4)


def _run_in_executor(func, *args):
    """在线程池中同步执行函数。"""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(_executor, func, *args)


def _cleanup_executor() -> None:
    """应用关闭时释放线程池。"""
    _executor.shutdown(wait=False, cancel_futures=True)


@router.post("/", response_model=list[SearchResult])
async def search(request: SearchRequest) -> list[SearchResult]:
    """全文检索（双引号精确匹配）。"""
    return await _run_in_executor(
        _fulltext_search, request.query, request.scopes, request.directories,
        request.limit, request.offset
    )


def _fulltext_search(query: str, scopes: list[str] | None = None,
                     directories: list[str] | None = None,
                     limit: int = 100, offset: int = 0) -> list[SearchResult]:
    """执行全文检索并丰富元数据。"""
    fts_results = fulltext_store.search_fulltext(query, scopes, directories, limit, offset)
    if not fts_results:
        return []

    doc_ids = list({r["doc_id"] for r in fts_results})
    docs = document_db.get_documents_by_ids(doc_ids)

    results = []
    for r in fts_results:
        doc = docs.get(r["doc_id"])
        if doc is None:
            continue
        results.append(SearchResult(
            doc_id=r["doc_id"],
            file_path=doc.file_path,
            file_name=doc.file_name,
            title=doc.title,
            doc_number=doc.doc_number,
            doc_date=doc.doc_date,
            issuing_authority=doc.issuing_authority,
            doc_type=doc.doc_type,
            source_year=doc.source_year,
            score=abs(r["rank"]),
            snippet=r["snippet"],
            extracted_text=doc.extracted_text,
            match_type="fulltext",
        ))
    return results
