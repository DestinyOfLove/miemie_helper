'use client'

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, type RuntimeCapabilities } from '../../api/client'

interface RuntimeCapabilitiesContextValue {
  capabilities: RuntimeCapabilities | null
}

const RuntimeCapabilitiesContext = createContext<RuntimeCapabilitiesContextValue | null>(null)

export function RuntimeCapabilitiesProvider({ children }: { children: ReactNode }) {
  const [capabilities, setCapabilities] = useState<RuntimeCapabilities | null>(null)

  useEffect(() => {
    let cancelled = false

    void api.runtimeCapabilities()
      .then(result => {
        if (!cancelled) {
          setCapabilities(result)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setCapabilities(null)
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <RuntimeCapabilitiesContext.Provider value={{ capabilities }}>
      {children}
    </RuntimeCapabilitiesContext.Provider>
  )
}

export function useRuntimeCapabilities() {
  const value = useContext(RuntimeCapabilitiesContext)
  if (!value) {
    throw new Error('useRuntimeCapabilities must be used within RuntimeCapabilitiesProvider')
  }
  return value
}
