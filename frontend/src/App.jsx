import { useEffect, useRef, useState, lazy, Suspense } from 'react'
import { HashRouter, Routes, Route, NavLink, Navigate, useLocation } from 'react-router-dom'
import Home from './pages/Home'
const Rating = lazy(() => import('./pages/Rating'))
const Division = lazy(() => import('./pages/Division'))
const Rules = lazy(() => import('./pages/Rules'))
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

function MetrikaTracker({ homeReady }) {
  const location = useLocation()
  const inited = useRef(false)
  useEffect(() => {
    if (!homeReady) return
    if (!inited.current) {
      initYandexMetrika()
      inited.current = true
    }
    hitYandexMetrika(window.location.href || '#/')
  }, [homeReady, location.pathname, location.search, location.hash])
  return null
}

function App() {
  const { user } = useTelegram()
  const { playerId: authPlayerId, telegramId: authTelegramId } = useAuth()
  const telegramId = authTelegramId ?? user?.id ?? null
  const playerId = authPlayerId ?? null
  const sessionSent = useRef(false)
  const [homeReady, setHomeReady] = useState(false)
  const homeReadyRef = useRef(false)

  const handleHomeReady = () => {
    if (homeReadyRef.current) return
    homeReadyRef.current = true
    setHomeReady(true)
  }

  useEffect(() => {
    if (!homeReady || sessionSent.current) return
    const timeout = setTimeout(() => {
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
    }, 2000)
    return () => clearTimeout(timeout)
  }, [homeReady, telegramId, playerId])

  return (
    <HashRouter>
      <>
        <MetrikaTracker homeReady={homeReady} />
        <Layout>
          <Suspense
            fallback={
              <div className="p-4 min-w-[320px] max-w-lg mx-auto">
                <p className="text-sm text-[var(--tg-theme-hint-color)]">Загрузка...</p>
              </div>
            }
          >
            <Routes>
              <Route index element={<Home telegramId={telegramId} playerId={playerId} onInitialDataLoaded={handleHomeReady} />} />
              <Route path="/rating" element={<Rating telegramId={telegramId} playerId={playerId} />} />
              <Route path="/division" element={<Division telegramId={telegramId} playerId={playerId} />} />
              <Route path="/division/:id" element={<Division telegramId={telegramId} playerId={playerId} />} />
              <Route path="/rules" element={<Rules />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </Layout>
      </>
    </HashRouter>
  )
}

export default App
