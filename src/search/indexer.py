"""增量索引编排器：扫描→变更检测→并行提取→批量索引。"""

import logging
import os
import threading
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from src.config import BATCH_COMMIT_SIZE, INDEXING_WORKERS
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

logger = logging.getLogger(__name__)


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


def _get_worker_count() -> int:
    """计算并行 worker 数量。"""
    if INDEXING_WORKERS > 0:
        return INDEXING_WORKERS
    return max(1, (os.cpu_count() or 4) - 2)


def _extract_single_file(file_path_str: str, root_str: str,
                          precomputed_hash: str | None = None) -> dict:
    """在独立进程中提取单个文件（纯 CPU 工作，无共享状态）。

    返回包含所有提取结果的字典。
    """
    file_path = Path(file_path_str)
    root = Path(root_str)

    try:
        stat = file_path.stat()
        file_hash = precomputed_hash or compute_file_hash(file_path)
        text, method = extract_text(file_path)
        year_hint = guess_year_from_path(file_path, root)

        if text:
            fields = parse_document_fields(text, file_path_str, year_hint)
        else:
            fields = {
                "发文字号": "", "发文标题": "", "发文日期": "",
                "发文机关": "", "主送单位": "", "公文种类": "",
                "密级": "", "来源年份": year_hint,
            }

        normalized_text = normalize_text_for_indexing(text) if text else text

        return {
            "success": True,
            "file_path": file_path_str,
            "file_name": file_path.name,
            "file_size": stat.st_size,
            "file_mtime": stat.st_mtime,
            "file_hash": file_hash,
            "text": text,
            "normalized_text": normalized_text,
            "method": method,
            "fields": fields,
        }
    except Exception as e:
        return {
            "success": False,
            "file_path": file_path_str,
            "file_name": Path(file_path_str).name,
            "error": str(e),
        }


def run_indexing(directory: str) -> None:
    """执行增量索引（同步，供后台线程调用）。

    流水线架构：
    1. 扫描文件系统 + 变更检测
    2. 并行文本提取（ProcessPoolExecutor）
    3. 批量写入 SQLite + FTS5（批量事务）
    4. 批量 Embedding + ChromaDB 写入
    """
    root = Path(directory).resolve()
    directory_str = str(root)

    indexing_status.reset(directory_str)
    document_db.upsert_directory(directory_str, status="scanning")

    try:
        # ── Phase 1: 扫描文件系统 ──
        indexing_status.phase = "scanning"
        all_files = scan_directory(root)
        indexing_status.total_files = len(all_files)

        # ── Phase 2: 加载已知文件 + 分类变更 ──
        known_files = document_db.get_known_files(directory_str)

        to_add: list[Path] = []
        to_update: list[tuple[Path, str, str]] = []  # (path, old_doc_id, new_hash)
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
                    to_update.append((file_path, known["id"], new_hash))
                else:
                    indexing_status.skipped += 1

        # 检测删除
        for path_str, info in known_files.items():
            if path_str not in current_paths:
                to_delete.append(info["id"])

        document_db.upsert_directory(
            directory_str, file_count=len(all_files), status="indexing"
        )

        # ── Phase 3: 处理删除 ──
        for doc_id in to_delete:
            _delete_document(doc_id)
            indexing_status.deleted += 1

        # ── Phase 4: 并行文本提取 ──
        indexing_status.phase = "extracting"

        # 准备提取任务：合并新增和更新
        extract_tasks: list[tuple[str, str | None, bool]] = []
        # (file_path_str, precomputed_hash_or_None, is_update)
        for fp in to_add:
            extract_tasks.append((str(fp), None, False))
        for fp, old_doc_id, new_hash in to_update:
            # 先删除旧记录
            _delete_document(old_doc_id)
            extract_tasks.append((str(fp), new_hash, True))

        extraction_results: list[dict] = []

        if extract_tasks:
            worker_count = min(_get_worker_count(), len(extract_tasks))
            root_str = str(root)

            if worker_count <= 1:
                # 单进程模式（调试或少量文件时避免多进程开销）
                for fp_str, pre_hash, _is_update in extract_tasks:
                    indexing_status.current_file = Path(fp_str).name
                    result = _extract_single_file(fp_str, root_str, pre_hash)
                    extraction_results.append(result)
                    indexing_status.processed_files += 1
            else:
                with ProcessPoolExecutor(max_workers=worker_count) as executor:
                    future_map = {
                        executor.submit(
                            _extract_single_file, fp_str, root_str, pre_hash
                        ): (fp_str, is_update)
                        for fp_str, pre_hash, is_update in extract_tasks
                    }
                    for future in as_completed(future_map):
                        result = future.result()
                        extraction_results.append(result)
                        indexing_status.current_file = result["file_name"]
                        indexing_status.processed_files += 1

        # ── Phase 5: 批量写入 SQLite + FTS5 ──
        indexing_status.phase = "indexing"

        successful_results: list[dict] = []
        for result in extraction_results:
            if not result["success"]:
                indexing_status.errors.append(
                    f"{result['file_name']}: {result['error']}"
                )
                continue
            successful_results.append(result)

        # 统计新增/更新
        update_paths = {str(fp) for fp, _, _ in to_update}
        for result in successful_results:
            if result["file_path"] in update_paths:
                indexing_status.updated += 1
            else:
                indexing_status.added += 1

        # 分批写入
        all_chunks: list[dict] = []
        all_doc_ids_for_vector: list[str] = []

        for batch_start in range(0, len(successful_results), BATCH_COMMIT_SIZE):
            batch = successful_results[batch_start:batch_start + BATCH_COMMIT_SIZE]

            document_db.begin_batch()
            try:
                fts_records: list[tuple] = []

                for result in batch:
                    fields = result["fields"]
                    normalized_text = result["normalized_text"]

                    doc = DocumentRecord(
                        id=result["file_hash"],
                        file_path=result["file_path"],
                        file_name=result["file_name"],
                        file_size=result["file_size"],
                        file_mtime=result["file_mtime"],
                        file_hash=result["file_hash"],
                        directory_root=directory_str,
                        extracted_text=normalized_text or "",
                        extraction_method=result["method"],
                        doc_number=fields["发文字号"],
                        title=fields["发文标题"],
                        doc_date=fields["发文日期"],
                        issuing_authority=fields["发文机关"],
                        recipients=fields["主送单位"],
                        doc_type=fields["公文种类"],
                        classification=fields["密级"],
                        source_year=fields["来源年份"],
                    )

                    # 写入 SQLite
                    document_db.upsert_document(doc)

                    # 收集 FTS5 记录
                    fts_records.append((
                        doc.id, doc.file_name, doc.title,
                        doc.doc_number, doc.issuing_authority,
                        normalized_text or "",
                    ))

                    # 标记 FTS 已索引
                    document_db.update_index_flags(doc.id, fts_indexed=True)

                    # 收集向量分块
                    if result["text"]:
                        metadata = {
                            "file_name": doc.file_name,
                            "title": doc.title,
                            "doc_number": doc.doc_number,
                            "source_year": doc.source_year,
                            "directory_root": directory_str,
                        }
                        chunks = vector_store.chunk_document(
                            doc.id, normalized_text or "", metadata
                        )
                        if chunks:
                            all_chunks.extend(chunks)
                            all_doc_ids_for_vector.append(doc.id)

                # 批量写入 FTS5
                fulltext_store.batch_insert_fts_records(fts_records)

                document_db.commit_batch()
            except Exception:
                document_db.rollback_batch()
                raise

        # ── Phase 6: 批量 Embedding + ChromaDB 写入 ──
        if all_chunks:
            indexing_status.phase = "embedding"
            all_texts = [c["text"] for c in all_chunks]
            embeddings = encode_texts(all_texts, batch_size=64)
            vector_store.batch_add_document_chunks(all_chunks, embeddings)

            # 标记向量索引完成
            document_db.begin_batch()
            try:
                for doc_id in set(all_doc_ids_for_vector):
                    document_db.update_index_flags(doc_id, vector_indexed=True)
                    document_db.mark_processing(doc_id, "indexed")
                document_db.commit_batch()
            except Exception:
                document_db.rollback_batch()
                raise

        # 将没有向量索引的文档也标记为 indexed
        document_db.begin_batch()
        try:
            vector_doc_ids = set(all_doc_ids_for_vector)
            for result in successful_results:
                if result["file_hash"] not in vector_doc_ids:
                    document_db.mark_processing(result["file_hash"], "indexed")
            document_db.commit_batch()
        except Exception:
            document_db.rollback_batch()
            raise

        # ── 完成 ──
        indexed_count = len(all_files) - len(indexing_status.errors)
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


def rebuild_directory(directory: str) -> None:
    """删除目录全部索引后重新全量索引（同步，供后台线程调用）。"""
    root = Path(directory).resolve()
    directory_str = str(root)

    # 先清除该目录的所有索引数据
    docs = document_db.get_documents_by_directory(directory_str)
    for doc in docs:
        _delete_document(doc.id)
    # 保留目录记录（含 starred 等元信息），重置计数
    document_db.upsert_directory(directory_str, file_count=0, indexed_count=0, status="rebuilding")

    # 复用 run_indexing 做全量索引
    run_indexing(directory_str)


def start_indexing_background(directory: str) -> bool:
    """在后台线程启动索引。返回是否成功启动。"""
    if indexing_status.is_running:
        return False
    thread = threading.Thread(target=run_indexing, args=(directory,), daemon=True)
    thread.start()
    return True


def start_rebuild_background(directory: str) -> bool:
    """在后台线程启动重建索引。返回是否成功启动。"""
    if indexing_status.is_running:
        return False
    thread = threading.Thread(target=rebuild_directory, args=(directory,), daemon=True)
    thread.start()
    return True
