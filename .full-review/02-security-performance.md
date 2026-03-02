# Phase 2: Security & Performance Review

## Security Findings

### Critical Issues

| Severity | CWE | Location | Issue |
|----------|-----|----------|-------|
| **Critical** | CWE-22 | `src/api/index_routes.py` 25-35, 94-105; `src/api/archive_routes.py` 125-136 | Path traversal vulnerability - directory parameters lack validation |
| **Critical** | CWE-611 | `src/core/extractor.py` 234-257 | XXE vulnerability in OFD XML parsing |

### High Priority Issues

| Severity | CWE | Location | Issue |
|----------|-----|----------|-------|
| **High** | CWE-306 | `main.py` 42-47, all API routes | No authentication - binds to 0.0.0.0 with no access control |
| **High** | CWE-1104 | `pyproject.toml` | Dependency vulnerabilities - pymupdf, openpyxl, pillow have known CVEs |

### Medium Priority Issues

| Severity | CWE | Location | Issue |
|----------|-----|----------|-------|
| **Medium** | CWE-89 | `src/search/fulltext_store.py` 84-94 | SQL injection risk - dynamic query construction |
| **Medium** | CWE-209 | `src/core/extractor.py` 284-289, `src/search/indexer.py` 408-411 | Information disclosure through error messages |
| **Medium** | CWE-662 | `src/search/document_db.py` 9, `src/search/embedding.py` 8, `src/core/extractor.py` 34 | Global state thread safety concerns |
| **Medium** | CWE-770 | All API endpoints | Missing rate limiting |
| **Medium** | CWE-502 | `src/search/indexer.py` 354-360 | Insecure path handling |
| **Medium** | CWE-377 | `src/api/export_routes.py` 42-43, `src/api/archive_routes.py` 113-114 | Insecure temporary file handling |

### Low Priority Issues

| Severity | CWE | Location | Issue |
|----------|-----|----------|-------|
| **Low** | CWE-611 | `src/core/extractor.py` 234-257 | XXE in OFD XML parsing |

---

## Performance Findings

### Critical Issues

| Severity | Location | Issue |
|----------|----------|-------|
| **Critical** | `src/core/extractor.py` 91-103 | PDF OCR loads full page images into memory - OOM risk on large PDFs |
| **Critical** | `src/api/export_routes.py` 23-40 | Export loads all documents into memory before writing Excel |

### High Priority Issues

| Severity | Location | Issue |
|----------|----------|-------|
| **High** | `src/search/document_db.py` | Missing indexes on processing_status, file_hash, file_mtime columns |
| **High** | `src/api/search_routes.py` | Synchronous blocking calls inside async functions |
| **High** | `src/search/document_db.py` | SQLite connection not thread-safe - uses check_same_thread=False workaround |
| **High** | Architecture | Single SQLite instance - no horizontal scaling capability |

### Medium Priority Issues

| Severity | Location | Issue |
|----------|----------|-------|
| **Medium** | `src/search/fulltext_store.py`, `vector_store.py` | No pagination in search results |
| **Medium** | `src/search/indexer.py` 266-327 | Unbounded all_chunks list accumulation during bulk indexing |
| **Medium** | `src/search/models.py` | Full document text included in SearchResult - large payloads |
| **Medium** | `src/api/search_routes.py` | No query result caching |
| **Medium** | Global singletons | No thread-safe initialization (double-checked locking) |
| **Medium** | `src/search/vector_store.py` | ChromaDB query without pagination |
| **Medium** | All API endpoints | No rate limiting |

### Low Priority Issues

| Severity | Location | Issue |
|----------|----------|-------|
| **Low** | `src/search/indexer.py` 457 | MD5 hash computed twice per unchanged file |
| **Low** | Frontend | No bundle size analysis or optimization |

---

## Critical Issues for Phase 3 Context

1. **No test coverage** for security-critical paths (path validation, authentication)
2. **No test coverage** for performance-critical paths (indexing pipeline, search)
3. **Minimal existing tests** - only `tests/test_text_utils.py` exists
4. **Documentation gaps** - no security or performance documentation

---

## Summary

### Security
- **Critical**: 2
- **High**: 2
- **Medium**: 6
- **Low**: 1

### Performance
- **Critical**: 2
- **High**: 4
- **Medium**: 7
- **Low**: 2

### Key Concerns
1. Path traversal vulnerability requires immediate attention
2. PDF OCR memory management critical for large files
3. Export streaming needed to prevent OOM
4. Missing database indexes impact query performance
5. No authentication (acceptable if truly offline)
