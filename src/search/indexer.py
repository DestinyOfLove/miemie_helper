"""增量索引编排器：扫描→变更检测→提取→索引。"""

import threading
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
        indexing_status.current_file = ""
        # is_running 必须在 phase 设置之后才清除，避免 UI 轮询竞态
        indexing_status.is_running = False


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

    # 规范化文本：去掉所有换行，拼成单行
    normalized_text = normalize_text_for_indexing(text) if text else text

    doc = DocumentRecord(
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

    # 存入 SQLite
    document_db.upsert_document(doc)

    # 存入 FTS5（使用规范化文本，提升分词和检索质量）
    fulltext_store.insert_fts_record(
        doc.id, doc.file_name, doc.title,
        doc.doc_number, doc.issuing_authority, normalized_text,
    )
    document_db.update_index_flags(doc.id, fts_indexed=True)

    # 存入 ChromaDB（向量，使用规范化文本）
    if text:
        metadata = {
            "file_name": doc.file_name,
            "title": doc.title,
            "doc_number": doc.doc_number,
            "source_year": doc.source_year,
        }
        chunks = vector_store.chunk_document(doc.id, normalized_text, metadata)
        if chunks:
            embeddings = encode_texts([c["text"] for c in chunks])
            vector_store.add_document_chunks(chunks, embeddings)
            document_db.update_index_flags(doc.id, vector_indexed=True)


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
