"""搜索系统数据模型。"""

from pydantic import BaseModel


class DocumentRecord(BaseModel):
    """文档记录。"""
    id: str                         # 文件 MD5 哈希
    file_path: str
    file_name: str
    file_size: int
    file_mtime: float
    file_hash: str
    directory_root: str
    extracted_text: str = ""
    extraction_method: str = ""
    doc_number: str = ""            # 发文字号
    title: str = ""                 # 发文标题
    doc_date: str = ""              # 发文日期
    issuing_authority: str = ""     # 发文机关
    recipients: str = ""            # 主送单位
    doc_type: str = ""              # 公文种类
    classification: str = ""        # 密级
    source_year: str = ""           # 来源年份
    indexed_at: str = ""
    vector_indexed: bool = False
    fts_indexed: bool = False


class SearchRequest(BaseModel):
    """搜索请求。"""
    query: str
    max_results: int = 0  # 0 表示不限制，返回所有匹配
    scopes: list[str] = ["content"]  # 搜索范围：content / title / all
    directories: list[str] = []  # 搜索目录过滤，空表示搜全部


class SearchResult(BaseModel):
    """单条搜索结果。"""
    doc_id: str
    file_path: str
    file_name: str
    title: str = ""
    doc_number: str = ""
    doc_date: str = ""
    issuing_authority: str = ""
    doc_type: str = ""
    source_year: str = ""
    score: float = 0.0
    snippet: str = ""
    extracted_text: str = ""        # 原始全文，用于前端高亮展示
    match_type: str = ""            # "vector" 或 "fulltext"


class DualSearchResponse(BaseModel):
    """双模式搜索响应。"""
    vector_results: list[SearchResult] = []
    fulltext_results: list[SearchResult] = []


class IndexRequest(BaseModel):
    """索引请求。"""
    directory: str


class IndexStatusResponse(BaseModel):
    """索引状态。"""
    is_running: bool = False
    phase: str = "idle"
    directory: str = ""
    total_files: int = 0
    processed_files: int = 0
    added: int = 0
    updated: int = 0
    deleted: int = 0
    skipped: int = 0
    current_file: str = ""
    errors: list[str] = []


class DirectoryInfo(BaseModel):
    """已索引目录信息。"""
    directory_path: str
    file_count: int = 0
    indexed_count: int = 0
    last_scan_at: str = ""
    status: str = "idle"
    starred: bool = False


class FileChange(BaseModel):
    """单个文件变更。"""
    file_path: str
    file_name: str
    change_type: str  # "new" | "deleted" | "renamed" | "modified"
    old_path: str = ""


class DirectoryScanResult(BaseModel):
    """目录变更扫描结果。"""
    directory_path: str
    new_count: int = 0
    deleted_count: int = 0
    renamed_count: int = 0
    modified_count: int = 0
    unchanged_count: int = 0
    total_on_disk: int = 0
    changes: list[FileChange] = []
    error: str = ""


class ScanChangesResponse(BaseModel):
    """全部目录的变更扫描响应。"""
    results: list[DirectoryScanResult] = []
