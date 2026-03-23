import { useState, useEffect } from 'react'
import {
  exchangeInitDataForToken,
  exchangeWebSessionForToken,
  getAuthPlayerId,
  getAuthTelegramId,
  getAuthToken,
  getAuthType,
  getAuthUserId,
} from '../auth/telegramAuth'

/**
 * Exchange Telegram initData for JWT on load and expose validated identity.
 * Use playerId/telegramId from this hook for "current user" (validated on server).
 */
export function useAuth() {
  const [ready, setReady] = useState(false)
  const [playerId, setPlayerId] = useState(getAuthPlayerId())
  const [telegramId, setTelegramId] = useState(getAuthTelegramId())
  const [authType, setAuthType] = useState(getAuthType())
  const [authUserId, setAuthUserId] = useState(getAuthUserId())

  useEffect(() => {
    let cancelled = false
    const webApp = window.Telegram?.WebApp
    const initData = webApp?.initData?.trim?.()
    const run = async () => {
      if (initData) {
        try {
          const result = await exchangeInitDataForToken(initData)
          if (cancelled) return
          if (result) {
            setPlayerId(getAuthPlayerId())
            setTelegramId(getAuthTelegramId())
            setAuthType(getAuthType())
            setAuthUserId(getAuthUserId())
          }
        } catch (_) {
          // ignore auth startup failures
        } finally {
          if (!cancelled) setReady(true)
        }
        return
      }
      try {
        const result = await exchangeWebSessionForToken()
        if (cancelled) return
        if (result) {
          setPlayerId(getAuthPlayerId())
          setTelegramId(getAuthTelegramId())
          setAuthType(getAuthType())
          setAuthUserId(getAuthUserId())
        }
      } catch (_) {
        // ignore auth startup failures
      } finally {
        if (!cancelled) setReady(true)
      }
    }
    run()
    return () => { cancelled = true }
  }, [])

  return {
    ready,
    token: getAuthToken(),
    playerId: playerId ?? getAuthPlayerId(),
    telegramId: telegramId ?? getAuthTelegramId(),
    authType: authType ?? getAuthType(),
    authUserId: authUserId ?? getAuthUserId(),
  }
}
