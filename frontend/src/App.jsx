import { useEffect } from 'react'
import { HashRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import Home from './pages/Home'
import Rating from './pages/Rating'
import Division from './pages/Division'
import Rules from './pages/Rules'
import { usePlatform } from './hooks/usePlatform'
import { getCurrentSeason } from './api/supabase'

const NAV_HEIGHT = 64

function Nav() {
  const link = (path, label, icon) => {
    const to = path === '/' ? '/' : `/${path}`
    return (
      <NavLink
        to={to}
        className={({ isActive: a }) =>
          `flex flex-col items-center justify-center min-w-0 flex-1 py-3 px-2 text-sm transition-colors ${
            a ? 'text-[var(--app-accent)]' : 'text-[var(--app-hint)]'
          }`
        }
        end={path === '/'}
      >
        <span className="text-2xl mb-1">{icon}</span>
        <span>{label}</span>
      </NavLink>
    )
  }
  return (
    <nav
      className="flex flex-shrink-0 items-stretch border-t border-[var(--app-hint)]/20 safe-area-pb"
      style={{ background: 'var(--app-bg)', minHeight: NAV_HEIGHT }}
    >
      {link('/', 'Главная', '🏠')}
      {link('rating', 'Рейтинг', '📊')}
      {link('division', 'Дивизионы', '🏓')}
      {link('rules', 'Правила', '📋')}
    </nav>
  )
}

function Layout({ children }) {
  return (
    <div
      className="min-w-[320px] flex flex-col safe-area-top"
      style={{
        height: '100vh',
        minHeight: '100dvh',
        background: 'var(--app-bg)',
        color: 'var(--app-text)',
      }}
    >
      <main
        className="flex-1 overflow-auto"
        style={{
          minHeight: 0,
          paddingBottom: NAV_HEIGHT + 8,
          paddingTop: 'max(env(safe-area-inset-top, 0px), 8px)',
        }}
      >
        {children}
      </main>
      <Nav />
    </div>
  )
}

function App() {
  const { platform, userId } = usePlatform()

  useEffect(() => {
    getCurrentSeason().catch(() => {})
  }, [])

  return (
    <HashRouter>
      <Layout>
        <Routes>
          <Route index element={<Home platform={platform} platformUserId={userId} />} />
          <Route path="/rating" element={<Rating platform={platform} platformUserId={userId} />} />
          <Route path="/division" element={<Division platform={platform} platformUserId={userId} />} />
          <Route path="/division/:id" element={<Division platform={platform} platformUserId={userId} />} />
          <Route path="/rules" element={<Rules />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </HashRouter>
  )
}

export default App
