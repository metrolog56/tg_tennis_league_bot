import { HashRouter, Routes, Route, NavLink } from 'react-router-dom'
import Home from './pages/Home'
import Rating from './pages/Rating'
import Division from './pages/Division'
import Rules from './pages/Rules'
import { useTelegram } from './hooks/useTelegram'

function Nav() {
  const link = (path, label, icon) => {
    const to = path === '/' ? '/' : `/${path}`
    return (
      <NavLink
        to={to}
        className={({ isActive: a }) =>
          `flex flex-col items-center justify-center min-w-0 flex-1 py-2 px-1 text-xs transition-colors ${
            a ? 'text-[var(--tg-theme-button-color)]' : 'text-[var(--tg-theme-hint-color)]'
          }`
        }
        end={path === '/'}
      >
        <span className="text-lg mb-0.5">{icon}</span>
        <span>{label}</span>
      </NavLink>
    )
  }
  return (
    <nav
      className="flex items-stretch border-t border-[var(--tg-theme-hint-color)]/20 safe-area-pb"
      style={{ background: 'var(--tg-theme-bg-color)' }}
    >
      {link('/', 'Главная', '🏠')}
      {link('rating', 'Рейтинг', '📊')}
      {link('division', 'Дивизион', '🏓')}
      {link('rules', 'Правила', '📋')}
    </nav>
  )
}

function Layout({ children }) {
  return (
    <div
      className="min-h-screen min-w-[320px] flex flex-col"
      style={{
        background: 'var(--tg-theme-bg-color)',
        color: 'var(--tg-theme-text-color)',
      }}
    >
      <main className="flex-1 overflow-auto pb-2">{children}</main>
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
          <Route path="/" element={<Home telegramId={telegramId} />} />
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
