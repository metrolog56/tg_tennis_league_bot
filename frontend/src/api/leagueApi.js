/**
 * League REST API client. All mutations go through this layer (X-API-Key, Bearer JWT).
 * Reads stay via Supabase (anon SELECT).
 */
import { getAuthToken } from '../auth/telegramAuth'

const baseUrl = () => (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
const apiKey = () => import.meta.env.VITE_API_KEY || ''

function headers() {
  const h = { 'Content-Type': 'application/json' }
  if (apiKey()) h['X-API-Key'] = apiKey()
  const token = getAuthToken()
  if (token) {
    h['Authorization'] = `Bearer ${token}`
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
    headers: headers(),
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
    headers: headers(),
    body: JSON.stringify({ name }),
  })
  await checkResponse(res)
  return res.json()
}

export async function getMyPlayer() {
  const url = baseUrl()
  if (!url) throw new Error('VITE_API_URL not set')
  const res = await fetch(`${url}/players/me`, {
    headers: headers(),
  })
  await checkResponse(res)
  return res.json()
}

export async function submitMatchForConfirmation(divisionId, player1Id, player2Id, sets1, sets2, submittedBy) {
  const url = baseUrl()
  if (!url) throw new Error('VITE_API_URL not set')
  const res = await fetch(`${url}/matches/submit-for-confirmation`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({
      division_id: divisionId,
      player1_id: player1Id,
      player2_id: player2Id,
      sets_player1: Number(sets1) || 0,
      sets_player2: Number(sets2) || 0,
      submitted_by: submittedBy, // ignored by API in Bearer-only mode (server takes identity from token)
    }),
  })
  await checkResponse(res)
  const data = await res.json()
  if (data?.id) notifyPending(data.id, submittedBy)
  return data
}

export async function confirmMatchResult(matchId, _confirmedByPlayerId) {
  const url = baseUrl()
  if (!url) throw new Error('VITE_API_URL not set')
  const res = await fetch(`${url}/matches/${matchId}/confirm`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ confirmed_by_player_id: confirmedByPlayerId }),
  })
  await checkResponse(res)
}

export async function rejectMatchResult(matchId, _rejectedByPlayerId) {
  const url = baseUrl()
  if (!url) throw new Error('VITE_API_URL not set')
  const res = await fetch(`${url}/matches/${matchId}/reject`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ rejected_by_player_id: rejectedByPlayerId }),
  })
  await checkResponse(res)
}

export function notifyPending(matchId, _playerId) {
  const url = baseUrl()
  if (!url || !matchId) return
  fetch(`${url}/matches/${matchId}/notify-pending`, {
    method: 'POST',
    headers: headers(),
  }).catch(() => {})
}

export async function createGameRequest(type, targetPlayerId, message, seasonId, _playerId) {
  const url = baseUrl()
  if (!url) throw new Error('VITE_API_URL not set')
  const body = { type }
  if (targetPlayerId) body.target_player_id = targetPlayerId
  if (message) body.message = message
  if (seasonId) body.season_id = seasonId
  const res = await fetch(`${url}/game-requests`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify(body),
  })
  await checkResponse(res)
  return res.json()
}

export async function listGameRequests(seasonId, _playerId) {
  const url = baseUrl()
  if (!url) throw new Error('VITE_API_URL not set')
  const params = seasonId ? `?season_id=${encodeURIComponent(seasonId)}` : ''
  const res = await fetch(`${url}/game-requests${params}`, {
    headers: headers(),
  })
  await checkResponse(res)
  return res.json()
}

export async function acceptGameRequest(requestId, _playerId) {
  const url = baseUrl()
  if (!url) throw new Error('VITE_API_URL not set')
  const res = await fetch(`${url}/game-requests/${requestId}/accept`, {
    method: 'POST',
    headers: headers(),
  })
  await checkResponse(res)
  return res.json()
}

export async function cancelGameRequest(requestId, _playerId) {
  const url = baseUrl()
  if (!url) throw new Error('VITE_API_URL not set')
  const res = await fetch(`${url}/game-requests/${requestId}/cancel`, {
    method: 'POST',
    headers: headers(),
  })
  await checkResponse(res)
  return res.json()
}
