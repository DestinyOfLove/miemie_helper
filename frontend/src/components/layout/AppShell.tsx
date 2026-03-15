import type { ReactNode } from 'react'
import { Box } from '@mui/material'
import { NavBar } from '../NavBar'
import { GlobalRuntimeAlert } from '../runtime/GlobalRuntimeAlert'
import { RuntimeCapabilitiesProvider } from '../runtime/RuntimeCapabilitiesProvider'

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <RuntimeCapabilitiesProvider>
      <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', color: 'text.primary' }}>
        <NavBar />
        <GlobalRuntimeAlert />
        <Box component="main" sx={{ py: 4 }}>
          {children}
        </Box>
      </Box>
    </RuntimeCapabilitiesProvider>
  )
}
