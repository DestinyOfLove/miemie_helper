'use client'

import Link from 'next/link'
import SearchRoundedIcon from '@mui/icons-material/SearchRounded'
import AutoAwesomeRoundedIcon from '@mui/icons-material/AutoAwesomeRounded'
import ArrowForwardRoundedIcon from '@mui/icons-material/ArrowForwardRounded'
import { Box, Button, Card, CardContent, Chip, Grid, Stack, Typography } from '@mui/material'
import { alpha } from '@mui/material/styles'
import { PageContainer } from '../components/layout/PageContainer'

const tools = [
  {
    icon: <SearchRoundedIcon />,
    title: '文档搜索',
    desc: '在本地公文资料中快速检索关键词，按正文、标题或全文范围定位信息。',
    sub: '正文 / 标题 / 全文',
    to: '/search',
  },
  {
    icon: <AutoAwesomeRoundedIcon />,
    title: '更多工具',
    desc: '当前版本聚焦文档搜索。后续能力会在稳定的桌面工作流基础上逐步扩展。',
    sub: '规划中',
    to: null,
  },
]

export function HomePage() {
  return (
    <PageContainer
      maxWidth="lg"
      title="工具集"
      description="当前工作区聚焦文档搜索。所有内容本地处理，不上传任何文件。"
    >
      <Box
        sx={{
          p: { xs: 3, md: 4 },
          borderRadius: '32px',
          background: theme => `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.14)}, ${alpha(theme.palette.secondary.main, 0.08)})`,
          border: '1px solid',
          borderColor: 'divider',
          maxWidth: 980,
        }}
      >
        <Stack spacing={2.5}>
          <Chip label="桌面工作流" color="primary" sx={{ alignSelf: 'flex-start' }} />
          <Typography variant="h2" sx={{ maxWidth: 680 }}>
            为高频文档检索提供更快、更清晰的桌面操作入口。
          </Typography>
          <Typography color="text.secondary" sx={{ maxWidth: 720 }}>
            现在先把搜索体验打磨到稳定、现代、易用。后续能力会在这个基础上再扩展，而不是继续堆叠旧式后台入口。
          </Typography>
          <Box>
            <Button
              component={Link}
              href="/search"
              variant="contained"
              endIcon={<ArrowForwardRoundedIcon />}
              size="large"
            >
              进入文档搜索
            </Button>
          </Box>
        </Stack>
      </Box>

      <Grid container spacing={3}>
        {tools.map((tool) => (
          <Grid key={tool.title} size={{ xs: 12, md: 6 }}>
            <Card
              variant="outlined"
              sx={{
                height: '100%',
                opacity: tool.to ? 1 : 0.72,
              }}
            >
              <CardContent sx={{ p: 3.5 }}>
                <Stack spacing={2}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: '18px',
                      display: 'grid',
                      placeItems: 'center',
                      bgcolor: 'action.hover',
                      color: 'primary.main',
                    }}
                  >
                    {tool.icon}
                  </Box>
                  <Stack spacing={1}>
                    <Typography variant="h6">{tool.title}</Typography>
                    <Typography color="text.secondary">{tool.desc}</Typography>
                  </Stack>
                  {tool.sub && (
                    <Chip label={tool.sub} variant="outlined" sx={{ alignSelf: 'flex-start' }} />
                  )}
                  {tool.to && (
                    <Button component={Link} href={tool.to} variant="text" sx={{ alignSelf: 'flex-start', px: 0 }}>
                      打开
                    </Button>
                  )}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </PageContainer>
  )
}
