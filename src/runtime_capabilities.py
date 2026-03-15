"""运行环境能力探测。"""

from src.core.extractor import find_soffice
from src.search.models import RuntimeCapabilities

LIBREOFFICE_MISSING_EFFECTS = [
    ".doc/.wps 文件无法提取文本内容",
    "这些文件不会进入全文检索结果",
    ".pdf / .docx / .ofd / 图片 等其他格式仍可正常处理",
]

LIBREOFFICE_MISSING_WARNING = (
    "当前机器未检测到 LibreOffice，.doc/.wps 文件无法提取文本或建立索引，"
    "搜索结果会遗漏这些文件内容。安装 LibreOffice 后重启应用即可恢复。"
)


def get_runtime_capabilities() -> RuntimeCapabilities:
    """返回当前机器的运行环境能力。"""
    libreoffice_path = find_soffice()
    libreoffice_available = libreoffice_path is not None

    warnings: list[str] = []
    unsupported_effects: list[str] = []

    if not libreoffice_available:
        warnings.append(LIBREOFFICE_MISSING_WARNING)
        unsupported_effects.extend(LIBREOFFICE_MISSING_EFFECTS)

    return RuntimeCapabilities(
        libreoffice_available=libreoffice_available,
        libreoffice_path=libreoffice_path,
        warnings=warnings,
        unsupported_effects=unsupported_effects,
    )
