import { NavLink } from 'react-router-dom'

export function NavBar() {
  return (
    <nav style={{
      background: '#1976D2',
      color: '#fff',
      padding: '0 24px',
      display: 'flex',
      alignItems: 'center',
      height: 52,
      gap: 32,
      fontSize: 15,
    }}>
      <span style={{ fontWeight: 700, fontSize: 17, marginRight: 16 }}>MieMie Helper</span>
      {[
        { to: '/', label: '首页' },
        { to: '/search', label: '文档搜索' },
        { to: '/archive', label: '归档导出' },
      ].map(({ to, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          style={({ isActive }) => ({
            color: '#fff',
            textDecoration: 'none',
            borderBottom: isActive ? '2px solid #fff' : '2px solid transparent',
            paddingBottom: 2,
            fontWeight: isActive ? 600 : 400,
          })}
        >
          {label}
        </NavLink>
      ))}
    </nav>
  )
}
