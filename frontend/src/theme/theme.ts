import { alpha, createTheme, type PaletteMode } from '@mui/material/styles'

export function buildAppTheme(mode: PaletteMode) {
  const isLight = mode === 'light'

  return createTheme({
    palette: {
      mode,
      primary: {
        main: isLight ? '#1557B0' : '#7FB3FF',
        light: isLight ? '#4A7FD6' : '#A9CCFF',
        dark: isLight ? '#0D3C7C' : '#4A88D9',
      },
      secondary: {
        main: isLight ? '#2B6F77' : '#7DC2CC',
      },
      success: {
        main: isLight ? '#2E7D32' : '#7DDC86',
      },
      warning: {
        main: isLight ? '#C77700' : '#FFC266',
      },
      error: {
        main: isLight ? '#C1443C' : '#FF8C85',
      },
      background: {
        default: isLight ? '#F3F6FA' : '#0F1722',
        paper: isLight ? '#FCFDFE' : '#16202D',
      },
      text: {
        primary: isLight ? '#122033' : '#E8EEF6',
        secondary: isLight ? '#536274' : '#A9B6C7',
      },
      divider: isLight ? '#D6DFEA' : '#2C3A4D',
    },
    shape: {
      borderRadius: 18,
    },
    typography: {
      fontFamily: [
        '-apple-system',
        'BlinkMacSystemFont',
        '"Segoe UI"',
        '"PingFang SC"',
        '"Noto Sans CJK SC"',
        'sans-serif',
      ].join(','),
      h1: {
        fontSize: '2rem',
        fontWeight: 700,
        letterSpacing: '-0.02em',
      },
      h2: {
        fontSize: '1.5rem',
        fontWeight: 700,
        letterSpacing: '-0.02em',
      },
      h6: {
        fontWeight: 700,
      },
      button: {
        textTransform: 'none',
        fontWeight: 600,
      },
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            backgroundImage: isLight
              ? 'radial-gradient(circle at top, rgba(21,87,176,0.08), transparent 28%)'
              : 'radial-gradient(circle at top, rgba(127,179,255,0.16), transparent 32%)',
          },
          '::selection': {
            backgroundColor: isLight ? alpha('#1557B0', 0.18) : alpha('#7FB3FF', 0.3),
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
          },
        },
      },
      MuiButton: {
        defaultProps: {
          disableElevation: true,
        },
        styleOverrides: {
          root: {
            borderRadius: 14,
            paddingInline: 18,
          },
        },
      },
      MuiOutlinedInput: {
        styleOverrides: {
          root: {
            borderRadius: 14,
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: 999,
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 24,
          },
        },
      },
    },
  })
}
