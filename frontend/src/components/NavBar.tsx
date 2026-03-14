'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import DarkModeOutlinedIcon from '@mui/icons-material/DarkModeOutlined'
import LightModeOutlinedIcon from '@mui/icons-material/LightModeOutlined'
import SearchRoundedIcon from '@mui/icons-material/SearchRounded'
import { AppBar, Box, Button, IconButton, Stack, Toolbar, Tooltip, Typography } from '@mui/material'
import { alpha } from '@mui/material/styles'
import { useThemeMode } from '../theme/AppThemeProvider'

export function NavBar() {
  const pathname = usePathname()
  const { mode, toggleMode } = useThemeMode()

  return (
    <AppBar
      position="sticky"
      color="transparent"
      elevation={0}
      sx={{
        backdropFilter: 'blur(12px)',
        backgroundColor: theme => alpha(theme.palette.background.paper, 0.82),
        borderBottom: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Toolbar sx={{ minHeight: 72, px: { xs: 2, md: 3 } }}>
        <Stack direction="row" alignItems="center" spacing={1.5} sx={{ flexGrow: 1 }}>
          <Box
            sx={{
              width: 40,
              height: 40,
              borderRadius: '16px',
              display: 'grid',
              placeItems: 'center',
              bgcolor: 'primary.main',
              color: 'primary.contrastText',
              boxShadow: theme => `0 10px 24px ${alpha(theme.palette.primary.main, 0.24)}`,
            }}
          >
            <SearchRoundedIcon fontSize="small" />
          </Box>
          <Box>
            <Typography variant="h6">MieMie Helper</Typography>
            <Typography variant="caption" color="text.secondary">
              Desktop document workflow
            </Typography>
          </Box>
        </Stack>

        <Stack direction="row" spacing={1} alignItems="center">
          {[
            { to: '/', label: '首页' },
            { to: '/search', label: '文档搜索' },
          ].map(({ to, label }) => {
            const active = pathname === to
            return (
              <Button
                key={to}
                component={Link}
                href={to}
                color={active ? 'primary' : 'inherit'}
                variant={active ? 'contained' : 'text'}
                sx={{
                  minWidth: 92,
                  color: active ? 'primary.contrastText' : 'text.primary',
                }}
              >
                {label}
              </Button>
            )
          })}

          <Tooltip title={mode === 'light' ? '切换到深色模式' : '切换到浅色模式'}>
            <IconButton onClick={toggleMode} color="primary">
              {mode === 'light' ? <DarkModeOutlinedIcon /> : <LightModeOutlinedIcon />}
            </IconButton>
          </Tooltip>
        </Stack>
      </Toolbar>
    </AppBar>
  )
}
