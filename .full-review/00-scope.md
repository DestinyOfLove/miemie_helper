# Review Scope

## Target

Comprehensive code review of the entire MieMie Helper project - a document archiving and search system with FastAPI + NiceGUI frontend, SQLite/Chromadb backend.

## Files

### Source Code (src/)
- `src/config.py` - Configuration management
- `src/core/extractor.py` - Text extraction (OCR, PDF, docx)
- `src/core/parser.py` - Field parsing (regex patterns)
- `src/core/file_scanner.py` - Directory scanning
- `src/core/excel_exporter.py` - Excel export
- `src/core/text_utils.py` - Text utilities
- `src/search/models.py` - Pydantic models
- `src/search/document_db.py` - SQLite metadata storage
- `src/search/fulltext_store.py` - FTS5 fulltext search
- `src/search/embedding.py` - Sentence transformer embeddings
- `src/search/vector_store.py` - ChromaDB vector storage
- `src/search/indexer.py` - Incremental indexing
- `src/api/index_routes.py` - Index API routes
- `src/api/search_routes.py` - Search API routes
- `src/api/export_routes.py` - Export API routes
- `src/api/archive_routes.py` - Archive API routes
- `src/ui/layout.py` - UI layout
- `src/ui/home_page.py` - Home page
- `src/ui/search_page.py` - Search page
- `src/ui/archive_page.py` - Archive page
- `src/webapp/app.py` - Main webapp
- `src/doc_archive/main.py` - CLI entry
- `src/doc_archive/extractor.py` - CLI extractor
- `src/doc_archive/parser.py` - CLI parser

### Entry Points
- `main.py` - Web application entry
- `start.py` - Start script
- `install.py` - Installation script

### Tests
- `tests/test_text_utils.py` - Text utilities tests

### Scripts
- `scripts/analyze_filenames.py` - Filename analysis script

## Flags

- Security Focus: no
- Performance Critical: no
- Strict Mode: no
- Framework: Python (FastAPI, NiceGUI)

## Review Phases

1. Code Quality & Architecture
2. Security & Performance
3. Testing & Documentation
4. Best Practices & Standards
5. Consolidated Report
