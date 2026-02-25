import { HashRouter, Routes, Route, NavLink } from 'react-router-dom'
import Home from './pages/Home'
import Rating from './pages/Rating'
import Division from './pages/Division'
import Rules from './pages/Rules'
import { useTelegram } from './hooks/useTelegram'

const NAV_HEIGHT = 64

function Nav() {
  const link = (path, label, icon) => {
    const to = path === '/' ? '/' : `/${path}`
    return (
      <NavLink
        to={to}
        className={({ isActive: a }) =>
          `flex flex-col items-center justify-center min-w-0 flex-1 py-3 px-2 text-sm transition-colors ${
            a ? 'text-[var(--tg-theme-button-color)]' : 'text-[var(--tg-theme-hint-color)]'
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
      className="flex flex-shrink-0 items-stretch border-t border-[var(--tg-theme-hint-color)]/20 safe-area-pb"
      style={{ background: 'var(--tg-theme-bg-color)', minHeight: NAV_HEIGHT }}
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
      className="min-h-screen min-w-[320px] flex flex-col safe-area-top"
      style={{
        background: 'var(--tg-theme-bg-color)',
        color: 'var(--tg-theme-text-color)',
      }}
    >
      <main
        className="flex-1 overflow-auto"
        style={{
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
  const { user } = useTelegram()
  const telegramId = user?.id ?? null

  return (
    <HashRouter>
      <Layout>
        <Routes>
          <Route index element={<Home telegramId={telegramId} />} />
          <Route path="/rating" element={<Rating telegramId={telegramId} />} />
          <Route path="/division" element={<Division telegramId={telegramId} />} />
          <Route path="/division/:id" element={<Division telegramId={telegramId} />} />
          <Route path="/rules" element={<Rules />} />
        </Routes>
      </Layout>
    </HashRouter>
  )
}

export default App
