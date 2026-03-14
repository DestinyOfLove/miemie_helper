import type { ReactNode } from 'react'
import { Container, Stack, Typography } from '@mui/material'

type PageContainerProps = {
  title: string
  description?: string
  children: ReactNode
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl'
}

export function PageContainer({
  title,
  description,
  children,
  maxWidth = 'xl',
}: PageContainerProps) {
  return (
    <Container maxWidth={maxWidth}>
      <Stack spacing={3}>
        <Stack spacing={1}>
          <Typography variant="h1">{title}</Typography>
          {description && (
            <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 760 }}>
              {description}
            </Typography>
          )}
        </Stack>
        {children}
      </Stack>
    </Container>
  )
}
