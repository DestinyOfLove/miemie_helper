"""归档处理 API 路由：后台扫描 + OCR + 导出 Excel。"""

import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.config import ALL_EXTENSIONS
from src.core.excel_exporter import EMPTY_FIELDS, export_records_to_excel, split_text_to_columns
from src.core.extractor import compute_file_hash, extract_text
from src.core.file_scanner import guess_year_from_path, scan_directory
from src.core.parser import parse_document_fields

router = APIRouter(prefix="/api/archive", tags=["archive"])


@dataclass
class ArchiveState:
    is_running: bool = False
    phase: str = "idle"
    directory: str = ""
    total_files: int = 0
    processed_files: int = 0
    errors: list[str] = field(default_factory=list)
    output_path: str = ""
    log_lines: list[str] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def reset(self, directory: str) -> None:
        with self._lock:
            self.is_running = True
            self.phase = "scanning"
            self.directory = directory
            self.total_files = 0
            self.processed_files = 0
            self.errors = []
            self.output_path = ""
            self.log_lines = []

    def log(self, msg: str) -> None:
        with self._lock:
            self.log_lines.append(msg)

    def to_dict(self) -> dict:
        with self._lock:
            return {
                "is_running": self.is_running,
                "phase": self.phase,
                "directory": self.directory,
                "total_files": self.total_files,
                "processed_files": self.processed_files,
                "errors": list(self.errors),
                "output_path": self.output_path,
                "log_lines": list(self.log_lines),
            }


_state = ArchiveState()


class ArchiveRequest(BaseModel):
    directory: str


def _run_archive(directory: str) -> None:
    root = Path(directory)
    _state.log(f"扫描目录: {directory}")

    files = scan_directory(root)
    if not files:
        _state.log(f"未找到支持的文件格式（{', '.join(sorted(ALL_EXTENSIONS))}）")
        with _state._lock:
            _state.phase = "complete"
            _state.is_running = False
        return

    with _state._lock:
        _state.total_files = len(files)
        _state.phase = "processing"
    _state.log(f"找到 {len(files)} 个文件，开始处理...")

    records = []
    for i, fp in enumerate(files, 1):
        _state.log(f"[{i}/{len(files)}] {fp.name} ... ")
        try:
            text, method = extract_text(fp)
            year_hint = guess_year_from_path(fp, root)
            fields = parse_document_fields(text, str(fp), year_hint) if text else dict(EMPTY_FIELDS)
            file_hash = compute_file_hash(fp)
            records.append({
                **fields,
                "文件名": fp.name,
                "文件路径": str(fp),
                "文件哈希": file_hash,
                "提取方式": method,
                **split_text_to_columns(text),
            })
            _state.log(f"  OK ({method})")
        except Exception as e:
            err = f"  错误: {e}"
            _state.log(err)
            with _state._lock:
                _state.errors.append(err)
        with _state._lock:
            _state.processed_files = i

    # 导出
    _state.log("导出 Excel...")
    tmp_dir = Path(tempfile.mkdtemp(prefix="miemie_archive_"))
    output_path = tmp_dir / "公文汇总.xlsx"
    export_records_to_excel(records, output_path)

    with _state._lock:
        _state.output_path = str(output_path)
        _state.phase = "complete"
        _state.is_running = False

    _state.log(f"完成！共 {len(records)} 条记录，输出: {output_path}")


@router.post("/start")
async def start_archive(request: ArchiveRequest) -> dict:
    directory = Path(request.directory).resolve()
    if not directory.is_dir():
        raise HTTPException(status_code=400, detail=f"目录不存在: {directory}")
    if _state.is_running:
        raise HTTPException(status_code=409, detail="归档任务正在运行中")

    _state.reset(str(directory))
    t = threading.Thread(target=_run_archive, args=(str(directory),), daemon=True)
    t.start()
    return {"message": "归档任务已启动"}


@router.get("/status")
async def get_archive_status() -> dict:
    return _state.to_dict()


@router.get("/download")
async def download_archive() -> FileResponse:
    if not _state.output_path or not Path(_state.output_path).exists():
        raise HTTPException(status_code=404, detail="结果文件不存在，请先运行归档")
    return FileResponse(
        path=_state.output_path,
        filename="公文汇总.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
