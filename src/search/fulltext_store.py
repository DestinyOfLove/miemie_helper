"""SQLite FTS5 全文检索：jieba 预分词 + unicode61 分词器。"""

import sqlite3

import jieba

from src.search.document_db import get_connection
from src.search.models import SearchResult


_fts_initialized = False


def _ensure_fts_table() -> None:
    """确保 FTS5 虚拟表存在。"""
    global _fts_initialized
    if _fts_initialized:
        return
    conn = get_connection()
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
            doc_id UNINDEXED,
            file_name,
            title,
            doc_number,
            issuing_authority,
            content_segmented,
            tokenize='unicode61'
        )
    """)
    conn.commit()
    _fts_initialized = True


def segment_text(text: str) -> str:
    """用 jieba 分词，返回空格分隔的 token 串。"""
    words = jieba.cut(text, cut_all=False)
    return " ".join(w.strip() for w in words if w.strip())


def insert_fts_record(doc_id: str, file_name: str, title: str,
                      doc_number: str, issuing_authority: str,
                      full_text: str) -> None:
    """插入一条 FTS5 记录。"""
    _ensure_fts_table()
    conn = get_connection()
    conn.execute(
        """INSERT OR REPLACE INTO documents_fts
           (doc_id, file_name, title, doc_number, issuing_authority, content_segmented)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (doc_id, segment_text(file_name), segment_text(title),
         segment_text(doc_number), segment_text(issuing_authority),
         segment_text(full_text)),
    )
    conn.commit()


def delete_fts_record(doc_id: str) -> None:
    """删除一条 FTS5 记录。"""
    _ensure_fts_table()
    conn = get_connection()
    conn.execute(
        "DELETE FROM documents_fts WHERE doc_id = ?", (doc_id,)
    )
    conn.commit()


def delete_fts_by_directory(doc_ids: list[str]) -> None:
    """批量删除 FTS5 记录。"""
    if not doc_ids:
        return
    _ensure_fts_table()
    conn = get_connection()
    placeholders = ",".join("?" for _ in doc_ids)
    conn.execute(
        f"DELETE FROM documents_fts WHERE doc_id IN ({placeholders})", doc_ids
    )
    conn.commit()


def search_fulltext(query: str, limit: int = 20) -> list[dict]:
    """全文检索。返回 [{doc_id, rank, snippet}, ...]。"""
    _ensure_fts_table()
    segmented_query = segment_text(query)
    if not segmented_query.strip():
        return []

    conn = get_connection()
    try:
        cursor = conn.execute(
            """SELECT doc_id, rank,
                      snippet(documents_fts, 5, '<mark>', '</mark>', '...', 40) as snippet
               FROM documents_fts
               WHERE documents_fts MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (segmented_query, limit),
        )
        return [
            {"doc_id": row[0], "rank": row[1], "snippet": row[2]}
            for row in cursor
        ]
    except sqlite3.OperationalError:
        # MATCH 语法错误时返回空
        return []
