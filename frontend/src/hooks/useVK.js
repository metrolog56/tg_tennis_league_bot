import { useState, useEffect } from 'react'

let vkBridge = null
let vkBridgePromise = null

function loadVKBridge() {
  if (vkBridgePromise) return vkBridgePromise
  vkBridgePromise = import('@vkontakte/vk-bridge').then((mod) => {
    vkBridge = mod.default
    return vkBridge
  })
  return vkBridgePromise
}

function isVKEnvironment() {
  if (typeof window === 'undefined') return false
  const params = new URLSearchParams(window.location.search)
  return params.has('vk_user_id') || params.has('vk_app_id') || params.has('sign')
}

export function useVK() {
  const [user, setUser] = useState(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    if (!isVKEnvironment()) {
      setReady(true)
      return
    }

    let cancelled = false
    loadVKBridge()
      .then((bridge) => {
        if (cancelled) return
        return bridge.send('VKWebAppInit').then(() => bridge)
      })
      .then((bridge) => {
        if (cancelled || !bridge) return
        return bridge.send('VKWebAppGetUserInfo')
      })
      .then((userData) => {
        if (cancelled) return
        if (userData) setUser(userData)
        setReady(true)
      })
      .catch(() => {
        if (!cancelled) setReady(true)
      })

    return () => { cancelled = true }
  }, [])

  return {
    user,
    ready,
    vkUserId: user?.id ?? null,
    firstName: user?.first_name ?? '',
    lastName: user?.last_name ?? '',
    isVK: isVKEnvironment(),
  }
}
