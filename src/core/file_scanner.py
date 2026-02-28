"""文件系统扫描与路径工具。"""

import re
from pathlib import Path

from src.config import ALL_EXTENSIONS


def scan_directory(root_dir: Path) -> list[Path]:
    """递归扫描目录，返回所有支持格式的文件路径（排序后）。"""
    files = []
    for file_path in sorted(root_dir.rglob("*")):
        if (
            file_path.is_file()
            and file_path.suffix.lower() in ALL_EXTENSIONS
            and not file_path.name.startswith((".", "~"))
        ):
            files.append(file_path)
    return files


def guess_year_from_path(file_path: Path, root_dir: Path) -> str:
    """从文件相对路径中推断年份。"""
    try:
        rel_path = file_path.relative_to(root_dir)
    except ValueError:
        rel_path = file_path
    for part in rel_path.parts:
        match = re.match(r"^(19\d{2}|20\d{2})$", part)
        if match:
            return match.group(1)
    return ""
