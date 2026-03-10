import { useState, useEffect, useCallback } from 'react'
import { listGameRequests, acceptGameRequest, cancelGameRequest } from '../api/leagueApi'
import { RESPECT_EMOJI } from '../constants/respect'

const TYPE_LABEL = {
  open_league: 'Матч лиги',
  open_casual: 'Просто поиграть',
  division_challenge: 'Матч лиги (вызов)',
}

function timeAgo(dateStr) {
  if (!dateStr) return ''
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000)
  if (diff < 60) return 'только что'
  if (diff < 3600) return `${Math.floor(diff / 60)} мин назад`
  if (diff < 86400) return `${Math.floor(diff / 3600)} ч назад`
  return `${Math.floor(diff / 86400)} дн назад`
}

export default function GameRequestFeed({ currentPlayerId, seasonId }) {
  const [data, setData] = useState({ open: [], challenges: [], mine: [] })
  const [loaded, setLoaded] = useState(false)
  const [actionId, setActionId] = useState(null)
  const [feedError, setFeedError] = useState('')

  const load = useCallback(async () => {
    if (!currentPlayerId) return
    try {
      const result = await listGameRequests(seasonId, currentPlayerId)
      setData(result || { open: [], challenges: [], mine: [] })
    } catch {
      // Non-critical: feed silently fails
    } finally {
      setLoaded(true)
    }
  }, [currentPlayerId, seasonId])

  useEffect(() => {
    load()
    const interval = window.setInterval(load, 30000)
    return () => window.clearInterval(interval)
  }, [load])

  const handleAccept = async (requestId) => {
    setActionId(requestId)
    setFeedError('')
    try {
      await acceptGameRequest(requestId, currentPlayerId)
      await load()
    } catch (e) {
      setFeedError(e?.message || 'Ошибка')
    } finally {
      setActionId(null)
    }
  }

  const handleCancel = async (requestId) => {
    setActionId(requestId)
    setFeedError('')
    try {
      await cancelGameRequest(requestId, currentPlayerId)
      await load()
    } catch (e) {
      setFeedError(e?.message || 'Ошибка')
    } finally {
      setActionId(null)
    }
  }

  const { open, challenges, mine } = data
  const hasAny = open.length > 0 || challenges.length > 0 || mine.length > 0

  if (!loaded || !hasAny) return null

  return (
    <div className="mb-4">
      <h2 className="text-base font-bold mb-3">Запросы на игру</h2>

      {feedError && (
        <p className="text-red-500 text-sm mb-2">{feedError}</p>
      )}

      {/* My own active requests */}
      {mine.length > 0 && (
        <div className="mb-3">
          <p className="text-xs text-[var(--tg-theme-hint-color)] mb-2 uppercase tracking-wide font-medium">
            Мои запросы
          </p>
          <ul className="space-y-2">
            {mine.map((req) => (
              <li
                key={req.id}
                className="glass glass-card p-3 rounded-xl flex items-center justify-between gap-2"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium">{TYPE_LABEL[req.type] || req.type}</p>
                  {req.type === 'division_challenge' && req.target?.name && (
                    <p className="text-xs text-[var(--tg-theme-hint-color)]">→ {req.target.name}</p>
                  )}
                  {req.message && (
                    <p className="text-xs text-[var(--tg-theme-hint-color)] truncate">{req.message}</p>
                  )}
                  <p className="text-xs text-[var(--tg-theme-hint-color)]">{timeAgo(req.created_at)}</p>
                </div>
                <button
                  type="button"
                  onClick={() => handleCancel(req.id)}
                  disabled={actionId === req.id}
                  className="flex-shrink-0 py-1.5 px-3 rounded-lg text-sm border border-[var(--tg-theme-hint-color)]/40 disabled:opacity-50"
                >
                  {actionId === req.id ? '...' : 'Отменить'}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Incoming division challenges addressed to me */}
      {challenges.length > 0 && (
        <div className="mb-3">
          <p className="text-xs text-[var(--tg-theme-hint-color)] mb-2 uppercase tracking-wide font-medium">
            Вызовы для вас
          </p>
          <ul className="space-y-2">
            {challenges.map((req) => {
              const name = req.requester?.name || 'Игрок'
              const busy = actionId === req.id
              return (
                <li key={req.id} className="glass glass-card p-3 rounded-xl">
                  <div className="mb-2">
                    <p className="text-sm font-medium">{name}</p>
                    <p className="text-xs text-[var(--tg-theme-hint-color)]">
                      {TYPE_LABEL[req.type]} · {timeAgo(req.created_at)}
                    </p>
                    {req.message && (
                      <p className="text-xs text-[var(--tg-theme-hint-color)] truncate">{req.message}</p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => handleCancel(req.id)}
                      disabled={busy}
                      className="flex-1 py-2 rounded-lg text-sm border border-[var(--tg-theme-hint-color)]/40 disabled:opacity-50"
                    >
                      {busy ? '...' : 'Отклонить'}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleAccept(req.id)}
                      disabled={busy}
                      className="flex-1 py-2 rounded-lg text-sm font-medium text-white disabled:opacity-50"
                      style={{
                        background: 'var(--tg-theme-button-color)',
                        color: 'var(--tg-theme-button-text-color)',
                      }}
                    >
                      {busy ? '...' : `Принять ${RESPECT_EMOJI}`}
                    </button>
                  </div>
                </li>
              )
            })}
          </ul>
        </div>
      )}

      {/* Open requests from other players */}
      {open.length > 0 && (
        <div>
          <p className="text-xs text-[var(--tg-theme-hint-color)] mb-2 uppercase tracking-wide font-medium">
            Ищут игру
          </p>
          <ul className="space-y-2">
            {open.map((req) => {
              const name = req.requester?.name || 'Игрок'
              const busy = actionId === req.id
              return (
                <li
                  key={req.id}
                  className="glass glass-card p-3 rounded-xl flex items-center justify-between gap-2"
                >
                  <div className="min-w-0">
                    <p className="text-sm font-medium">{name}</p>
                    <p className="text-xs text-[var(--tg-theme-hint-color)]">
                      {TYPE_LABEL[req.type]} · {timeAgo(req.created_at)}
                    </p>
                    {req.message && (
                      <p className="text-xs text-[var(--tg-theme-hint-color)] truncate">{req.message}</p>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => handleAccept(req.id)}
                    disabled={busy}
                    className="flex-shrink-0 py-2 px-3 rounded-lg text-sm font-medium text-white disabled:opacity-50"
                    style={{
                      background: 'var(--tg-theme-button-color)',
                      color: 'var(--tg-theme-button-text-color)',
                    }}
                  >
                    {busy ? '...' : RESPECT_EMOJI}
                  </button>
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </div>
  )
}
