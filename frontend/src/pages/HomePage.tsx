import { useNavigate } from 'react-router-dom'

const tools = [
  {
    icon: '🔍',
    title: '文档搜索',
    desc: '在公文文件中搜索关键词。支持全文精确匹配，并可按字段范围检索。',
    sub: 'PDF / DOCX / JPG / PNG / TIFF / BMP',
    to: '/search',
  },
  {
    icon: '📊',
    title: '归档导出',
    desc: '批量提取公文元数据（发文字号、标题、日期等），导出为结构化 Excel 表格。',
    sub: '',
    to: '/archive',
  },
  {
    icon: '⋯',
    title: '更多工具',
    desc: '即将推出...',
    sub: '',
    to: null,
  },
]

export function HomePage() {
  const navigate = useNavigate()

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '40px 24px' }}>
      <h1 style={{ fontSize: 28, marginBottom: 8 }}>工具集</h1>
      <p style={{ color: '#666', marginBottom: 32 }}>所有数据本地处理，不上传任何内容</p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20 }}>
        {tools.map((t) => (
          <div
            key={t.title}
            onClick={() => t.to && navigate(t.to)}
            style={{
              border: '1px solid #e0e0e0',
              borderRadius: 8,
              padding: 24,
              cursor: t.to ? 'pointer' : 'default',
              opacity: t.to ? 1 : 0.5,
              transition: 'box-shadow 0.15s',
            }}
            onMouseEnter={(e) => t.to && ((e.currentTarget as HTMLDivElement).style.boxShadow = '0 2px 12px rgba(0,0,0,0.12)')}
            onMouseLeave={(e) => ((e.currentTarget as HTMLDivElement).style.boxShadow = 'none')}
          >
            <div style={{ fontSize: 32, marginBottom: 12 }}>{t.icon}</div>
            <div style={{ fontWeight: 600, fontSize: 17, marginBottom: 8 }}>{t.title}</div>
            <div style={{ color: '#555', fontSize: 14, lineHeight: 1.6 }}>{t.desc}</div>
            {t.sub && <div style={{ color: '#999', fontSize: 12, marginTop: 10 }}>{t.sub}</div>}
          </div>
        ))}
      </div>
    </div>
  )
}
