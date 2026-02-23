import { useState, useEffect, useCallback } from 'react'

/**
 * Хук для работы с window.Telegram.WebApp
 */
export function useTelegram() {
  const [tg, setTg] = useState(null)
  const [user, setUser] = useState(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const webApp = window.Telegram?.WebApp
    if (!webApp) {
      setReady(true)
      return
    }
    webApp.ready()
    setTg(webApp)
    setUser(webApp.initDataUnsafe?.user ?? null)
    setReady(true)
  }, [])

  const onClose = useCallback(() => {
    if (tg?.close) tg.close()
  }, [tg])

  const onMainButton = useCallback((callback) => {
    if (!tg?.MainButton) return
    tg.MainButton.onClick(callback)
    return () => tg.MainButton?.offClick(callback)
  }, [tg])

  const setMainButton = useCallback(({ text, visible = true, onClick, progress }) => {
    if (!tg?.MainButton) return
    if (visible) {
      tg.MainButton.setText(text ?? '')
      tg.MainButton.show()
      if (onClick) tg.MainButton.onClick(onClick)
      if (progress) tg.MainButton.showProgress()
      else tg.MainButton.hideProgress()
    } else {
      tg.MainButton.hide()
    }
  }, [tg])

  return {
    tg,
    user,
    ready,
    telegramId: user?.id ?? null,
    username: user?.username ?? null,
    firstName: user?.first_name ?? '',
    lastName: user?.last_name ?? '',
    onClose,
    onMainButton,
    setMainButton,
  }
}
