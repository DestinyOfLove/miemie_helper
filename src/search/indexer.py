"""增量索引编排器：扫描→变更检测→提取→索引。"""

import threading
import time
from pathlib import Path

from src.core.extractor import compute_file_hash, extract_text
from src.core.file_scanner import guess_year_from_path, scan_directory
from src.core.parser import parse_document_fields
from src.search import document_db, fulltext_store, vector_store
from src.search.embedding import encode_texts
from src.search.models import DocumentRecord, IndexStatusResponse


class IndexingStatus:
    """线程安全的索引状态容器。"""

    def __init__(self):
        self._lock = threading.Lock()
        self.is_running: bool = False
        self.phase: str = "idle"
        self.directory: str = ""
        self.total_files: int = 0
        self.processed_files: int = 0
        self.added: int = 0
        self.updated: int = 0
        self.deleted: int = 0
        self.skipped: int = 0
        self.current_file: str = ""
        self.errors: list[str] = []

    def reset(self, directory: str) -> None:
        with self._lock:
            self.is_running = True
            self.phase = "scanning"
            self.directory = directory
            self.total_files = 0
            self.processed_files = 0
            self.added = 0
            self.updated = 0
            self.deleted = 0
            self.skipped = 0
            self.current_file = ""
            self.errors = []

    def to_response(self) -> IndexStatusResponse:
        with self._lock:
            return IndexStatusResponse(
                is_running=self.is_running,
                phase=self.phase,
                directory=self.directory,
                total_files=self.total_files,
                processed_files=self.processed_files,
                added=self.added,
                updated=self.updated,
                deleted=self.deleted,
                skipped=self.skipped,
                current_file=self.current_file,
                errors=list(self.errors),
            )


# 全局索引状态
indexing_status = IndexingStatus()


def run_indexing(directory: str) -> None:
    """执行增量索引（同步，供后台线程调用）。"""
    root = Path(directory).resolve()
    directory_str = str(root)

    indexing_status.reset(directory_str)
    document_db.upsert_directory(directory_str, status="scanning")

    try:
        # Phase 1: 扫描文件系统
        indexing_status.phase = "scanning"
        all_files = scan_directory(root)
        indexing_status.total_files = len(all_files)

        # Phase 2: 加载已知文件
        known_files = document_db.get_known_files(directory_str)

        # Phase 3: 分类变更
        to_add: list[Path] = []
        to_update: list[tuple[Path, str]] = []  # (path, old_doc_id)
        to_delete: list[str] = []  # doc_ids

        current_paths: set[str] = set()

        for file_path in all_files:
            path_str = str(file_path)
            current_paths.add(path_str)

            if path_str not in known_files:
                to_add.append(file_path)
            else:
                known = known_files[path_str]
                stat = file_path.stat()
                # 快速预过滤：mtime + size 一致则跳过
                if stat.st_mtime == known["file_mtime"] and stat.st_size == known["file_size"]:
                    indexing_status.skipped += 1
                    continue
                # MD5 确认
                new_hash = compute_file_hash(file_path)
                if new_hash != known["file_hash"]:
                    to_update.append((file_path, known["id"]))
                else:
                    indexing_status.skipped += 1

        # 检测删除
        for path_str, info in known_files.items():
            if path_str not in current_paths:
                to_delete.append(info["id"])

        document_db.upsert_directory(
            directory_str, file_count=len(all_files), status="indexing"
        )

        # Phase 4: 处理删除
        indexing_status.phase = "indexing"
        for doc_id in to_delete:
            _delete_document(doc_id)
            indexing_status.deleted += 1

        # Phase 5: 处理新增和更新
        total_to_process = len(to_add) + len(to_update)

        for file_path in to_add:
            indexing_status.current_file = file_path.name
            try:
                _index_file(file_path, root, directory_str)
                indexing_status.added += 1
            except Exception as e:
                indexing_status.errors.append(f"{file_path.name}: {e}")
            indexing_status.processed_files += 1

        for file_path, old_doc_id in to_update:
            indexing_status.current_file = file_path.name
            try:
                _delete_document(old_doc_id)
                _index_file(file_path, root, directory_str)
                indexing_status.updated += 1
            except Exception as e:
                indexing_status.errors.append(f"{file_path.name}: {e}")
            indexing_status.processed_files += 1

        # 完成
        indexed_count = (
            len(all_files) - len(indexing_status.errors)
        )
        document_db.update_directory_status(
            directory_str, status="complete", indexed_count=indexed_count
        )
        indexing_status.phase = "complete"

    except Exception as e:
        indexing_status.phase = "error"
        indexing_status.errors.append(f"索引失败: {e}")
        document_db.update_directory_status(directory_str, status="error")

    finally:
        indexing_status.is_running = False
        indexing_status.current_file = ""


def _index_file(file_path: Path, root: Path, directory_str: str) -> None:
    """索引单个文件：提取→解析→存入 SQLite + FTS5 + ChromaDB。"""
    stat = file_path.stat()
    file_hash = compute_file_hash(file_path)
    text, method = extract_text(file_path)
    year_hint = guess_year_from_path(file_path, root)

    if text:
        fields = parse_document_fields(text, str(file_path), year_hint)
    else:
        fields = {
            "发文字号": "", "发文标题": "", "发文日期": "",
            "发文机关": "", "主送单位": "", "公文种类": "",
            "密级": "", "来源年份": year_hint,
        }

    doc = DocumentRecord(
        id=file_hash,
        file_path=str(file_path),
        file_name=file_path.name,
        file_size=stat.st_size,
        file_mtime=stat.st_mtime,
        file_hash=file_hash,
        directory_root=directory_str,
        extracted_text=text,
        extraction_method=method,
        doc_number=fields["发文字号"],
        title=fields["发文标题"],
        doc_date=fields["发文日期"],
        issuing_authority=fields["发文机关"],
        recipients=fields["主送单位"],
        doc_type=fields["公文种类"],
        classification=fields["密级"],
        source_year=fields["来源年份"],
    )

    # 存入 SQLite
    document_db.upsert_document(doc)

    # 存入 FTS5
    fulltext_store.insert_fts_record(
        doc.id, doc.file_name, doc.title,
        doc.doc_number, doc.issuing_authority, text,
    )
    document_db.update_index_flags(doc.id, fts_indexed=True)

    # 存入 ChromaDB（向量）
    if text:
        metadata = {
            "file_name": doc.file_name,
            "title": doc.title,
            "doc_number": doc.doc_number,
            "source_year": doc.source_year,
        }
        chunks = vector_store.chunk_document(doc.id, text, metadata)
        if chunks:
            embeddings = encode_texts([c["text"] for c in chunks])
            vector_store.add_document_chunks(chunks, embeddings)
            document_db.update_index_flags(doc.id, vector_indexed=True)


def _delete_document(doc_id: str) -> None:
    """从所有存储中删除文档。"""
    fulltext_store.delete_fts_record(doc_id)
    vector_store.delete_document_chunks(doc_id)
    document_db.delete_document(doc_id)


def start_indexing_background(directory: str) -> bool:
    """在后台线程启动索引。返回是否成功启动。"""
    if indexing_status.is_running:
        return False
    thread = threading.Thread(target=run_indexing, args=(directory,), daemon=True)
    thread.start()
    return True
