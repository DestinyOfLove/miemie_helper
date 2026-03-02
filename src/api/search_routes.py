"""搜索 API 路由。"""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, FastAPI

from src.search import document_db, fulltext_store, vector_store
from src.search.embedding import encode_query
from src.search.models import DualSearchResponse, SearchRequest, SearchResult

router = APIRouter(prefix="/api/search", tags=["search"])

_executor = ThreadPoolExecutor(max_workers=4)


def _run_in_executor(func, *args):
    """在线程池中同步执行函数。"""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(_executor, func, *args)


def _cleanup_executor():
    """清理线程池执行器。"""
    _executor.shutdown(wait=True)


async def _run_parallel(*coros):
    """并行执行多个协程。"""
    return await asyncio.gather(*coros)


@router.post("/", response_model=DualSearchResponse)
async def dual_search(request: SearchRequest) -> DualSearchResponse:
    """同时执行全文检索和向量检索，返回双栏结果。"""
    dirs = request.directories or None

    fulltext_coro = _run_in_executor(
        _fulltext_search, request.query, request.scopes, dirs,
        request.limit, request.offset
    )
    vector_coro = _run_in_executor(
        _vector_search, request.query, dirs, request.limit, request.offset
    )
    fulltext_results, vector_results = await _run_parallel(fulltext_coro, vector_coro)
    return DualSearchResponse(
        fulltext_results=fulltext_results,
        vector_results=vector_results,
    )


@router.post("/fulltext", response_model=list[SearchResult])
async def fulltext_search(request: SearchRequest) -> list[SearchResult]:
    """仅全文检索。"""
    return await _run_in_executor(
        _fulltext_search, request.query, request.scopes, request.directories,
        request.limit, request.offset
    )


@router.post("/vector", response_model=list[SearchResult])
async def vector_search_endpoint(request: SearchRequest) -> list[SearchResult]:
    """仅向量检索。"""
    return await _run_in_executor(
        _vector_search, request.query, request.directories,
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


def _vector_search(query: str, directories: list[str] | None = None,
                  limit: int = 100, offset: int = 0) -> list[SearchResult]:
    """执行向量检索并丰富元数据。目录过滤下推到 ChromaDB 层。"""
    query_embedding = encode_query(query)
    chroma_results = vector_store.search_similar(
        query_embedding, directories=directories, limit=limit, offset=offset
    )

    if not chroma_results["ids"] or not chroma_results["ids"][0]:
        return []

    # 按 doc_id 去重（多个分块可能来自同一文档）
    seen_docs: dict[str, dict] = {}
    for i, chunk_id in enumerate(chroma_results["ids"][0]):
        meta = chroma_results["metadatas"][0][i]
        doc_id = meta.get("doc_id", "")
        distance = chroma_results["distances"][0][i]
        snippet = chroma_results["documents"][0][i]

        if doc_id not in seen_docs:
            seen_docs[doc_id] = {
                "distance": distance,
                "snippet": snippet[:200],
            }

    doc_ids = list(seen_docs.keys())
    docs = document_db.get_documents_by_ids(doc_ids)

    results = []
    for doc_id in doc_ids:
        doc = docs.get(doc_id)
        if doc is None:
            continue
        info = seen_docs[doc_id]
        results.append(SearchResult(
            doc_id=doc_id,
            file_path=doc.file_path,
            file_name=doc.file_name,
            title=doc.title,
            doc_number=doc.doc_number,
            doc_date=doc.doc_date,
            issuing_authority=doc.issuing_authority,
            doc_type=doc.doc_type,
            source_year=doc.source_year,
            score=1.0 - info["distance"],  # cosine distance → similarity
            snippet=info["snippet"],
            extracted_text=doc.extracted_text,
            match_type="vector",
        ))
    return results
