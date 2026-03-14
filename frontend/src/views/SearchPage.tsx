'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { KeyboardEvent, ReactNode } from 'react'
import { AgGridReact } from 'ag-grid-react'
import type { ColDef } from 'ag-grid-community'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { api, type DirectoryInfo, type DirectoryScanResult, type IndexStatus } from '../api/client'

ModuleRegistry.registerModules([AllCommunityModule])

const AG_GRID_LOCALE_ZH: Record<string, string> = {
  contains: '包含',
  notContains: '不包含',
  equals: '等于',
  notEqual: '不等于',
  startsWith: '开头是',
  endsWith: '结尾是',
  blank: '为空',
  notBlank: '不为空',
  filterOoo: '筛选...',
  applyFilter: '应用',
  resetFilter: '重置',
  clearFilter: '清除',
  noRowsToShow: '暂无数据',
  page: '页',
  of: '/',
  to: '至',
  more: '更多',
  next: '下一页',
  previous: '上一页',
  first: '第一页',
  last: '最后一页',
  loadingOoo: '加载中...',
  pinColumn: '固定列',
  autosizeThisColumn: '自适应列宽',
  autosizeAllColumns: '自适应所有列宽',
  resetColumns: '重置列',
  sortAscending: '升序',
  sortDescending: '降序',
  sortUnSort: '取消排序',
}

type SearchScope = 'content' | 'title' | 'all'

const SCOPE_OPTIONS: { value: SearchScope; label: string; tip: string }[] = [
  { value: 'content', label: '正文', tip: '搜索文档正文内容（OCR / PDF / docx 提取的文字）' },
  { value: 'title', label: '标题', tip: '搜索发文标题和文件名' },
  { value: 'all', label: '全文', tip: '搜索所有字段：文件名、标题、发文字号、发文机关、正文' },
]

interface RowData {
  id: string
  doc_number: string
  folder: string
  file_name: string
  content: string
  _raw_text: string
}

function escapeRegex(s: string) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function highlightText(text: string, terms: string[]): string {
  if (!text || terms.length === 0) return escapeHtml(text)
  const escaped = escapeHtml(text)
  const sorted = [...terms].sort((a, b) => b.length - a.length)
  const pattern = sorted.map(escapeRegex).join('|')
  return escaped.replace(new RegExp(`(${pattern})`, 'gi'), '<mark>$1</mark>')
}

function escapeHtml(s: string) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function Tip({ text, children }: { text: string; children: ReactNode }) {
  return (
    <span className="tip-wrap" style={{ position: 'relative', display: 'inline-flex' }}>
      {children}
      <span className="tip-bubble">{text}</span>
    </span>
  )
}

function CopyableCell({ text, children }: { text: string; children: ReactNode }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // Clipboard copy is best-effort only.
    }
  }

  return (
    <div className="copyable-cell" style={{ position: 'relative' }}>
      {children}
      <button
        className="copy-btn"
        onClick={handleCopy}
        title="复制内容"
        style={{
          position: 'absolute',
          right: 4,
          top: 4,
          padding: '2px 8px',
          fontSize: 12,
          background: copied ? '#4CAF50' : '#fff',
          color: copied ? '#fff' : '#555',
          border: '1px solid #ccc',
          borderRadius: 4,
          cursor: 'pointer',
          opacity: 0,
          transition: 'opacity 0.15s',
          zIndex: 10,
          lineHeight: 1.6,
        }}
      >
        {copied ? '已复制' : '复制'}
      </button>
    </div>
  )
}

function stripHtml(html: string): string {
  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent || ''
}

function ContentCell({ value }: { value: string }) {
  const plainText = useMemo(() => stripHtml(value), [value])
  return (
    <CopyableCell text={plainText}>
      <div
        dangerouslySetInnerHTML={{ __html: value }}
        style={{
          padding: '8px 0',
          lineHeight: 1.8,
          fontSize: '0.85em',
          whiteSpace: 'normal',
          wordBreak: 'break-all',
          maxHeight: '220px',
          overflowY: 'auto',
        }}
      />
    </CopyableCell>
  )
}

function TextCell({ value }: { value: string }) {
  return (
    <CopyableCell text={value || ''}>
      <div style={{ padding: '8px 0', whiteSpace: 'normal', wordBreak: 'break-all' }}>{value}</div>
    </CopyableCell>
  )
}

const colDefs: ColDef<RowData>[] = [
  {
    field: 'doc_number',
    headerName: '发文字号',
    headerTooltip: '公文的正式编号，如"深龙办字〔2024〕11 号"',
    width: 160,
    sortable: true,
    filter: 'agTextColumnFilter',
    floatingFilter: true,
    cellRenderer: TextCell,
    cellStyle: { fontSize: '0.82em', color: '#555' },
  },
  {
    field: 'folder',
    headerName: '文件夹',
    headerTooltip: '文件所在的目录路径',
    flex: 1,
    minWidth: 130,
    sortable: true,
    filter: 'agTextColumnFilter',
    floatingFilter: true,
    autoHeight: true,
    wrapText: true,
    cellRenderer: TextCell,
    cellStyle: { fontSize: '0.82em', color: '#666' },
  },
  {
    field: 'file_name',
    headerName: '文件名',
    headerTooltip: '原始文件名',
    flex: 1,
    minWidth: 160,
    sortable: true,
    filter: 'agTextColumnFilter',
    floatingFilter: true,
    autoHeight: true,
    wrapText: true,
    cellRenderer: TextCell,
    cellStyle: { fontWeight: 500 },
  },
  {
    field: 'content',
    headerName: '内容',
    headerTooltip: '文档提取的完整原文，搜索关键词已高亮标记',
    flex: 3,
    minWidth: 320,
    cellRenderer: ContentCell,
  },
]

export function SearchPage() {
  const [tags, setTags] = useState<string[]>([])
  const [inputVal, setInputVal] = useState('')
  const [scopes, setScopes] = useState<SearchScope[]>(['content'])

  const [rows, setRows] = useState<RowData[]>([])
  const [count, setCount] = useState<string>('')
  const [searching, setSearching] = useState(false)
  const searchSeqRef = useRef(0)

  const [indexExpanded, setIndexExpanded] = useState(true)
  const [dirInput, setDirInput] = useState('')
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null)
  const [indexing, setIndexing] = useState(false)
  const [directories, setDirectories] = useState<DirectoryInfo[]>([])
  const [scanResults, setScanResults] = useState<Record<string, DirectoryScanResult>>({})
  const [scanning, setScanning] = useState(false)
  const [selectedDirs, setSelectedDirs] = useState<string[]>([])
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const gridRef = useRef<AgGridReact<RowData>>(null)

  const loadDirectories = useCallback(async () => {
    try {
      const dirs = await api.indexDirectories()
      setDirectories(dirs)
      setSelectedDirs(prev => {
        if (prev.length > 0) return prev
        const starred = dirs.filter(d => d.starred).map(d => d.directory_path)
        return starred.length > 0 ? starred : dirs.map(d => d.directory_path)
      })
    } catch {
      // Initial directory load failure should not block page rendering.
    }
  }, [])

  const doScanChanges = useCallback(async () => {
    setScanning(true)
    try {
      const res = await api.scanChanges()
      const map: Record<string, DirectoryScanResult> = {}
      for (const r of res.results) map[r.directory_path] = r
      setScanResults(map)
    } catch {
      // Scan failures are non-fatal for the rest of the page.
    }
    setScanning(false)
  }, [])

  useEffect(() => {
    loadDirectories().then(() => doScanChanges())
  }, [loadDirectories, doScanChanges])

  const commitTag = () => {
    const v = inputVal.trim()
    if (v && !tags.includes(v)) setTags(prev => [...prev, v])
    setInputVal('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      if (inputVal.trim()) {
        commitTag()
      } else {
        doSearch()
      }
    } else if (e.key === 'Backspace' && inputVal === '' && tags.length > 0) {
      setTags(prev => prev.slice(0, -1))
    }
  }

  const removeTag = (idx: number) => setTags(prev => prev.filter((_, i) => i !== idx))

  const toggleScope = (s: SearchScope) => {
    setScopes(prev =>
      prev.includes(s)
        ? prev.length > 1 ? prev.filter(x => x !== s) : prev
        : [...prev, s],
    )
  }

  const startIndexing = async () => {
    if (!dirInput.trim()) return
    try {
      await api.indexStart(dirInput.trim())
      setIndexing(true)
      pollRef.current = setInterval(async () => {
        const s = await api.indexStatus()
        setIndexStatus(s)
        if (!s.is_running && ['complete', 'error', 'idle'].includes(s.phase)) {
          clearInterval(pollRef.current!)
          setIndexing(false)
          await loadDirectories()
        }
      }, 600)
    } catch (e: unknown) {
      alert(String(e))
    }
  }

  const deleteDirectory = async (dir: string) => {
    if (!confirm(`确定删除「${dir}」的全部索引数据？此操作不可撤销。`)) return
    try {
      await api.deleteDirectory(dir)
      await loadDirectories()
      setSelectedDirs(prev => prev.filter(d => d !== dir))
    } catch (e: unknown) {
      alert(String(e))
    }
  }

  const refreshDirectory = async (dir: string) => {
    try {
      await api.indexStart(dir)
      setIndexing(true)
      pollRef.current = setInterval(async () => {
        const s = await api.indexStatus()
        setIndexStatus(s)
        if (!s.is_running && ['complete', 'error', 'idle'].includes(s.phase)) {
          clearInterval(pollRef.current!)
          setIndexing(false)
          await loadDirectories()
          await doScanChanges()
        }
      }, 600)
    } catch (e: unknown) {
      alert(String(e))
    }
  }

  const rebuildDirectory = async (dir: string) => {
    if (!confirm(`确定重建「${dir}」的索引？将删除旧索引并重新提取全部文件。`)) return
    try {
      await api.rebuildDirectory(dir)
      setIndexing(true)
      pollRef.current = setInterval(async () => {
        const s = await api.indexStatus()
        setIndexStatus(s)
        if (!s.is_running && ['complete', 'error', 'idle'].includes(s.phase)) {
          clearInterval(pollRef.current!)
          setIndexing(false)
          await loadDirectories()
        }
      }, 600)
    } catch (e: unknown) {
      alert(String(e))
    }
  }

  const doSearch = async () => {
    const allTerms = inputVal.trim()
      ? [...tags, inputVal.trim()]
      : [...tags]

    if (allTerms.length === 0) return
    if (inputVal.trim()) commitTag()

    setSearching(true)
    setRows([])
    setCount('搜索中...')
    const seq = ++searchSeqRef.current

    try {
      const query = allTerms.join(' ')
      const res = await api.search(query, scopes, selectedDirs)

      if (seq !== searchSeqRef.current) return

      const data = res.map((r, i) => {
        const folder = r.file_path.replace(/[/\\][^/\\]+$/, '')
        const text = r.extracted_text || r.snippet || ''
        return {
          id: `${seq}-${i}`,
          doc_number: r.doc_number || '',
          folder,
          file_name: r.file_name,
          content: highlightText(text, allTerms),
          _raw_text: text,
        }
      })

      setRows(data)
      setCount(data.length === 0 ? '无匹配结果' : `共 ${data.length} 条结果`)
    } catch (e: unknown) {
      alert(`搜索出错: ${String(e)}`)
      setCount('')
    } finally {
      setSearching(false)
    }
  }

  const getRowId = useCallback((params: { data: RowData }) => params.data.id, [])

  const onGridReady = useCallback(() => {
    gridRef.current?.api.sizeColumnsToFit()
  }, [])

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: '24px' }}>
      <h1 style={{ fontSize: 26, marginBottom: 20 }}>文档搜索</h1>

      <div style={{ border: '1px solid #e0e0e0', borderRadius: 8, marginBottom: 20 }}>
        <div
          onClick={() => setIndexExpanded(!indexExpanded)}
          style={{ padding: '12px 16px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, userSelect: 'none', fontWeight: 500 }}
        >
          ⚙ 索引管理 <span style={{ marginLeft: 'auto' }}>{indexExpanded ? '▲' : '▼'}</span>
        </div>
        {indexExpanded && (
          <div style={{ padding: '0 16px 16px', borderTop: '1px solid #f0f0f0' }}>
            <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
              <input
                value={dirInput}
                onChange={e => setDirInput(e.target.value)}
                placeholder="/path/to/documents"
                style={{ flex: 1, padding: '8px 12px', border: '1px solid #ccc', borderRadius: 6, fontSize: 14 }}
              />
              <button
                onClick={startIndexing}
                disabled={indexing}
                style={{ padding: '8px 18px', background: '#1976D2', color: '#fff', border: 'none', borderRadius: 6, cursor: indexing ? 'not-allowed' : 'pointer', opacity: indexing ? 0.6 : 1 }}
              >
                {indexing ? '索引中...' : '开始索引'}
              </button>
            </div>
            {indexStatus && (
              <div style={{ marginTop: 10 }}>
                <div style={{ padding: '10px 12px', background: '#f5f5f5', borderRadius: 6, fontSize: 13, color: '#555' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: indexStatus.is_running && indexStatus.total_files > 0 ? 8 : 0 }}>
                    <span
                      style={{
                        padding: '2px 8px',
                        borderRadius: 4,
                        fontSize: 12,
                        fontWeight: 600,
                        color: '#fff',
                        background: indexStatus.phase === 'complete'
                          ? '#4CAF50'
                          : indexStatus.phase === 'error'
                            ? '#D32F2F'
                            : indexStatus.is_running
                              ? '#1976D2'
                              : '#9E9E9E',
                      }}
                    >
                      {{
                        scanning: '扫描中',
                        extracting: '提取中',
                        indexing: '写入索引',
                        embedding: '生成向量',
                        complete: '完成',
                        error: '出错',
                        idle: '空闲',
                      }[indexStatus.phase] || indexStatus.phase}
                    </span>
                    {indexStatus.is_running && indexStatus.total_files > 0 && (
                      <span style={{ fontWeight: 500 }}>
                        {indexStatus.processed_files} / {indexStatus.total_files} 文件
                      </span>
                    )}
                    {indexStatus.current_file && (
                      <span
                        style={{ color: '#888', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}
                        title={indexStatus.current_file}
                      >
                        {indexStatus.current_file}
                      </span>
                    )}
                  </div>
                  {indexStatus.is_running && indexStatus.total_files > 0 && (
                    <div style={{ background: '#e0e0e0', borderRadius: 4, height: 6, overflow: 'hidden', marginBottom: 6 }}>
                      <div
                        style={{
                          height: '100%',
                          borderRadius: 4,
                          transition: 'width 0.3s ease',
                          width: `${Math.round((indexStatus.processed_files / indexStatus.total_files) * 100)}%`,
                          background: 'linear-gradient(90deg, #42A5F5, #1976D2)',
                        }}
                      />
                    </div>
                  )}
                  {(indexStatus.added > 0 || indexStatus.updated > 0 || indexStatus.deleted > 0 || indexStatus.skipped > 0 || indexStatus.phase === 'complete') && (
                    <div style={{ fontSize: 12, color: '#777', display: 'flex', gap: 12 }}>
                      {indexStatus.added > 0 && <span style={{ color: '#2E7D32' }}>+{indexStatus.added} 新增</span>}
                      {indexStatus.updated > 0 && <span style={{ color: '#E65100' }}>~{indexStatus.updated} 更新</span>}
                      {indexStatus.deleted > 0 && <span style={{ color: '#D32F2F' }}>-{indexStatus.deleted} 删除</span>}
                      {indexStatus.skipped > 0 && <span>{indexStatus.skipped} 跳过</span>}
                    </div>
                  )}
                </div>
                {indexStatus.warnings?.length > 0 && (
                  <div style={{ marginTop: 6, padding: '6px 12px', background: '#FFF8E1', border: '1px solid #FFE082', borderRadius: 6, fontSize: 12, color: '#F57F17' }}>
                    {indexStatus.warnings.map((w, i) => <div key={i} style={{ whiteSpace: 'pre-wrap' }}>{w}</div>)}
                  </div>
                )}
                {indexStatus.errors?.length > 0 && (
                  <div style={{ marginTop: 6, padding: '6px 12px', background: '#FFEBEE', border: '1px solid #EF9A9A', borderRadius: 6, fontSize: 12, color: '#C62828' }}>
                    {indexStatus.errors.map((e, i) => <div key={i}>{e}</div>)}
                  </div>
                )}
              </div>
            )}
            {directories.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <div style={{ fontWeight: 500, marginBottom: 8, fontSize: 14 }}>已索引目录</div>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ background: '#f5f5f5' }}>
                      {['目录', '文件数', '已索引', '状态', '变更检测', '最后扫描', '操作'].map(h => (
                        <th key={h} style={{ padding: '6px 10px', textAlign: 'left', borderBottom: '1px solid #e0e0e0', fontWeight: 500 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {directories.map(d => {
                      const scan = scanResults[d.directory_path]
                      let changeCell: ReactNode
                      if (scanning) {
                        changeCell = <span style={{ color: '#999' }}>扫描中...</span>
                      } else if (!scan) {
                        changeCell = <span style={{ color: '#999' }}>-</span>
                      } else if (scan.error) {
                        changeCell = <span style={{ color: '#D32F2F' }} title={scan.error}>错误</span>
                      } else {
                        const parts: ReactNode[] = []
                        if (scan.new_count > 0) parts.push(<span key="new" style={{ color: '#2E7D32' }}>+{scan.new_count} 新增</span>)
                        if (scan.deleted_count > 0) parts.push(<span key="del" style={{ color: '#D32F2F' }}>-{scan.deleted_count} 删除</span>)
                        if (scan.modified_count > 0) parts.push(<span key="mod" style={{ color: '#E65100' }}>~{scan.modified_count} 修改</span>)
                        if (scan.renamed_count > 0) parts.push(<span key="ren" style={{ color: '#F57C00' }}>{scan.renamed_count} 重命名</span>)
                        changeCell = parts.length > 0
                          ? <span style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>{parts}</span>
                          : <span style={{ color: '#4CAF50' }}>无变更</span>
                      }
                      return (
                        <tr key={d.directory_path}>
                          <td style={{ padding: '6px 10px', wordBreak: 'break-all' }}>{d.directory_path}</td>
                          <td style={{ padding: '6px 10px' }}>{d.file_count}</td>
                          <td style={{ padding: '6px 10px' }}>{d.indexed_count}</td>
                          <td style={{ padding: '6px 10px' }}>{d.status}</td>
                          <td style={{ padding: '6px 10px' }}>{changeCell}</td>
                          <td style={{ padding: '6px 10px' }}>{d.last_scan_at}</td>
                          <td style={{ padding: '6px 10px', whiteSpace: 'nowrap' }}>
                            {(() => {
                              const hasChanges = scan && !scan.error && (scan.new_count + scan.deleted_count + scan.modified_count + scan.renamed_count > 0)
                              return (
                                <button
                                  onClick={() => refreshDirectory(d.directory_path)}
                                  disabled={indexing}
                                  title="增量刷新：只处理新增、修改、删除的文件"
                                  style={{
                                    padding: '2px 10px',
                                    fontSize: 12,
                                    marginRight: 6,
                                    background: hasChanges ? '#4CAF50' : '#9E9E9E',
                                    color: '#fff',
                                    border: 'none',
                                    borderRadius: 4,
                                    cursor: indexing ? 'not-allowed' : 'pointer',
                                    opacity: indexing ? 0.5 : 1,
                                    fontWeight: hasChanges ? 600 : 400,
                                  }}
                                >
                                  刷新
                                </button>
                              )
                            })()}
                            <button
                              onClick={() => rebuildDirectory(d.directory_path)}
                              disabled={indexing}
                              title="删除旧索引并重新全量索引"
                              style={{
                                padding: '2px 10px',
                                fontSize: 12,
                                marginRight: 6,
                                background: '#FF9800',
                                color: '#fff',
                                border: 'none',
                                borderRadius: 4,
                                cursor: indexing ? 'not-allowed' : 'pointer',
                                opacity: indexing ? 0.5 : 1,
                              }}
                            >
                              重建
                            </button>
                            <button
                              onClick={() => deleteDirectory(d.directory_path)}
                              disabled={indexing}
                              title="删除该目录的全部索引数据"
                              style={{
                                padding: '2px 10px',
                                fontSize: 12,
                                background: '#D32F2F',
                                color: '#fff',
                                border: 'none',
                                borderRadius: 4,
                                cursor: indexing ? 'not-allowed' : 'pointer',
                                opacity: indexing ? 0.5 : 1,
                              }}
                            >
                              删除
                            </button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
        <Tip text="选择要搜索的字段范围，可多选">
          <span style={{ fontSize: 13, color: '#666', cursor: 'help', borderBottom: '1px dashed #aaa' }}>搜索范围：</span>
        </Tip>
        {SCOPE_OPTIONS.map(({ value, label, tip }) => {
          const active = scopes.includes(value)
          return (
            <Tip key={value} text={tip}>
              <button
                onClick={() => toggleScope(value)}
                style={{
                  padding: '4px 14px',
                  borderRadius: 20,
                  border: `1px solid ${active ? '#1976D2' : '#ccc'}`,
                  background: active ? '#E3F2FD' : '#fff',
                  color: active ? '#1565C0' : '#555',
                  cursor: 'pointer',
                  fontSize: 13,
                  fontWeight: active ? 600 : 400,
                }}
              >
                {label}
              </button>
            </Tip>
          )
        })}
      </div>

      {directories.length > 1 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10, flexWrap: 'wrap' }}>
          <Tip text="选择要搜索的目录范围，可多选。星标目录在页面加载时自动选中">
            <span style={{ fontSize: 13, color: '#666', cursor: 'help', borderBottom: '1px dashed #aaa' }}>搜索目录：</span>
          </Tip>
          {directories.map(d => {
            const dirName = d.directory_path.replace(/\\/g, '/').split('/').filter(Boolean).pop() || d.directory_path
            const active = selectedDirs.includes(d.directory_path)
            return (
              <span key={d.directory_path} style={{ display: 'inline-flex', alignItems: 'center', gap: 2 }}>
                <Tip text={d.directory_path}>
                  <button
                    onClick={() => {
                      setSelectedDirs(prev => {
                        if (active) {
                          return prev.length > 1 ? prev.filter(x => x !== d.directory_path) : prev
                        }
                        return [...prev, d.directory_path]
                      })
                    }}
                    style={{
                      padding: '4px 14px',
                      borderRadius: '20px 0 0 20px',
                      border: `1px solid ${active ? '#1976D2' : '#ccc'}`,
                      borderRight: 'none',
                      background: active ? '#E3F2FD' : '#fff',
                      color: active ? '#1565C0' : '#555',
                      cursor: 'pointer',
                      fontSize: 13,
                      fontWeight: active ? 600 : 400,
                    }}
                  >
                    {dirName}
                  </button>
                </Tip>
                <button
                  onClick={async () => {
                    try {
                      const res = await api.toggleDirectoryStar(d.directory_path)
                      setDirectories(prev => prev.map(dir =>
                        dir.directory_path === d.directory_path ? { ...dir, starred: res.starred } : dir,
                      ))
                    } catch {
                      // Preserve current UI state if the toggle call fails.
                    }
                  }}
                  title={d.starred ? '取消星标' : '设为默认'}
                  style={{
                    padding: '4px 8px',
                    borderRadius: '0 20px 20px 0',
                    border: `1px solid ${active ? '#1976D2' : '#ccc'}`,
                    background: active ? '#E3F2FD' : '#fff',
                    cursor: 'pointer',
                    fontSize: 14,
                    lineHeight: 1,
                    color: d.starred ? '#F9A825' : '#bbb',
                  }}
                >
                  {d.starred ? '★' : '☆'}
                </button>
              </span>
            )
          })}
        </div>
      )}

      <div style={{ display: 'flex', gap: 12, marginBottom: 10 }}>
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            gap: 6,
            padding: '6px 10px',
            border: '1px solid #ccc',
            borderRadius: 6,
            background: '#fff',
            minHeight: 44,
            cursor: 'text',
          }}
          onClick={() => document.getElementById('search-input')?.focus()}
        >
          {tags.map((t, i) => (
            <span
              key={i}
              style={{
                background: '#E3F2FD',
                color: '#1565C0',
                border: '1px solid #90CAF9',
                borderRadius: 4,
                padding: '2px 8px',
                fontSize: 14,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              {t}
              <span
                onClick={e => {
                  e.stopPropagation()
                  removeTag(i)
                }}
                style={{ cursor: 'pointer', color: '#888', fontWeight: 700, lineHeight: 1 }}
              >
                ×
              </span>
            </span>
          ))}
          <input
            id="search-input"
            value={inputVal}
            onChange={e => setInputVal(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={tags.length === 0 ? '输入关键词，按 Enter 添加标签，空输入再按 Enter 搜索...' : '继续添加关键词...'}
            style={{
              flex: 1,
              minWidth: 180,
              border: 'none',
              outline: 'none',
              fontSize: 15,
              padding: '2px 4px',
            }}
          />
        </div>
        <button
          onClick={doSearch}
          disabled={searching || (tags.length === 0 && !inputVal.trim())}
          style={{
            padding: '10px 28px',
            background: '#1976D2',
            color: '#fff',
            border: 'none',
            borderRadius: 6,
            cursor: searching ? 'not-allowed' : 'pointer',
            fontSize: 15,
            opacity: searching ? 0.6 : 1,
          }}
        >
          搜索
        </button>
      </div>

      {count && <div style={{ fontSize: 13, color: '#888', marginBottom: 8 }}>{count}</div>}

      <div style={{ width: '100%', height: 600 }}>
        <AgGridReact
          ref={gridRef}
          rowData={rows}
          columnDefs={colDefs}
          rowHeight={120}
          getRowId={getRowId}
          defaultColDef={{ resizable: true }}
          localeText={AG_GRID_LOCALE_ZH}
          onGridReady={onGridReady}
        />
      </div>

      <style>{`
        mark { background: #FFF176; padding: 1px 2px; border-radius: 2px; }
        .tip-wrap .tip-bubble {
          visibility: hidden; opacity: 0;
          position: absolute; bottom: calc(100% + 8px); left: 50%;
          transform: translateX(-50%); padding: 6px 12px;
          background: #333; color: #fff; font-size: 12px; line-height: 1.5;
          border-radius: 6px; white-space: nowrap;
          pointer-events: none; transition: opacity 0.15s; z-index: 100;
        }
        .tip-wrap .tip-bubble::after {
          content: ''; position: absolute; top: 100%; left: 50%;
          transform: translateX(-50%);
          border: 5px solid transparent; border-top-color: #333;
        }
        .tip-wrap:hover .tip-bubble { visibility: visible; opacity: 1; }
        .copyable-cell { position: relative; }
        .copyable-cell:hover .copy-btn { opacity: 1 !important; }
      `}</style>
    </div>
  )
}
