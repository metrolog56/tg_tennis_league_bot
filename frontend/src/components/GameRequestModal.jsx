import { useState } from 'react'
import { Dialog } from '@headlessui/react'
import { createGameRequest } from '../api/supabase'
import { RESPECT_EMOJI } from '../constants/respect'

export default function GameRequestModal({
  currentPlayerId,
  opponents,
  existingMatchesByOpponentId,
  seasonId,
  onClose,
  onSaved,
}) {
  const [mode, setMode] = useState('open') // 'challenge' | 'open'
  const [selectedOpponent, setSelectedOpponent] = useState(null)
  const [openType, setOpenType] = useState('open_league')
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  // Only show opponents who haven't had a played match yet
  const challengeOpponents = (opponents || []).filter((p) => {
    return (existingMatchesByOpponentId || {})[p.id] !== 'played'
  })

  const handleSubmit = async () => {
    setError('')
    setSaving(true)
    try {
      if (mode === 'challenge') {
        if (!selectedOpponent) {
          setError('Выберите соперника')
          setSaving(false)
          return
        }
        await createGameRequest(
          'division_challenge',
          selectedOpponent.id,
          message.trim() || null,
          seasonId,
          currentPlayerId,
        )
        onSaved?.({ type: 'challenge', opponent: selectedOpponent })
      } else {
        await createGameRequest(
          openType,
          null,
          message.trim() || null,
          seasonId,
          currentPlayerId,
        )
        onSaved?.({ type: 'open', subtype: openType })
      }
      onClose?.()
    } catch (e) {
      setError(e?.message || 'Ошибка')
    } finally {
      setSaving(false)
    }
  }

  const tabStyle = (active) =>
    active
      ? {
          background: 'var(--tg-theme-button-color)',
          color: 'var(--tg-theme-button-text-color)',
          borderColor: 'var(--tg-theme-button-color)',
        }
      : { borderColor: 'var(--tg-theme-hint-color)' }

  return (
    <Dialog open onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/50" aria-hidden="true" />
      <div className="fixed inset-0 flex items-center justify-center p-3 min-w-[320px]">
        <Dialog.Panel
          className="glass glass-modal w-full max-w-md max-h-[90vh] overflow-y-auto rounded-2xl p-4 shadow-xl"
          style={{ color: 'var(--tg-theme-text-color)' }}
        >
          <Dialog.Title className="text-lg font-bold mb-3">
            🎾 Ищу игру
          </Dialog.Title>

          {/* Mode tabs */}
          <div className="flex gap-2 mb-4">
            <button
              type="button"
              onClick={() => { setMode('challenge'); setError('') }}
              className="flex-1 py-2 rounded-lg text-sm font-medium border"
              style={tabStyle(mode === 'challenge')}
            >
              Вызов из дивизиона
            </button>
            <button
              type="button"
              onClick={() => { setMode('open'); setError('') }}
              className="flex-1 py-2 rounded-lg text-sm font-medium border"
              style={tabStyle(mode === 'open')}
            >
              Открытый запрос
            </button>
          </div>

          {/* Challenge mode: pick an unplayed division opponent */}
          {mode === 'challenge' && (
            <>
              <p className="text-sm text-[var(--tg-theme-hint-color)] mb-2">
                Выберите соперника из дивизиона:
              </p>
              {challengeOpponents.length === 0 ? (
                <p className="text-sm text-[var(--tg-theme-hint-color)] mb-4">
                  Нет доступных соперников для вызова.
                </p>
              ) : (
                <div className="grid grid-cols-2 gap-2 mb-4">
                  {challengeOpponents.map((p) => {
                    const isSelected = selectedOpponent?.id === p.id
                    return (
                      <button
                        key={p.id}
                        type="button"
                        onClick={() => setSelectedOpponent(p)}
                        className="py-2.5 px-3 rounded-lg text-left text-sm font-medium border truncate"
                        style={{
                          borderColor: isSelected ? 'var(--tg-theme-button-color)' : 'var(--tg-theme-hint-color)',
                          background: isSelected ? 'var(--tg-theme-button-color)' : 'var(--tg-theme-secondary-bg-color)',
                          color: isSelected ? 'var(--tg-theme-button-text-color)' : undefined,
                        }}
                        title={p.name || '—'}
                      >
                        {p.name || '—'}
                      </button>
                    )
                  })}
                </div>
              )}
            </>
          )}

          {/* Open mode: choose league or casual */}
          {mode === 'open' && (
            <>
              <p className="text-sm text-[var(--tg-theme-hint-color)] mb-2">
                Тип игры:
              </p>
              <div className="flex gap-2 mb-4">
                {[
                  { value: 'open_league', label: 'Матч лиги' },
                  { value: 'open_casual', label: 'Просто поиграть' },
                ].map(({ value, label }) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => setOpenType(value)}
                    className="flex-1 py-2 rounded-lg text-sm font-medium border"
                    style={tabStyle(openType === value)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </>
          )}

          {/* Optional message */}
          <div className="mb-4">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              maxLength={100}
              placeholder="Комментарий (необязательно): время, место..."
              rows={2}
              className="w-full px-3 py-2 rounded-xl border border-[var(--tg-theme-hint-color)]/40 bg-[var(--tg-theme-bg-color)] text-sm resize-none"
            />
          </div>

          {error && (
            <p className="text-red-500 text-sm mb-3">{error}</p>
          )}

          <div className="flex gap-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-3 rounded-xl border border-[var(--tg-theme-hint-color)]/40"
            >
              Отмена
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={saving || (mode === 'challenge' && !selectedOpponent) || (mode === 'challenge' && challengeOpponents.length === 0)}
              className="flex-1 py-3 rounded-xl font-medium text-white disabled:opacity-50"
              style={{ background: 'var(--tg-theme-button-color)', color: 'var(--tg-theme-button-text-color)' }}
            >
              {saving
                ? 'Отправка...'
                : mode === 'challenge'
                  ? `Вызвать ${RESPECT_EMOJI}`
                  : 'Отправить запрос'}
            </button>
          </div>
        </Dialog.Panel>
      </div>
    </Dialog>
  )
}
