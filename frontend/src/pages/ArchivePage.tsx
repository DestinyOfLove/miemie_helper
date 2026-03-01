import { useRef, useState } from 'react'
import { api, type ArchiveStatus } from '../api/client'

export function ArchivePage() {
  const [dirInput, setDirInput] = useState('')
  const [running, setRunning] = useState(false)
  const [status, setStatus] = useState<ArchiveStatus | null>(null)
  const [done, setDone] = useState(false)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const logRef = useRef<HTMLPreElement>(null)

  const start = async () => {
    if (!dirInput.trim()) return
    setRunning(true)
    setDone(false)
    setStatus(null)

    try {
      await api.archiveStart(dirInput.trim())

      pollRef.current = setInterval(async () => {
        const s = await api.archiveStatus()
        setStatus(s)
        // 自动滚到底
        if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
        if (!s.is_running && s.phase !== 'idle') {
          clearInterval(pollRef.current!)
          setRunning(false)
          if (s.phase === 'complete') setDone(true)
        }
      }, 500)
    } catch (e: unknown) {
      alert(String(e))
      setRunning(false)
    }
  }

  const progress = status && status.total_files > 0
    ? Math.round((status.processed_files / status.total_files) * 100)
    : 0

  return (
    <div style={{ maxWidth: 860, margin: '0 auto', padding: '24px 24px' }}>
      <h1 style={{ fontSize: 26, marginBottom: 8 }}>归档导出</h1>
      <p style={{ color: '#666', marginBottom: 24 }}>
        批量提取公文元数据并导出为 Excel 表格。直接扫描本地目录，文件不会被复制或上传。
      </p>

      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        <input
          value={dirInput}
          onChange={e => setDirInput(e.target.value)}
          placeholder="/path/to/documents"
          disabled={running}
          style={{ flex: 1, padding: '10px 14px', border: '1px solid #ccc', borderRadius: 6, fontSize: 15 }}
        />
        <button
          onClick={start}
          disabled={running || !dirInput.trim()}
          style={{ padding: '10px 24px', background: '#388E3C', color: '#fff', border: 'none', borderRadius: 6, cursor: running ? 'not-allowed' : 'pointer', fontSize: 15, opacity: running ? 0.6 : 1 }}
        >
          {running ? '处理中...' : '开始处理'}
        </button>
      </div>

      {status && (
        <>
          {/* 进度条 */}
          <div style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: '#555', marginBottom: 4 }}>
              <span>{status.phase}</span>
              <span>{status.processed_files} / {status.total_files} 文件</span>
            </div>
            <div style={{ background: '#e0e0e0', borderRadius: 4, height: 8 }}>
              <div style={{ background: '#388E3C', height: '100%', borderRadius: 4, width: `${progress}%`, transition: 'width 0.3s' }} />
            </div>
          </div>

          {/* 日志 */}
          <pre
            ref={logRef}
            style={{
              background: '#1e1e1e',
              color: '#d4d4d4',
              padding: 16,
              borderRadius: 8,
              fontSize: 12.5,
              lineHeight: 1.7,
              maxHeight: 360,
              overflowY: 'auto',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-all',
              fontFamily: 'ui-monospace, SFMono-Regular, monospace',
            }}
          >
            {status.log_lines.join('\n')}
          </pre>
        </>
      )}

      {done && (
        <button
          onClick={api.archiveDownload}
          style={{ marginTop: 16, padding: '10px 28px', background: '#1976D2', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 15 }}
        >
          ⬇ 下载 Excel 结果
        </button>
      )}
    </div>
  )
}
