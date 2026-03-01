import { useCallback, useEffect, useRef, useState } from 'react'
import type { KeyboardEvent } from 'react'
import { AgGridReact } from 'ag-grid-react'
import type { ColDef, GridReadyEvent } from 'ag-grid-community'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { api, type DirectoryInfo, type IndexStatus } from '../api/client'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-quartz.css'

ModuleRegistry.registerModules([AllCommunityModule])

// ── AG Grid 中文本地化 ──────────────────────────────────────────
const AG_GRID_LOCALE_ZH: Record<string, string> = {
  // 筛选器
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
  // 通用
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
  // 列菜单
  pinColumn: '固定列',
  autosizeThisColumn: '自适应列宽',
  autosizeAllColumns: '自适应所有列宽',
  resetColumns: '重置列',
  sortAscending: '升序',
  sortDescending: '降序',
  sortUnSort: '取消排序',
}

// ── 搜索范围 ────────────────────────────────────────────────────
type SearchScope = 'content' | 'title' | 'all'

const SCOPE_OPTIONS: { value: SearchScope; label: string; tip: string }[] = [
  { value: 'content', label: '正文', tip: '搜索文档正文内容（OCR / PDF / docx 提取的文字）' },
  { value: 'title', label: '标题', tip: '搜索发文标题和文件名' },
  { value: 'all', label: '全文', tip: '搜索所有字段：文件名、标题、发文字号、发文机关、正文' },
]

// ── 行数据 ──────────────────────────────────────────────────────
interface RowData {
  doc_number: string
  folder: string
  file_name: string
  content: string   // 已渲染 HTML，供 cellRenderer 使用
  match_type: string
  _raw_text: string // 原始文本，供调试
}

const MATCH_BADGE: Record<string, string> = {
  '精确匹配': '<span style="background:#1565C0;color:#fff;padding:2px 10px;border-radius:4px;font-size:0.78em;white-space:nowrap">精确匹配</span>',
  '语义匹配': '<span style="background:#E65100;color:#fff;padding:2px 10px;border-radius:4px;font-size:0.78em;white-space:nowrap">语义匹配</span>',
  '精确+语义': '<span style="background:#6A1B9A;color:#fff;padding:2px 10px;border-radius:4px;font-size:0.78em;white-space:nowrap">精确+语义</span>',
}

// ── 高亮函数 ────────────────────────────────────────────────────
function escapeRegex(s: string) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function highlightText(text: string, terms: string[]): string {
  if (!text || terms.length === 0) return escapeHtml(text)
  const escaped = escapeHtml(text)
  // 按长度降序排，长词优先匹配，避免短词把长词拆散
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

// ── Tooltip 组件（纯 CSS，零依赖）────────────────────────────────
function Tip({ text, children }: { text: string; children: React.ReactNode }) {
  return (
    <span className="tip-wrap" style={{ position: 'relative', display: 'inline-flex' }}>
      {children}
      <span className="tip-bubble">{text}</span>
    </span>
  )
}

// ── 复制按钮包装器 ──────────────────────────────────────────────
function CopyableCell({ text, children }: { text: string; children: React.ReactNode }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch { /* 降级：不处理 */ }
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
          bottom: 4,
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

// ── 从 HTML 中提取纯文本 ─────────────────────────────────────────
function stripHtml(html: string): string {
  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent || ''
}

// ── Cell Renderers ──────────────────────────────────────────────
function HtmlCell({ value }: { value: string }) {
  return (
    <CopyableCell text={stripHtml(value)}>
      <div
        dangerouslySetInnerHTML={{ __html: value }}
        style={{ padding: '8px 0', lineHeight: 1.8, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}
      />
    </CopyableCell>
  )
}

function ContentCell({ value }: { value: string }) {
  return (
    <CopyableCell text={stripHtml(value)}>
      <div
        dangerouslySetInnerHTML={{ __html: value }}
        style={{
          padding: '8px 0',
          lineHeight: 1.8,
          fontSize: '0.85em',
          whiteSpace: 'pre-wrap',
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
      <div style={{ padding: '8px 0' }}>{value}</div>
    </CopyableCell>
  )
}

// ── 列定义 ──────────────────────────────────────────────────────
const colDefs: ColDef<RowData>[] = [
  {
    field: 'doc_number',
    headerName: '发文字号',
    headerTooltip: '公文的正式编号，如"深龙办字〔2024〕11 号"',
    width: 160,
    sortable: true,
    filter: 'agTextColumnFilter',
    floatingFilter: true,
    wrapText: true,
    autoHeight: true,
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
    wrapText: true,
    autoHeight: true,
    cellRenderer: TextCell,
    cellStyle: { fontSize: '0.82em', color: '#666', wordBreak: 'break-all' },
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
    wrapText: true,
    autoHeight: true,
    cellRenderer: TextCell,
    cellStyle: { fontWeight: 500 },
  },
  {
    field: 'content',
    headerName: '内容',
    headerTooltip: '文档提取的完整原文，搜索关键词已高亮标记',
    flex: 3,
    minWidth: 320,
    autoHeight: true,
    cellRenderer: ContentCell,
  },
  {
    field: 'match_type',
    headerName: '匹配方式',
    headerTooltip: '精确匹配 = 关键词逐字匹配；语义匹配 = 含义相近；精确+语义 = 两者都命中',
    width: 120,
    sortable: true,
    filter: 'agTextColumnFilter',
    cellRenderer: HtmlCell,
    cellStyle: { display: 'flex', alignItems: 'center', justifyContent: 'center' },
  },
]

// ── 主组件 ──────────────────────────────────────────────────────
export function SearchPage() {
  // 搜索词 Tags
  const [tags, setTags] = useState<string[]>([])
  const [inputVal, setInputVal] = useState('')
  // 搜索范围（多选）
  const [scopes, setScopes] = useState<SearchScope[]>(['content'])

  const [rows, setRows] = useState<RowData[]>([])
  const [count, setCount] = useState<string>('')
  const [searching, setSearching] = useState(false)

  // 索引管理
  const [indexExpanded, setIndexExpanded] = useState(false)
  const [dirInput, setDirInput] = useState('')
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null)
  const [indexing, setIndexing] = useState(false)
  const [directories, setDirectories] = useState<DirectoryInfo[]>([])
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const gridRef = useRef<AgGridReact<RowData>>(null)

  const loadDirectories = useCallback(async () => {
    try { setDirectories(await api.indexDirectories()) } catch (_) {}
  }, [])

  useEffect(() => { loadDirectories() }, [loadDirectories])

  // ── Tag 输入处理 ──────────────────────────────────────────────
  const commitTag = () => {
    const v = inputVal.trim()
    if (v && !tags.includes(v)) setTags(prev => [...prev, v])
    setInputVal('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      if (inputVal.trim()) {
        // 有内容：提交为 tag
        commitTag()
      } else {
        // 空内容：触发搜索
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
        ? prev.length > 1 ? prev.filter(x => x !== s) : prev  // 至少保留一个
        : [...prev, s]
    )
  }

  // ── 索引 ─────────────────────────────────────────────────────
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
    } catch (e: unknown) { alert(String(e)) }
  }

  // ── 搜索 ─────────────────────────────────────────────────────
  const doSearch = async () => {
    // 把当前输入框内容也纳入 tags（若有）
    const allTerms = inputVal.trim()
      ? [...tags, inputVal.trim()]
      : [...tags]

    if (allTerms.length === 0) return
    if (inputVal.trim()) { commitTag() }

    setSearching(true)
    setRows([])
    setCount('搜索中...')

    try {
      // 将所有 tag 用空格连接成查询词发给后端
      const query = allTerms.join(' ')
      const res = await api.search(query, scopes)
      const merged = new Map<string, RowData>()

      for (const r of res.fulltext_results) {
        const folder = r.file_path.replace(/[/\\][^/\\]+$/, '')
        const text = r.extracted_text || r.snippet || ''
        merged.set(r.doc_id, {
          doc_number: r.doc_number || '',
          folder,
          file_name: r.file_name,
          content: highlightText(text, allTerms),
          match_type: MATCH_BADGE['精确匹配'],
          _raw_text: text,
        })
      }

      for (const r of res.vector_results) {
        const folder = r.file_path.replace(/[/\\][^/\\]+$/, '')
        const text = r.extracted_text || r.snippet || ''
        if (merged.has(r.doc_id)) {
          merged.get(r.doc_id)!.match_type = MATCH_BADGE['精确+语义']
        } else {
          merged.set(r.doc_id, {
            doc_number: r.doc_number || '',
            folder,
            file_name: r.file_name,
            content: highlightText(text, allTerms),
            match_type: MATCH_BADGE['语义匹配'],
            _raw_text: text,
          })
        }
      }

      const data = Array.from(merged.values())
      setRows(data)
      setCount(`共 ${data.length} 条结果`)
      if (data.length === 0) setCount('无匹配结果')
    } catch (e: unknown) {
      alert(`搜索出错: ${String(e)}`)
      setCount('')
    } finally {
      setSearching(false)
    }
  }

  const onGridReady = (_: GridReadyEvent) => {
    gridRef.current?.api.sizeColumnsToFit()
  }

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: '24px' }}>
      <h1 style={{ fontSize: 26, marginBottom: 20 }}>文档搜索</h1>

      {/* 索引管理 */}
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
              <div style={{ marginTop: 10, padding: '8px 12px', background: '#f5f5f5', borderRadius: 6, fontSize: 13, color: '#555' }}>
                {indexStatus.phase} | {indexStatus.current_file || '-'} | 新增 {indexStatus.added} / 更新 {indexStatus.updated} / 跳过 {indexStatus.skipped}
              </div>
            )}
            {directories.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <div style={{ fontWeight: 500, marginBottom: 8, fontSize: 14 }}>已索引目录</div>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ background: '#f5f5f5' }}>
                      {['目录', '文件数', '已索引', '状态', '最后扫描'].map(h => (
                        <th key={h} style={{ padding: '6px 10px', textAlign: 'left', borderBottom: '1px solid #e0e0e0', fontWeight: 500 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {directories.map(d => (
                      <tr key={d.directory_path}>
                        <td style={{ padding: '6px 10px', wordBreak: 'break-all' }}>{d.directory_path}</td>
                        <td style={{ padding: '6px 10px' }}>{d.file_count}</td>
                        <td style={{ padding: '6px 10px' }}>{d.indexed_count}</td>
                        <td style={{ padding: '6px 10px' }}>{d.status}</td>
                        <td style={{ padding: '6px 10px' }}>{d.last_scan_at}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 搜索范围 */}
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

      {/* Tag 输入框 */}
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
                onClick={e => { e.stopPropagation(); removeTag(i) }}
                style={{ cursor: 'pointer', color: '#888', fontWeight: 700, lineHeight: 1 }}
              >×</span>
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

      {/* AG Grid */}
      <div className="ag-theme-quartz" style={{ width: '100%' }}>
        <AgGridReact
          ref={gridRef}
          rowData={rows}
          columnDefs={colDefs}
          domLayout="autoHeight"
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
        .copyable-cell:hover .copy-btn { opacity: 1 !important; }
      `}</style>
    </div>
  )
}
