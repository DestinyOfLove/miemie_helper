'use client'

import WarningAmberRoundedIcon from '@mui/icons-material/WarningAmberRounded'
import { Alert, AlertTitle, Box, Stack, Typography } from '@mui/material'
import { useRuntimeCapabilities } from './RuntimeCapabilitiesProvider'

export function GlobalRuntimeAlert() {
  const { capabilities } = useRuntimeCapabilities()

  if (!capabilities || capabilities.libreoffice_available) return null

  return (
    <Box sx={{ px: { xs: 2, md: 3 }, pt: 2 }}>
      <Alert
        severity="warning"
        variant="filled"
        icon={<WarningAmberRoundedIcon fontSize="inherit" />}
        sx={{
          borderRadius: '22px',
          alignItems: 'flex-start',
          boxShadow: theme => theme.shadows[4],
        }}
      >
        <AlertTitle sx={{ fontWeight: 700 }}>未检测到 LibreOffice</AlertTitle>
        <Typography variant="body2" sx={{ mb: 1 }}>
          .doc/.wps 文件目前无法提取文本，也不会进入全文检索结果。安装 LibreOffice 后重启应用即可恢复完整能力。
        </Typography>
        <Stack spacing={0.5}>
          {capabilities.unsupported_effects.map(effect => (
            <Typography key={effect} variant="body2">
              • {effect}
            </Typography>
          ))}
        </Stack>
      </Alert>
    </Box>
  )
}
