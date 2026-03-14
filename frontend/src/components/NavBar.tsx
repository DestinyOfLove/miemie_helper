'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

export function NavBar() {
  const pathname = usePathname()

  return (
    <nav style={{
      background: '#1976D2',
      color: '#fff',
      padding: '0 24px',
      display: 'flex',
      alignItems: 'center',
      height: 52,
      gap: 32,
      fontSize: 15,
    }}>
      <span style={{ fontWeight: 700, fontSize: 17, marginRight: 16 }}>MieMie Helper</span>
      {[
        { to: '/', label: '首页' },
        { to: '/search', label: '文档搜索' },
        { to: '/archive', label: '归档导出' },
      ].map(({ to, label }) => (
        <Link
          key={to}
          href={to}
          style={{
            color: '#fff',
            textDecoration: 'none',
            borderBottom: pathname === to ? '2px solid #fff' : '2px solid transparent',
            paddingBottom: 2,
            fontWeight: pathname === to ? 600 : 400,
          }}
        >
          {label}
        </Link>
      ))}
    </nav>
  )
}
