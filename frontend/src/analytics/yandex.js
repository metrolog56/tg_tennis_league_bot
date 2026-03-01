const COUNTER_ID = import.meta.env.VITE_YM_COUNTER_ID

export function initYandexMetrika() {
  if (!COUNTER_ID || typeof window === 'undefined' || !window.ym) return
  window.ym(COUNTER_ID, 'init', { clickmap: true, trackLinks: true, webvisor: true })
}

export function hitYandexMetrika(url) {
  if (!COUNTER_ID || typeof window === 'undefined' || !window.ym) return
  window.ym(COUNTER_ID, 'hit', url)
}
