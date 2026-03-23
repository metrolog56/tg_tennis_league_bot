import { createClient } from '@supabase/supabase-js'

/**
 * Unified auth store:
 * - telegram: exchange initData -> API JWT
 * - web: Supabase magic link -> API JWT
 */
let authToken = null
let authPlayerId = null
let authTelegramId = null
let authUserId = null
let authType = null

const webStorageKey = 'web-auth-email'

export function getAuthToken() {
  return authToken
}

export function getAuthPlayerId() {
  return authPlayerId
}

export function getAuthTelegramId() {
  return authTelegramId
}

export function getAuthUserId() {
  return authUserId
}

export function getAuthType() {
  return authType
}

export function setAuth(token, playerId, telegramId, userId = null, type = null) {
  authToken = token
  authPlayerId = playerId ?? null
  authTelegramId = telegramId ?? null
  authUserId = userId ?? null
  authType = type ?? null
}

export function clearAuth() {
  authToken = null
  authPlayerId = null
  authTelegramId = null
  authUserId = null
  authType = null
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
  setAuth(
    data.access_token,
    data.player_id ?? null,
    data.telegram_id ?? null,
    data.auth_user_id ?? null,
    data.auth_type ?? 'telegram',
  )
  return { player_id: data.player_id ?? null, telegram_id: data.telegram_id ?? null }
}

function webSupabaseClient() {
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
  const supabaseKey = import.meta.env.VITE_SUPABASE_KEY || import.meta.env.VITE_SUPABASE_ANON_KEY
  if (!supabaseUrl || !supabaseKey) return null
  return createClient(supabaseUrl, supabaseKey)
}

export async function requestMagicLink(email) {
  const sb = webSupabaseClient()
  const cleanEmail = (email || '').trim().toLowerCase()
  if (!sb || !cleanEmail) return { error: 'Некорректный email или Supabase не настроен' }
  try {
    window.localStorage.setItem(webStorageKey, cleanEmail)
  } catch (_) {}
  // Use Vite BASE_URL so GitHub Pages subpath deployments redirect correctly.
  const redirectTo = new URL(import.meta.env.BASE_URL || '/', window.location.origin).toString()
  const { error } = await sb.auth.signInWithOtp({
    email: cleanEmail,
    options: { emailRedirectTo: redirectTo },
  })
  if (error) return { error: error.message || 'Не удалось отправить ссылку' }
  return { error: null }
}

export async function exchangeWebSessionForToken() {
  const url = baseUrl()
  if (!url) return null
  const sb = webSupabaseClient()
  if (!sb) return null
  const { data, error } = await sb.auth.getSession()
  if (error || !data?.session?.access_token) return null
  const res = await fetch(`${url}/auth/web`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(apiKey() ? { 'X-API-Key': apiKey() } : {}),
    },
    body: JSON.stringify({ access_token: data.session.access_token }),
  })
  if (!res.ok) return null
  const payload = await res.json().catch(() => null)
  if (!payload?.access_token) return null
  setAuth(
    payload.access_token,
    payload.player_id ?? null,
    payload.telegram_id ?? null,
    payload.auth_user_id ?? null,
    payload.auth_type ?? 'web',
  )
  return payload
}

export async function signOutWeb() {
  const sb = webSupabaseClient()
  clearAuth()
  if (!sb) return
  await sb.auth.signOut()
}
