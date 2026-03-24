/**
 * Telegram auth: exchange initData for JWT and store for API calls.
 * Used by leagueApi.js and by app init (useAuth / App.jsx).
 */
let authToken = null
let authPlayerId = null
let authTelegramId = null

export function getAuthToken() {
  return authToken
}

export function getAuthPlayerId() {
  return authPlayerId
}

export function getAuthTelegramId() {
  return authTelegramId
}

export function setAuth(token, playerId, telegramId) {
  authToken = token
  authPlayerId = playerId ?? null
  authTelegramId = telegramId ?? null
}

export function clearAuth() {
  authToken = null
  authPlayerId = null
  authTelegramId = null
}

const baseUrl = () => (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
const apiKey = () => import.meta.env.VITE_API_KEY || ''

/**
 * Exchange raw initData for JWT. On success sets auth store and returns { player_id, telegram_id }.
 * On failure returns null and does not set auth.
 */
export async function exchangeInitDataForToken(initData) {
  const url = baseUrl()
  if (!url || !(initData || '').trim()) return null
  const res = await fetch(`${url}/auth/telegram`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(apiKey() ? { 'X-API-Key': apiKey() } : {}),
    },
    body: JSON.stringify({ init_data: initData.trim() }),
  })
  if (!res.ok) return null
  const data = await res.json().catch(() => null)
  if (!data?.access_token) return null
  setAuth(data.access_token, data.player_id ?? null, data.telegram_id ?? null)
  return { player_id: data.player_id ?? null, telegram_id: data.telegram_id ?? null }
}
