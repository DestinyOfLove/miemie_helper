import type { ReactNode } from 'react'
import { Paper, type PaperProps } from '@mui/material'

export function SectionPanel(props: PaperProps & { children: ReactNode }) {
  const { children, sx, ...rest } = props

  return (
    <Paper
      variant="outlined"
      sx={{
        p: 3,
        borderColor: 'divider',
        borderRadius: '28px',
        ...sx,
      }}
      {...rest}
    >
      {children}
    </Paper>
  )
}
