"""SQLite FTS5 全文检索：jieba 预分词 + unicode61 分词器。"""

import sqlite3

import jieba

from src.search.document_db import get_connection
from src.search.models import SearchResult

# 预加载 jieba 词典，避免首次分词时的延迟
jieba.initialize()

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
    """插入一条 FTS5 记录。元数据字段不分词，仅全文内容使用 jieba 分词。不自动 commit。"""
    _ensure_fts_table()
    conn = get_connection()
    conn.execute(
        """INSERT OR REPLACE INTO documents_fts
           (doc_id, file_name, title, doc_number, issuing_authority, content_segmented)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (doc_id, file_name, title, doc_number, issuing_authority,
         segment_text(full_text)),
    )


def batch_insert_fts_records(records: list[tuple]) -> None:
    """批量插入 FTS5 记录。不自动 commit。

    records 格式: [(doc_id, file_name, title, doc_number, issuing_authority, full_text), ...]
    仅对 full_text 做 jieba 分词，元数据字段直接使用原文。
    """
    _ensure_fts_table()
    conn = get_connection()
    conn.executemany(
        """INSERT OR REPLACE INTO documents_fts
           (doc_id, file_name, title, doc_number, issuing_authority, content_segmented)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [(doc_id, file_name, title, doc_number, issuing_authority, segment_text(full_text))
         for doc_id, file_name, title, doc_number, issuing_authority, full_text in records],
    )


def delete_fts_record(doc_id: str) -> None:
    """删除一条 FTS5 记录。不自动 commit。"""
    _ensure_fts_table()
    conn = get_connection()
    conn.execute(
        "DELETE FROM documents_fts WHERE doc_id = ?", (doc_id,)
    )


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


# FTS5 列名与搜索范围的映射
# 表结构：doc_id(UNINDEXED), file_name, title, doc_number, issuing_authority, content_segmented
_SCOPE_COLS = {
    "content": ["content_segmented"],
    "title":   ["title", "file_name"],
    "all":     ["file_name", "title", "doc_number", "issuing_authority", "content_segmented"],
}


def search_fulltext(query: str, scopes: list[str] | None = None,
                    directories: list[str] | None = None,
                    limit: int = 100, offset: int = 0) -> list[dict]:
    """全文检索。返回 [{doc_id, rank, snippet}, ...]。

    scopes: ["content"] | ["title"] | ["all"] 或任意组合，控制搜索范围。
    directories: 限制搜索的目录列表，None/空表示搜全部。
    limit: 限制返回结果数量。
    offset: 偏移量，用于分页。
    """
    _ensure_fts_table()
    segmented_query = segment_text(query)
    if not segmented_query.strip():
        return []

    # 汇总所有要搜索的列（去重）
    if scopes:
        cols: list[str] = []
        for s in scopes:
            cols.extend(_SCOPE_COLS.get(s, _SCOPE_COLS["content"]))
        cols = list(dict.fromkeys(cols))  # 保序去重
    else:
        cols = _SCOPE_COLS["content"]

    # FTS5 列限定语法：{col1 col2}: query
    col_expr = "{" + " ".join(cols) + "}"
    fts_query = f"{col_expr}: {segmented_query}"

    conn = get_connection()
    try:
        if directories:
            placeholders = ",".join("?" for _ in directories)
            cursor = conn.execute(
                f"""SELECT f.doc_id, f.rank,
                          snippet(documents_fts, 5, '<mark>', '</mark>', '...', 64) as snippet
                   FROM documents_fts f
                   JOIN documents d ON d.id = f.doc_id
                   WHERE documents_fts MATCH ?
                     AND d.directory_root IN ({placeholders})
                   ORDER BY f.rank
                   LIMIT ? OFFSET ?""",
                (fts_query, *directories, limit, offset),
            )
        else:
            cursor = conn.execute(
                """SELECT doc_id, rank,
                          snippet(documents_fts, 5, '<mark>', '</mark>', '...', 64) as snippet
                   FROM documents_fts
                   WHERE documents_fts MATCH ?
                   ORDER BY rank
                   LIMIT ? OFFSET ?""",
                (fts_query, limit, offset),
            )
        return [
            {"doc_id": row[0], "rank": row[1], "snippet": row[2]}
            for row in cursor
        ]
    except sqlite3.OperationalError:
        return []
