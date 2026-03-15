import { useState } from 'react'
import { Dialog } from '@headlessui/react'
import { createGameRequest } from '../api/supabase'

export default function GameRequestModal({
  currentPlayerId,
  seasonId,
  onClose,
  onSaved,
}) {
  const [openType, setOpenType] = useState('open_league')
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async () => {
    setError('')
    setSaving(true)
    try {
      await createGameRequest(
        openType,
        null,
        message.trim() || null,
        seasonId,
        currentPlayerId,
      )
      onSaved?.({ type: 'open', subtype: openType })
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
            Ищу игру
          </Dialog.Title>

          <p className="text-sm font-medium text-[var(--tg-theme-text-color)] mb-2">
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
              disabled={saving}
              className="flex-1 py-3 rounded-xl font-medium text-white disabled:opacity-50"
              style={{ background: 'var(--tg-theme-button-color)', color: 'var(--tg-theme-button-text-color)' }}
            >
              {saving ? 'Отправка...' : 'Отправить запрос'}
            </button>
          </div>
        </Dialog.Panel>
      </div>
    </Dialog>
  )
}
