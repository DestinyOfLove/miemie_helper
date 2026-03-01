"""增量索引编排器：扫描→变更检测→多线程提取→索引。"""

import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from src.core.extractor import compute_file_hash, extract_text
from src.core.file_scanner import guess_year_from_path, scan_directory
from src.core.parser import parse_document_fields
from src.core.text_utils import normalize_text_for_indexing
from src.search import document_db, fulltext_store, vector_store
from src.search.embedding import encode_texts
from src.search.models import (
    DirectoryScanResult,
    DocumentRecord,
    FileChange,
    IndexStatusResponse,
)

# 线程池大小：CPU 核心数，但不超过 8（避免内存压力过大，OCR 比较吃内存）
_MAX_WORKERS = min(os.cpu_count() or 4, 8)


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

        # Phase 5: 先删除待更新文件的旧记录
        for _, old_doc_id in to_update:
            _delete_document(old_doc_id)

        # Phase 6: 多线程提取+解析，再批量存储
        all_to_index: list[tuple[Path, str]] = (
            [(p, "add") for p in to_add]
            + [(p, "update") for p, _ in to_update]
        )

        if all_to_index:
            _index_files_parallel(all_to_index, root, directory_str)

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
        indexing_status.current_file = ""
        # is_running 必须在 phase 设置之后才清除，避免 UI 轮询竞态
        indexing_status.is_running = False


def _extract_and_parse(file_path: Path, root: Path, directory_str: str) -> DocumentRecord | None:
    """提取文本并解析字段（CPU 密集，适合并行）。返回 DocumentRecord 或 None。"""
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

    # 规范化文本：去掉所有换行，拼成单行
    normalized_text = normalize_text_for_indexing(text) if text else text

    return DocumentRecord(
        id=file_hash,
        file_path=str(file_path),
        file_name=file_path.name,
        file_size=stat.st_size,
        file_mtime=stat.st_mtime,
        file_hash=file_hash,
        directory_root=directory_str,
        extracted_text=normalized_text,
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


def _index_files_parallel(
    files: list[tuple[Path, str]],
    root: Path,
    directory_str: str,
) -> None:
    """多线程提取+解析文件，按批次存入数据库。

    流水线设计：
      1. ThreadPoolExecutor 并行执行 CPU 密集的文本提取+解析
      2. 主线程收集结果，每攒够一批就写入存储（SQLite + FTS5 + ChromaDB）
    """
    STORE_BATCH_SIZE = 20  # 每攒够 N 个结果就批量存储一次

    pending_docs: list[tuple[DocumentRecord, str]] = []  # (doc, change_type)

    def _flush_batch(batch: list[tuple[DocumentRecord, str]]) -> None:
        """将一批提取结果写入所有存储层。"""
        for doc, change_type in batch:
            # SQLite
            document_db.upsert_document(doc)

            # FTS5
            fulltext_store.insert_fts_record(
                doc.id, doc.file_name, doc.title,
                doc.doc_number, doc.issuing_authority, doc.extracted_text,
            )
            document_db.update_index_flags(doc.id, fts_indexed=True)

        # ChromaDB + Embedding 按批次处理（减少模型调用开销）
        chunks_all: list[dict] = []
        doc_ids_with_vectors: list[str] = []
        for doc, _ in batch:
            if doc.extracted_text:
                metadata = {
                    "file_name": doc.file_name,
                    "title": doc.title,
                    "doc_number": doc.doc_number,
                    "source_year": doc.source_year,
                }
                chunks = vector_store.chunk_document(doc.id, doc.extracted_text, metadata)
                if chunks:
                    chunks_all.extend(chunks)
                    doc_ids_with_vectors.append(doc.id)

        if chunks_all:
            embeddings = encode_texts([c["text"] for c in chunks_all])
            vector_store.add_document_chunks(chunks_all, embeddings)
            for doc_id in doc_ids_with_vectors:
                document_db.update_index_flags(doc_id, vector_indexed=True)

    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
        future_map = {}
        for file_path, change_type in files:
            future = executor.submit(_extract_and_parse, file_path, root, directory_str)
            future_map[future] = (file_path, change_type)

        for future in as_completed(future_map):
            file_path, change_type = future_map[future]
            indexing_status.current_file = file_path.name

            try:
                doc = future.result()
                if doc is not None:
                    pending_docs.append((doc, change_type))
                    if change_type == "add":
                        indexing_status.added += 1
                    else:
                        indexing_status.updated += 1
                else:
                    indexing_status.errors.append(f"{file_path.name}: 提取失败")
            except Exception as e:
                indexing_status.errors.append(f"{file_path.name}: {e}")

            indexing_status.processed_files += 1

            # 攒够一批就写入存储
            if len(pending_docs) >= STORE_BATCH_SIZE:
                _flush_batch(pending_docs)
                pending_docs.clear()

    # 处理最后不足一批的剩余
    if pending_docs:
        _flush_batch(pending_docs)
        pending_docs.clear()


def _delete_document(doc_id: str) -> None:
    """从所有存储中删除文档。"""
    fulltext_store.delete_fts_record(doc_id)
    vector_store.delete_document_chunks(doc_id)
    document_db.delete_document(doc_id)


def scan_directory_changes(directory: str) -> DirectoryScanResult:
    """轻量扫描目录变更（仅文件系统元数据 + MD5，不做文本提取）。"""
    root = Path(directory).resolve()
    directory_str = str(root)

    try:
        all_files = scan_directory(root)
    except Exception as e:
        return DirectoryScanResult(directory_path=directory_str, error=str(e))

    known_files = document_db.get_known_files(directory_str)
    current_paths: set[str] = set()

    new_files: list[tuple[Path, str]] = []  # (path, md5)
    deleted_files: list[tuple[str, str]] = []  # (path, md5)
    modified_files: list[Path] = []
    unchanged_count = 0

    for file_path in all_files:
        path_str = str(file_path)
        current_paths.add(path_str)

        if path_str not in known_files:
            md5 = compute_file_hash(file_path)
            new_files.append((file_path, md5))
        else:
            known = known_files[path_str]
            stat = file_path.stat()
            if stat.st_mtime == known["file_mtime"] and stat.st_size == known["file_size"]:
                unchanged_count += 1
                continue
            new_hash = compute_file_hash(file_path)
            if new_hash != known["file_hash"]:
                modified_files.append(file_path)
            else:
                unchanged_count += 1

    for path_str, info in known_files.items():
        if path_str not in current_paths:
            deleted_files.append((path_str, info["file_hash"]))

    # 重命名检测：新文件的 MD5 匹配到某个已删除文件的 MD5
    deleted_by_hash: dict[str, str] = {md5: path for path, md5 in deleted_files}
    changes: list[FileChange] = []
    renamed_count = 0
    actual_new: list[tuple[Path, str]] = []

    for file_path, md5 in new_files:
        if md5 in deleted_by_hash:
            old_path = deleted_by_hash.pop(md5)
            changes.append(FileChange(
                file_path=str(file_path),
                file_name=file_path.name,
                change_type="renamed",
                old_path=old_path,
            ))
            renamed_count += 1
        else:
            actual_new.append((file_path, md5))

    for file_path, _ in actual_new:
        changes.append(FileChange(
            file_path=str(file_path), file_name=file_path.name, change_type="new",
        ))

    for path_str in deleted_by_hash.values():
        changes.append(FileChange(
            file_path=path_str, file_name=Path(path_str).name, change_type="deleted",
        ))

    for file_path in modified_files:
        changes.append(FileChange(
            file_path=str(file_path), file_name=file_path.name, change_type="modified",
        ))

    return DirectoryScanResult(
        directory_path=directory_str,
        new_count=len(actual_new),
        deleted_count=len(deleted_by_hash),
        renamed_count=renamed_count,
        modified_count=len(modified_files),
        unchanged_count=unchanged_count,
        total_on_disk=len(all_files),
        changes=changes,
    )


def start_indexing_background(directory: str) -> bool:
    """在后台线程启动索引。返回是否成功启动。"""
    if indexing_status.is_running:
        return False
    thread = threading.Thread(target=run_indexing, args=(directory,), daemon=True)
    thread.start()
    return True
