import type { ReactNode } from 'react'
import { Box } from '@mui/material'
import { NavBar } from '../NavBar'

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', color: 'text.primary' }}>
      <NavBar />
      <Box component="main" sx={{ py: 4 }}>
        {children}
      </Box>
    </Box>
  )
}
