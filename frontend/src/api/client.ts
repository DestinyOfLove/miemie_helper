const BASE = '/api'

export interface SearchResult {
  doc_id: string
  file_path: string
  file_name: string
  title: string
  doc_number: string
  doc_date: string
  issuing_authority: string
  doc_type: string
  source_year: string
  score: number
  snippet: string
  extracted_text: string
  match_type: string
}

export interface DualSearchResponse {
  fulltext_results: SearchResult[]
  vector_results: SearchResult[]
}

export interface DirectoryInfo {
  directory_path: string
  file_count: number
  indexed_count: number
  last_scan_at: string
  status: string
}

export interface IndexStatus {
  is_running: boolean
  phase: string
  directory: string
  total_files: number
  processed_files: number
  added: number
  updated: number
  deleted: number
  skipped: number
  current_file: string
  errors: string[]
}

export interface ArchiveStatus {
  is_running: boolean
  phase: string
  directory: string
  total_files: number
  processed_files: number
  errors: string[]
  output_path: string
  log_lines: string[]
}

export const api = {
  search: async (query: string, scopes: string[] = ['content']): Promise<DualSearchResponse> => {
    const res = await fetch(`${BASE}/search/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, max_results: 0, scopes }),
    })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  },

  indexStart: async (directory: string): Promise<void> => {
    const res = await fetch(`${BASE}/index/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ directory }),
    })
    if (!res.ok) throw new Error(await res.text())
  },

  indexStatus: async (): Promise<IndexStatus> => {
    const res = await fetch(`${BASE}/index/status`)
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  },

  indexDirectories: async (): Promise<DirectoryInfo[]> => {
    const res = await fetch(`${BASE}/index/directories`)
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  },

  archiveStart: async (directory: string): Promise<void> => {
    const res = await fetch(`${BASE}/archive/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ directory }),
    })
    if (!res.ok) throw new Error(await res.text())
  },

  archiveStatus: async (): Promise<ArchiveStatus> => {
    const res = await fetch(`${BASE}/archive/status`)
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  },

  archiveDownload: () => {
    window.open(`${BASE}/archive/download`, '_blank')
  },

  exportExcel: (directory?: string) => {
    const url = directory
      ? `${BASE}/export/excel?directory=${encodeURIComponent(directory)}`
      : `${BASE}/export/excel`
    window.open(url, '_blank')
  },
}
