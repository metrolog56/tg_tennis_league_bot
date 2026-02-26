import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  getMatchById,
  confirmMatchResult,
  rejectMatchResult,
  getPlayerByTelegramId,
} from '../api/supabase'

export default function ConfirmMatch({ telegramId }) {
  const { matchId } = useParams()
  const navigate = useNavigate()
  const [match, setMatch] = useState(null)
  const [currentPlayerId, setCurrentPlayerId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [action, setAction] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      if (!matchId || !telegramId) {
        setLoading(false)
        return
      }
      try {
        const [matchData, player] = await Promise.all([
          getMatchById(matchId),
          getPlayerByTelegramId(telegramId),
        ])
        if (cancelled) return
        setMatch(matchData)
        setCurrentPlayerId(player?.id ?? null)
      } catch (e) {
        if (!cancelled) setError(e?.message || 'Ошибка загрузки')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [matchId, telegramId])

  if (!telegramId) {
    return (
      <div className="p-4 min-w-[320px]">
        <p className="text-[var(--tg-theme-hint-color)]">Откройте приложение из Telegram.</p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="p-4 min-w-[320px]">
        <p className="text-[var(--tg-theme-hint-color)]">Загрузка...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 min-w-[320px]">
        <p className="text-red-500">{error}</p>
        <button
          type="button"
          onClick={() => navigate('/')}
          className="mt-4 py-2 px-4 rounded-xl border border-[var(--tg-theme-hint-color)]/40"
        >
          На главную
        </button>
      </div>
    )
  }

  if (!match || match.status !== 'pending_confirm') {
    return (
      <div className="p-4 min-w-[320px]">
        <p className="text-[var(--tg-theme-hint-color)]">Матч не найден или уже обработан.</p>
        <button
          type="button"
          onClick={() => navigate('/')}
          className="mt-4 py-2 px-4 rounded-xl border border-[var(--tg-theme-hint-color)]/40"
        >
          На главную
        </button>
      </div>
    )
  }

  const isParticipant = currentPlayerId === match.player1_id || currentPlayerId === match.player2_id
  const isOpponent = isParticipant && currentPlayerId !== match.submitted_by
  const submitterId = match.submitted_by
  const submitterName =
    (match.player1_id === submitterId ? match.player1?.name : match.player2?.name) || 'Соперник'
  const mySets = currentPlayerId === match.player1_id ? match.sets_player1 : match.sets_player2
  const oppSets = currentPlayerId === match.player1_id ? match.sets_player2 : match.sets_player1

  if (!isOpponent) {
    return (
      <div className="p-4 min-w-[320px]">
        <p className="text-[var(--tg-theme-hint-color)]">Подтвердить результат может только соперник.</p>
        <button
          type="button"
          onClick={() => navigate('/')}
          className="mt-4 py-2 px-4 rounded-xl border border-[var(--tg-theme-hint-color)]/40"
        >
          На главную
        </button>
      </div>
    )
  }

  const handleConfirm = async () => {
    setError('')
    setAction('confirm')
    try {
      await confirmMatchResult(matchId, currentPlayerId)
      navigate('/', { state: { message: 'Результат подтверждён.' } })
    } catch (e) {
      setError(e?.message || 'Ошибка')
      setAction(null)
    }
  }

  const handleReject = async () => {
    setError('')
    setAction('reject')
    try {
      await rejectMatchResult(matchId, currentPlayerId)
      navigate('/', { state: { message: 'Результат отклонён.' } })
    } catch (e) {
      setError(e?.message || 'Ошибка')
      setAction(null)
    }
  }

  return (
    <div className="p-4 min-w-[320px] max-w-lg mx-auto">
      <h1 className="text-xl font-bold mb-4">Подтверждение результата матча</h1>
      <p className="text-[var(--tg-theme-text-color)] mb-2">
        <strong>{submitterName}</strong> внёс результат матча:
      </p>
      <p className="text-lg font-medium mb-2">
        Вы — {mySets}, {submitterName} — {oppSets}
      </p>
      <p className="text-sm text-[var(--tg-theme-hint-color)] mb-6">
        Подтвердите, если счёт верный, или отклоните.
      </p>

      {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

      <div className="flex gap-3">
        <button
          type="button"
          onClick={handleReject}
          disabled={!!action}
          className="flex-1 py-3 rounded-xl border border-[var(--tg-theme-hint-color)]/40 disabled:opacity-50"
        >
          {action === 'reject' ? 'Отправка...' : 'Отклонить'}
        </button>
        <button
          type="button"
          onClick={handleConfirm}
          disabled={!!action}
          className="flex-1 py-3 rounded-xl font-medium text-white disabled:opacity-50"
          style={{
            background: 'var(--tg-theme-button-color)',
            color: 'var(--tg-theme-button-text-color)',
          }}
        >
          {action === 'confirm' ? 'Отправка...' : 'Подтвердить'}
        </button>
      </div>
    </div>
  )
}
