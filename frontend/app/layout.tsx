import type { ReactNode } from 'react'
import type { Metadata } from 'next'
import './globals.css'
import { NavBar } from '../src/components/NavBar'

export const metadata: Metadata = {
  title: 'MieMie Helper',
  description: '本地文档搜索与归档工具',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <NavBar />
        <main>{children}</main>
      </body>
    </html>
  )
}
