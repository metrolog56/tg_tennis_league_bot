/**
 * League REST API client. All mutations go through this layer (X-API-Key, Bearer JWT or X-Player-Id).
 * Reads stay via Supabase (anon SELECT).
 */
import { getAuthToken, getAuthPlayerId } from '../auth/telegramAuth'

const baseUrl = () => (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
const apiKey = () => import.meta.env.VITE_API_KEY || ''

function headers(playerId = null) {
  const h = { 'Content-Type': 'application/json' }
  if (apiKey()) h['X-API-Key'] = apiKey()
  const token = getAuthToken()
  if (token) {
    h['Authorization'] = `Bearer ${token}`
    const authPlayerId = getAuthPlayerId()
    if (authPlayerId) h['X-Player-Id'] = String(authPlayerId)
  } else if (playerId) {
    h['X-Player-Id'] = String(playerId)
  }
  return h
}

async function checkResponse(res) {
  if (!res.ok) {
    const text = await res.text()
    let detail = text
    try {
      const j = JSON.parse(text)
      if (j.detail) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail)
    } catch (_) {}
    throw new Error(detail || `HTTP ${res.status}`)
  }
}

export async function saveClientSession(clientData, playerId = null, platform = null) {
  const url = baseUrl()
  if (!url) return new Error('VITE_API_URL not set')
  const res = await fetch(`${url}/client-sessions`, {
    method: 'POST',
    headers: headers(playerId),
    body: JSON.stringify({
      ...clientData,
      platform,
      player_id: playerId || undefined,
    }),
  })
  await checkResponse(res)
  return null
}

export async function updatePlayerName(playerId, newName) {
  const url = baseUrl()
  if (!url) throw new Error('VITE_API_URL not set')
  const name = (newName || '').trim()
  if (!name) throw new Error('Имя не может быть пустым')
  const res = await fetch(`${url}/players/${playerId}`, {
    method: 'PATCH',
    headers: headers(playerId),
    body: JSON.stringify({ name }),
  })
  await checkResponse(res)
  return res.json()
}

export async function submitMatchForConfirmation(divisionId, player1Id, player2Id, sets1, sets2, submittedBy) {
  const url = baseUrl()
  if (!url) throw new Error('VITE_API_URL not set')
  const res = await fetch(`${url}/matches/submit-for-confirmation`, {
    method: 'POST',
    headers: headers(submittedBy),
    body: JSON.stringify({
      division_id: divisionId,
      player1_id: player1Id,
      player2_id: player2Id,
      sets_player1: Number(sets1) || 0,
      sets_player2: Number(sets2) || 0,
      submitted_by: submittedBy,
    }),
  })
  await checkResponse(res)
  const data = await res.json()
  if (data?.id) notifyPending(data.id, submittedBy)
  return data
}

export async function confirmMatchResult(matchId, confirmedByPlayerId) {
  const url = baseUrl()
  if (!url) throw new Error('VITE_API_URL not set')
  const res = await fetch(`${url}/matches/${matchId}/confirm`, {
    method: 'POST',
    headers: headers(confirmedByPlayerId),
    body: JSON.stringify({ confirmed_by_player_id: confirmedByPlayerId }),
  })
  await checkResponse(res)
}

export async function rejectMatchResult(matchId, rejectedByPlayerId) {
  const url = baseUrl()
  if (!url) throw new Error('VITE_API_URL not set')
  const res = await fetch(`${url}/matches/${matchId}/reject`, {
    method: 'POST',
    headers: headers(rejectedByPlayerId),
    body: JSON.stringify({ rejected_by_player_id: rejectedByPlayerId }),
  })
  await checkResponse(res)
}

export function notifyPending(matchId, playerId) {
  const url = baseUrl()
  if (!url || !matchId) return
  fetch(`${url}/matches/${matchId}/notify-pending`, {
    method: 'POST',
    headers: headers(playerId),
  }).catch(() => {})
}
