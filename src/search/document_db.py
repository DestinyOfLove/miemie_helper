"""SQLite 文档数据库：元数据存储 + 索引目录管理。"""

import sqlite3
from pathlib import Path

from src.config import DB_PATH, ensure_dirs
from src.search.models import DirectoryInfo, DocumentRecord

_conn: sqlite3.Connection | None = None
_in_batch: bool = False


def get_connection() -> sqlite3.Connection:
    """获取 SQLite 连接（单例，WAL 模式）。"""
    global _conn
    if _conn is None:
        ensure_dirs()
        _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA foreign_keys=ON")
        _conn.execute("PRAGMA busy_timeout=5000")
        _init_schema(_conn)
    return _conn


def _init_schema(conn: sqlite3.Connection) -> None:
    """初始化数据库表结构。"""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            file_path TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            file_mtime REAL NOT NULL,
            file_hash TEXT NOT NULL,
            directory_root TEXT NOT NULL,
            extracted_text TEXT NOT NULL DEFAULT '',
            extraction_method TEXT NOT NULL DEFAULT '',
            doc_number TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            doc_date TEXT NOT NULL DEFAULT '',
            issuing_authority TEXT NOT NULL DEFAULT '',
            recipients TEXT NOT NULL DEFAULT '',
            doc_type TEXT NOT NULL DEFAULT '',
            classification TEXT NOT NULL DEFAULT '',
            source_year TEXT NOT NULL DEFAULT '',
            indexed_at TEXT NOT NULL DEFAULT (datetime('now')),
            vector_indexed INTEGER NOT NULL DEFAULT 0,
            fts_indexed INTEGER NOT NULL DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_documents_file_path
            ON documents(file_path);
        CREATE INDEX IF NOT EXISTS idx_documents_directory_root
            ON documents(directory_root);
        CREATE INDEX IF NOT EXISTS idx_documents_processing_status
            ON documents(processing_status);
        CREATE INDEX IF NOT EXISTS idx_documents_file_hash
            ON documents(file_hash);
        CREATE INDEX IF NOT EXISTS idx_documents_mtime
            ON documents(file_mtime);

        CREATE TABLE IF NOT EXISTS indexed_directories (
            directory_path TEXT PRIMARY KEY,
            last_scan_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            file_count INTEGER NOT NULL DEFAULT 0,
            indexed_count INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'idle',
            starred INTEGER NOT NULL DEFAULT 0
        );

        -- 启动时清理上次崩溃残留的中间状态
        UPDATE indexed_directories
            SET status = 'incomplete'
            WHERE status IN ('scanning', 'indexing', 'rebuilding');
    """)
    conn.commit()

    # 增量迁移：添加可恢复索引所需的列
    for col_name, col_type in [
        ("processing_status", "TEXT NOT NULL DEFAULT 'indexed'"),
        ("error_message", "TEXT NOT NULL DEFAULT ''"),
        ("retry_count", "INTEGER NOT NULL DEFAULT 0"),
    ]:
        try:
            conn.execute(f"ALTER TABLE documents ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass  # 列已存在

    # 启动时将 extracting 状态的文档重置为 pending（上次崩溃残留）
    conn.execute(
        "UPDATE documents SET processing_status = 'pending' "
        "WHERE processing_status = 'extracting'"
    )
    conn.commit()


# ── 批量事务控制 ──

def begin_batch() -> None:
    """开启批量事务。在批量模式下，写入方法不自动 commit。"""
    global _in_batch
    conn = get_connection()
    conn.execute("BEGIN")
    _in_batch = True


def commit_batch() -> None:
    """提交批量事务。"""
    global _in_batch
    conn = get_connection()
    conn.commit()
    _in_batch = False


def rollback_batch() -> None:
    """回滚批量事务。"""
    global _in_batch
    conn = get_connection()
    conn.rollback()
    _in_batch = False


# ── 文档 CRUD ──

def upsert_document(doc: DocumentRecord) -> None:
    """插入或更新文档记录。"""
    conn = get_connection()
    conn.execute(
        """INSERT OR REPLACE INTO documents
           (id, file_path, file_name, file_size, file_mtime, file_hash,
            directory_root, extracted_text, extraction_method,
            doc_number, title, doc_date, issuing_authority, recipients,
            doc_type, classification, source_year,
            indexed_at, vector_indexed, fts_indexed, processing_status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                   datetime('now'), ?, ?, 'extracting')""",
        (doc.id, doc.file_path, doc.file_name, doc.file_size, doc.file_mtime,
         doc.file_hash, doc.directory_root, doc.extracted_text,
         doc.extraction_method, doc.doc_number, doc.title, doc.doc_date,
         doc.issuing_authority, doc.recipients, doc.doc_type,
         doc.classification, doc.source_year,
         int(doc.vector_indexed), int(doc.fts_indexed)),
    )
    if not _in_batch:
        conn.commit()


def get_document(doc_id: str) -> DocumentRecord | None:
    """按 ID 获取文档记录。"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if row is None:
        return None
    return _row_to_document(row)


def get_documents_by_ids(doc_ids: list[str]) -> dict[str, DocumentRecord]:
    """批量获取文档记录。"""
    if not doc_ids:
        return {}
    conn = get_connection()
    placeholders = ",".join("?" for _ in doc_ids)
    rows = conn.execute(
        f"SELECT * FROM documents WHERE id IN ({placeholders})", doc_ids
    ).fetchall()
    return {row["id"]: _row_to_document(row) for row in rows}


def get_documents_by_directory(directory_root: str) -> list[DocumentRecord]:
    """获取某目录下所有文档记录。"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM documents WHERE directory_root = ?", (directory_root,)
    ).fetchall()
    return [_row_to_document(row) for row in rows]


def get_known_files(directory_root: str) -> dict[str, dict]:
    """获取目录下已知文件的快速查找表。返回 {file_path: {id, mtime, size, hash}}。"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, file_path, file_mtime, file_size, file_hash "
        "FROM documents WHERE directory_root = ?",
        (directory_root,),
    ).fetchall()
    return {
        row["file_path"]: {
            "id": row["id"],
            "file_mtime": row["file_mtime"],
            "file_size": row["file_size"],
            "file_hash": row["file_hash"],
        }
        for row in rows
    }


def delete_document(doc_id: str) -> None:
    """删除文档记录。"""
    conn = get_connection()
    conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    if not _in_batch:
        conn.commit()


def delete_documents_by_directory(directory_root: str) -> int:
    """删除某目录下所有文档记录，返回删除数量。"""
    conn = get_connection()
    cursor = conn.execute(
        "DELETE FROM documents WHERE directory_root = ?", (directory_root,)
    )
    conn.commit()
    return cursor.rowcount


def get_all_documents() -> list[DocumentRecord]:
    """获取所有文档记录。"""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM documents").fetchall()
    return [_row_to_document(row) for row in rows]


def update_index_flags(doc_id: str, vector_indexed: bool | None = None,
                       fts_indexed: bool | None = None) -> None:
    """更新文档的索引标志。"""
    conn = get_connection()
    updates = []
    params = []
    if vector_indexed is not None:
        updates.append("vector_indexed = ?")
        params.append(int(vector_indexed))
    if fts_indexed is not None:
        updates.append("fts_indexed = ?")
        params.append(int(fts_indexed))
    if not updates:
        return
    params.append(doc_id)
    conn.execute(
        f"UPDATE documents SET {', '.join(updates)} WHERE id = ?", params
    )
    if not _in_batch:
        conn.commit()


def mark_processing(doc_id: str, status: str,
                    error_message: str | None = None) -> None:
    """更新文档的处理状态。"""
    conn = get_connection()
    if error_message is not None:
        conn.execute(
            "UPDATE documents SET processing_status = ?, error_message = ?, "
            "retry_count = retry_count + 1 WHERE id = ?",
            (status, error_message, doc_id),
        )
    else:
        conn.execute(
            "UPDATE documents SET processing_status = ? WHERE id = ?",
            (status, doc_id),
        )
    if not _in_batch:
        conn.commit()


def get_resumable_files(directory_root: str, max_retries: int = 3) -> list[dict]:
    """获取需要恢复处理的文件（pending 或 extracting 状态，retry_count < max_retries）。"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, file_path, file_hash FROM documents "
        "WHERE directory_root = ? AND processing_status IN ('pending', 'extracting') "
        "AND retry_count < ?",
        (directory_root, max_retries),
    ).fetchall()
    return [
        {"id": row["id"], "file_path": row["file_path"], "file_hash": row["file_hash"]}
        for row in rows
    ]


# ── 索引目录管理 ──

def upsert_directory(directory_path: str, file_count: int = 0,
                     indexed_count: int = 0, status: str = "idle") -> None:
    """插入或更新索引目录记录（保留 starred 值）。"""
    conn = get_connection()
    conn.execute(
        """INSERT INTO indexed_directories
           (directory_path, last_scan_at, file_count, indexed_count, status)
           VALUES (?, datetime('now', 'localtime'), ?, ?, ?)
           ON CONFLICT(directory_path) DO UPDATE SET
               last_scan_at = datetime('now', 'localtime'),
               file_count = excluded.file_count,
               indexed_count = excluded.indexed_count,
               status = excluded.status""",
        (directory_path, file_count, indexed_count, status),
    )
    conn.commit()


def update_directory_status(directory_path: str, status: str,
                            indexed_count: int | None = None) -> None:
    """更新目录索引状态。"""
    conn = get_connection()
    if indexed_count is not None:
        conn.execute(
            "UPDATE indexed_directories SET status = ?, indexed_count = ?, "
            "last_scan_at = datetime('now', 'localtime') WHERE directory_path = ?",
            (status, indexed_count, directory_path),
        )
    else:
        conn.execute(
            "UPDATE indexed_directories SET status = ?, "
            "last_scan_at = datetime('now', 'localtime') WHERE directory_path = ?",
            (status, directory_path),
        )
    conn.commit()


def get_all_directories() -> list[DirectoryInfo]:
    """获取所有已索引目录信息。indexed_count 实时从 documents 表统计。"""
    conn = get_connection()
    rows = conn.execute("""
        SELECT d.*,
               COALESCE(c.cnt, 0) AS real_indexed_count
        FROM indexed_directories d
        LEFT JOIN (
            SELECT directory_root, COUNT(*) AS cnt
            FROM documents
            GROUP BY directory_root
        ) c ON c.directory_root = d.directory_path
    """).fetchall()
    return [
        DirectoryInfo(
            directory_path=row["directory_path"],
            file_count=row["file_count"],
            indexed_count=row["real_indexed_count"],
            last_scan_at=row["last_scan_at"],
            status=row["status"],
            starred=bool(row["starred"]),
        )
        for row in rows
    ]


def toggle_directory_starred(directory_path: str) -> bool:
    """切换目录星标状态，返回新状态。"""
    conn = get_connection()
    conn.execute(
        "UPDATE indexed_directories SET starred = 1 - starred WHERE directory_path = ?",
        (directory_path,),
    )
    conn.commit()
    row = conn.execute(
        "SELECT starred FROM indexed_directories WHERE directory_path = ?",
        (directory_path,),
    ).fetchone()
    return bool(row["starred"]) if row else False


def delete_directory(directory_path: str) -> None:
    """删除索引目录记录。"""
    conn = get_connection()
    conn.execute("DELETE FROM indexed_directories WHERE directory_path = ?",
                 (directory_path,))
    conn.commit()


# ── 内部工具 ──

def _row_to_document(row: sqlite3.Row) -> DocumentRecord:
    """将 SQLite Row 转为 DocumentRecord。"""
    return DocumentRecord(
        id=row["id"],
        file_path=row["file_path"],
        file_name=row["file_name"],
        file_size=row["file_size"],
        file_mtime=row["file_mtime"],
        file_hash=row["file_hash"],
        directory_root=row["directory_root"],
        extracted_text=row["extracted_text"],
        extraction_method=row["extraction_method"],
        doc_number=row["doc_number"],
        title=row["title"],
        doc_date=row["doc_date"],
        issuing_authority=row["issuing_authority"],
        recipients=row["recipients"],
        doc_type=row["doc_type"],
        classification=row["classification"],
        source_year=row["source_year"],
        indexed_at=row["indexed_at"],
        vector_indexed=bool(row["vector_indexed"]),
        fts_indexed=bool(row["fts_indexed"]),
        processing_status=row["processing_status"],
        error_message=row["error_message"],
        retry_count=row["retry_count"],
    )
