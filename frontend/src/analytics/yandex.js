const COUNTER_ID = import.meta.env.VITE_YM_COUNTER_ID || '107060791'

export function initYandexMetrika() {
  if (typeof window === 'undefined' || !window.ym) return
  window.ym(COUNTER_ID, 'init', { clickmap: true, trackLinks: true, webvisor: true })
}

export function hitYandexMetrika(url) {
  if (typeof window === 'undefined' || !window.ym) return
  window.ym(COUNTER_ID, 'hit', url || window.location.href || '#/')
}
