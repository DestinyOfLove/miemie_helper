const BASE = process.env.NEXT_PUBLIC_API_BASE ?? '/api'

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
}

export interface DirectoryInfo {
  directory_path: string
  file_count: number
  indexed_count: number
  last_scan_at: string
  status: string
  starred: boolean
}

export interface FileChange {
  file_path: string
  file_name: string
  change_type: string
  old_path: string
}

export interface DirectoryScanResult {
  directory_path: string
  new_count: number
  deleted_count: number
  renamed_count: number
  modified_count: number
  unchanged_count: number
  total_on_disk: number
  changes: FileChange[]
  error: string
}

export interface ScanChangesResponse {
  results: DirectoryScanResult[]
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
  warnings: string[]
}

export const api = {
  search: async (query: string, scopes: string[] = ['content'], directories: string[] = []): Promise<SearchResult[]> => {
    const res = await fetch(`${BASE}/search/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, scopes, directories }),
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

  scanChanges: async (): Promise<ScanChangesResponse> => {
    const res = await fetch(`${BASE}/index/scan-changes`)
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  },

  toggleDirectoryStar: async (directory: string): Promise<{ directory: string; starred: boolean }> => {
    const res = await fetch(`${BASE}/index/directory/star`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ directory }),
    })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  },

  deleteDirectory: async (directory: string): Promise<void> => {
    const res = await fetch(`${BASE}/index/directory?directory=${encodeURIComponent(directory)}`, {
      method: 'DELETE',
    })
    if (!res.ok) throw new Error(await res.text())
  },

  rebuildDirectory: async (directory: string): Promise<void> => {
    const res = await fetch(`${BASE}/index/directory/rebuild`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ directory }),
    })
    if (!res.ok) throw new Error(await res.text())
  },
}
