import { useEffect, useRef } from 'react'
import { HashRouter, Routes, Route, NavLink, Navigate, useLocation } from 'react-router-dom'
import Home from './pages/Home'
import Rating from './pages/Rating'
import Division from './pages/Division'
import Rules from './pages/Rules'
import { useTelegram } from './hooks/useTelegram'
import { useAuth } from './hooks/useAuth'
import { getCurrentSeason, saveClientSession } from './api/supabase'
import { collectClientData } from './analytics/clientData'
import { initYandexMetrika, hitYandexMetrika } from './analytics/yandex'

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
      className="glass glass-nav flex flex-shrink-0 items-stretch safe-area-pb"
      style={{ minHeight: NAV_HEIGHT }}
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
        background: 'var(--tg-theme-bg-color)',
        color: 'var(--tg-theme-text-color)',
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

function MetrikaTracker() {
  const location = useLocation()
  const inited = useRef(false)
  useEffect(() => {
    if (!inited.current) {
      initYandexMetrika()
      inited.current = true
    }
    hitYandexMetrika(window.location.href || '#/')
  }, [location.pathname, location.search, location.hash])
  return null
}

function App() {
  const { user } = useTelegram()
  const { playerId: authPlayerId, telegramId: authTelegramId } = useAuth()
  const telegramId = authTelegramId ?? user?.id ?? null
  const playerId = authPlayerId ?? null
  const sessionSent = useRef(false)

  useEffect(() => {
    getCurrentSeason().catch(() => {})
  }, [])

  useEffect(() => {
    if (sessionSent.current) return
    sessionSent.current = true
    const platform = telegramId ? 'telegram' : 'web'
    let clientData
    try {
      clientData = collectClientData()
    } catch (e) {
      console.warn('[analytics] collectClientData failed', e)
      return
    }
    console.warn('[analytics] client_sessions sending', platform)
    saveClientSession(clientData, playerId, platform).then((err) => {
      if (err) {
        console.warn('[analytics] client_sessions insert failed', err?.message ?? err)
      } else {
        console.warn('[analytics] client_sessions ok')
      }
    }).catch((e) => {
      console.warn('[analytics] client_sessions error', e)
    })
  }, [telegramId, playerId])

  return (
    <HashRouter>
      <>
        <MetrikaTracker />
        <Layout>
          <Routes>
          <Route index element={<Home telegramId={telegramId} playerId={playerId} />} />
          <Route path="/rating" element={<Rating telegramId={telegramId} playerId={playerId} />} />
          <Route path="/division" element={<Division telegramId={telegramId} playerId={playerId} />} />
          <Route path="/division/:id" element={<Division telegramId={telegramId} playerId={playerId} />} />
          <Route path="/rules" element={<Rules />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </Layout>
      </>
    </HashRouter>
  )
}

export default App
