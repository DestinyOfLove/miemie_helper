"""集中配置：路径常量、模型名称、搜索参数。"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 运行时数据目录（可通过环境变量覆盖）
DATA_DIR = Path(
    os.environ.get("MIEMIE_DATA_DIR", PROJECT_ROOT / ".miemie_helper" / "doc_search")
).resolve()

# SQLite 数据库
DB_DIR = DATA_DIR / "db"
DB_PATH = DB_DIR / "documents.db"

# ChromaDB 持久化存储
CHROMA_DIR = DATA_DIR / "vector" / "chroma"

# Embedding 模型缓存
MODEL_DIR = DATA_DIR / "models"

# Embedding 模型配置
EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5"
EMBEDDING_DIMENSION = 512

# 文档分块参数
CHUNK_SIZE = 400  # 字符
CHUNK_OVERLAP = 80

# 支持的文件扩展名
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"}
PDF_EXTENSIONS = {".pdf"}
DOCX_EXTENSIONS = {".docx"}
DOC_EXTENSIONS = {".doc"}
WPS_EXTENSIONS = {".wps"}
OFD_EXTENSIONS = {".ofd"}
ALL_EXTENSIONS = (
    IMAGE_EXTENSIONS | PDF_EXTENSIONS | DOCX_EXTENSIONS
    | DOC_EXTENSIONS | WPS_EXTENSIONS | OFD_EXTENSIONS
)

# Excel 单元格字符上限
EXCEL_CELL_MAX = 32000

# Web 服务端口
WEB_PORT = 4001

# ── 性能相关配置 ──

# OCR 渲染 DPI（降低可提升速度，200 对标准公文足够）
OCR_DPI = int(os.environ.get("MIEMIE_OCR_DPI", "200"))

# 索引并行 worker 数（0 = 自动: max(1, cpu_count - 2)）
INDEXING_WORKERS = int(os.environ.get("MIEMIE_INDEXING_WORKERS", "0"))

# SQLite 批量提交大小
BATCH_COMMIT_SIZE = 50

# 向量检索返回的最大结果数
VECTOR_SEARCH_TOP_K = 100


def ensure_dirs() -> None:
    """确保运行时目录存在。"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
