import { useState, useEffect } from 'react'
import {
  exchangeInitDataForToken,
  getAuthPlayerId,
  getAuthTelegramId,
  getAuthToken,
} from '../auth/telegramAuth'

/**
 * Exchange Telegram initData for JWT on load and expose validated identity.
 * Use playerId/telegramId from this hook for "current user" (validated on server).
 */
export function useAuth() {
  const [ready, setReady] = useState(false)
  const [playerId, setPlayerId] = useState(getAuthPlayerId())
  const [telegramId, setTelegramId] = useState(getAuthTelegramId())

  useEffect(() => {
    let cancelled = false
    const webApp = window.Telegram?.WebApp
    const initData = webApp?.initData?.trim?.()
    if (!initData) {
      setReady(true)
      return
    }
    exchangeInitDataForToken(initData)
      .then((result) => {
        if (cancelled) return
        if (result) {
          setPlayerId(getAuthPlayerId())
          setTelegramId(getAuthTelegramId())
        }
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setReady(true)
      })
    return () => { cancelled = true }
  }, [])

  return {
    ready,
    token: getAuthToken(),
    playerId: playerId ?? getAuthPlayerId(),
    telegramId: telegramId ?? getAuthTelegramId(),
  }
}
