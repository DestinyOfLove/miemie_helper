# Phase 1: Code Quality & Architecture Review

## Code Quality Findings

### Critical Issues (0)
No critical issues found.

### High Priority Issues

| Severity | File | Issue |
|----------|------|-------|
| **High** | `src/doc_archive/` | Duplicate code: `extractor.py` and `parser.py` duplicate `src/core/` implementations with hardcoded values |
| **High** | `src/webapp/app.py` | Legacy Gradio interface completely duplicates NiceGUI UI, should be removed |
| **High** | `src/webapp/app.py` | Hacky `sys.path.insert(0, ...)` workaround for imports |

### Medium Priority Issues

| Severity | File | Line | Issue |
|----------|------|------|-------|
| **Medium** | `src/search/indexer.py` | 135-417 | `run_indexing()` function too long (282 lines), should be split |
| **Medium** | `src/api/archive_routes.py` | 69-122 | `_run_archive()` contains too much business logic |
| **Medium** | `src/core/extractor.py` | 269-294 | `extract_text()` function too long, consider strategy pattern |
| **Medium** | `src/search/indexer.py` | 220-243 | 4-level nested if/else, should refactor to early returns |
| **Medium** | `src/search/indexer.py` | 269-335 | 5-level nested batch write loop |
| **Medium** | `src/search/indexer.py` | 333-335 | Exception re-raised without logging details to `indexing_status.errors` |
| **Medium** | `src/core/extractor.py` | 287-289 | LibreOffice conversion exception silently swallowed |
| **Medium** | `src/ui/search_page.py` | 188-191 | UI imports private functions (`_fulltext_search`, `_vector_search`) from API routes |
| **Medium** | Global | - | Global singletons (`_ocr_engine`, `_model`, `_conn`, `_chroma_client`) lack proper lifecycle management |
| **Medium** | `src/search/indexer.py` | 78 | Global `indexing_status` makes testing difficult |
| **Medium** | Multiple | - | No path traversal validation on directory parameters in API endpoints |
| **Medium** | `tests/` | - | Minimal test coverage - only `test_text_utils.py` exists |

### Low Priority Issues

| Severity | File | Issue |
|----------|------|-------|
| **Low** | `src/search/fulltext_store.py` | 158-159 FTS query exceptions silently return empty list |
| **Low** | Multiple | `split_text_to_columns()` defined in multiple files |
| **Low** | `src/search/vector_store.py` | `CHROMA_BATCH = 5000` should be in config.py |
| **Low** | `src/core/parser.py` | 95-121 3-level nesting in `extract_issuing_authority()` |
| **Low** | `src/core/file_scanner.py` | Missing return type annotations |
| **Low** | `src/search/document_db.py` | Uses `check_same_thread=False` as thread safety workaround |

---

## Architecture Findings

### Critical Issues (0)
No critical issues.

### High Priority Issues

| Severity | Location | Issue |
|----------|----------|-------|
| **High** | `src/doc_archive/` | Duplicate modules create maintenance burden - changes to core logic require updating multiple places |
| **High** | `src/webapp/app.py` | Path manipulation workaround indicates architectural problem |

### Medium Priority Issues

| Severity | Location | Issue |
|----------|----------|-------|
| **Medium** | Entry points | Three different entry points (`main.py`, `src/webapp/app.py`, `src/doc_archive/main.py`) create confusion |
| **Medium** | Global state | Globals for expensive resources lack proper lifecycle management and thread-safety |
| **Medium** | `src/search/indexer.py` | Documents identified by `file_hash` (MD5) only - collision risk |
| **Medium** | `src/api/archive_routes.py` | Implements separate state management from indexer, duplicating patterns |

### Positive Findings

| Aspect | Details |
|--------|---------|
| **Module Organization** | Clear separation: `core/`, `search/`, `api/`, `ui/`, `doc_archive/` |
| **Database Design** | Proper SQLite with WAL mode, foreign keys, incremental migrations |
| **Patterns Used** | Repository pattern, Factory pattern, Builder pattern, Pipeline pattern |
| **Pydantic Models** | Well-defined request/response schemas with validation |
| **Performance** | Incremental indexing, batch processing, parallel processing, ChromaDB chunking |

---

## Critical Issues for Phase 2 Context

1. **Path traversal vulnerability risk** - Directory parameters in API endpoints lack validation
2. **Silent exception handling** - Some exceptions swallowed, affecting security logging
3. **Global state management** - Thread-safety concerns with singletons
4. **No authentication** - Project states offline operation, but API has no access control
5. **Memory concerns** - PDF OCR loads entire page images into memory

---

## Summary

- **Code Quality**: 1 High, 12 Medium, 6 Low findings
- **Architecture**: 2 High, 4 Medium findings
- **Total Critical**: 0

Key concerns: Legacy duplicate code, overly long functions, global state management, minimal test coverage.
