import type { ReactNode } from 'react'
import type { Metadata } from 'next'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-quartz.css'
import './globals.css'
import { AppThemeProvider } from '../src/theme/AppThemeProvider'
import { AppShell } from '../src/components/layout/AppShell'

export const metadata: Metadata = {
  title: 'MieMie Helper',
  description: '本地文档搜索与归档工具',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body>
        <AppThemeProvider>
          <AppShell>{children}</AppShell>
        </AppThemeProvider>
      </body>
    </html>
  )
}
