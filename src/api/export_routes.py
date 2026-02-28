"""Excel 导出 API 路由。"""

import tempfile
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

from src.core.excel_exporter import BASE_COLUMNS, export_records_to_excel, split_text_to_columns
from src.search import document_db

router = APIRouter(prefix="/api/export", tags=["export"])


@router.post("/excel")
async def export_to_excel(directory: str | None = None) -> FileResponse:
    """导出文档数据为 Excel。可指定目录或导出全部。"""
    if directory:
        docs = document_db.get_documents_by_directory(directory)
    else:
        docs = document_db.get_all_documents()

    records = []
    for doc in docs:
        record = {
            "发文字号": doc.doc_number,
            "发文标题": doc.title,
            "发文日期": doc.doc_date,
            "发文机关": doc.issuing_authority,
            "主送单位": doc.recipients,
            "公文种类": doc.doc_type,
            "密级": doc.classification,
            "来源年份": doc.source_year,
            "文件名": doc.file_name,
            "文件路径": doc.file_path,
            "文件哈希": doc.file_hash,
            "提取方式": doc.extraction_method,
            **split_text_to_columns(doc.extracted_text),
        }
        records.append(record)

    tmp_dir = Path(tempfile.mkdtemp(prefix="miemie_export_"))
    output_path = tmp_dir / "公文汇总.xlsx"
    export_records_to_excel(records, output_path)

    return FileResponse(
        path=str(output_path),
        filename="公文汇总.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
