"""集中配置：路径常量、模型名称、搜索参数。"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 运行时数据目录（可通过环境变量覆盖）
DATA_DIR = Path(
    os.environ.get("MIEMIE_DATA_DIR", PROJECT_ROOT / ".miemie_data")
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
ALL_EXTENSIONS = IMAGE_EXTENSIONS | PDF_EXTENSIONS | DOCX_EXTENSIONS | DOC_EXTENSIONS

# Excel 单元格字符上限
EXCEL_CELL_MAX = 32000

# Web 服务端口
WEB_PORT = 4001


def ensure_dirs() -> None:
    """确保运行时目录存在。"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
