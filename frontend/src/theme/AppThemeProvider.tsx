'use client'

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { CssBaseline, ThemeProvider, type PaletteMode } from '@mui/material'
import { buildAppTheme } from './theme'

const STORAGE_KEY = 'miemie-helper-color-mode'

type ThemeModeContextValue = {
  mode: PaletteMode
  toggleMode: () => void
}

const ThemeModeContext = createContext<ThemeModeContextValue | null>(null)

function resolveInitialMode(): PaletteMode {
  if (typeof window === 'undefined') return 'light'

  const stored = window.localStorage.getItem(STORAGE_KEY)
  if (stored === 'light' || stored === 'dark') return stored

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function AppThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<PaletteMode>(() => resolveInitialMode())

  useEffect(() => {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(STORAGE_KEY, mode)
  }, [mode])

  const value = useMemo<ThemeModeContextValue>(() => ({
    mode,
    toggleMode: () => setMode(prev => (prev === 'light' ? 'dark' : 'light')),
  }), [mode])

  const theme = useMemo(() => buildAppTheme(mode), [mode])

  return (
    <ThemeModeContext.Provider value={value}>
      <ThemeProvider theme={theme}>
        <CssBaseline enableColorScheme />
        {children}
      </ThemeProvider>
    </ThemeModeContext.Provider>
  )
}

export function useThemeMode() {
  const value = useContext(ThemeModeContext)
  if (!value) {
    throw new Error('useThemeMode must be used within AppThemeProvider')
  }
  return value
}
