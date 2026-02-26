import { useState } from 'react'
import { Dialog } from '@headlessui/react'
import { submitMatchForConfirmation } from '../api/supabase'
import { previewRatingChange } from '../utils/ratingCalc'

export default function MatchInput({
  divisionId,
  divisionCoef,
  currentPlayerId,
  currentPlayerRating,
  opponents,
  existingMatchesByOpponentId = {},
  onClose,
  onSaved,
}) {
  const [selectedOpponent, setSelectedOpponent] = useState(null)
  const [scoreChoice, setScoreChoice] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const opponentList = (opponents || []).filter((p) => {
    const status = (existingMatchesByOpponentId || {})[p.id]
    return status !== 'played' && status !== 'pending_confirm'
  })
  const alreadyPlayedWithSelected = selectedOpponent && (existingMatchesByOpponentId || {})[selectedOpponent.id] === 'played'
  const myRating = Number(currentPlayerRating) || 100
  const oppRating = Number(selectedOpponent?.rating) || 100

  let preview = null
  if (scoreChoice && selectedOpponent) {
    const [mySets, oppSets] = scoreChoice
    const result = previewRatingChange(myRating, oppRating, mySets, oppSets, divisionCoef)
    if (result) {
      preview = {
        text: `${mySets}:${oppSets}`,
        myDelta: result.myDelta,
        newRating: result.newRating,
      }
    }
  }

  const handleConfirm = async () => {
    if (!selectedOpponent || !scoreChoice) return
    setError('')
    setSaving(true)
    try {
      const [sets1, sets2] = scoreChoice
      await submitMatchForConfirmation(
        divisionId,
        currentPlayerId,
        selectedOpponent.id,
        sets1,
        sets2,
        currentPlayerId
      )
      const opponentName = selectedOpponent.name || 'соперник'
      onSaved?.(opponentName)
      onClose?.()
    } catch (e) {
      setError(e?.message || 'Ошибка сохранения')
    } finally {
      setSaving(false)
    }
  }

  const scoreOptionsWin = [[3, 0], [3, 1], [3, 2]]
  const scoreOptionsLose = [[0, 3], [1, 3], [2, 3]]

  return (
    <Dialog open onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/50" aria-hidden="true" />
      <div className="fixed inset-0 flex items-center justify-center p-3 min-w-[320px]">
        <Dialog.Panel
          className="w-full max-w-md max-h-[90vh] overflow-y-auto rounded-2xl p-4 shadow-xl"
          style={{
            background: 'var(--tg-theme-bg-color)',
            color: 'var(--tg-theme-text-color)',
          }}
        >
          <Dialog.Title className="text-lg font-bold mb-3">
            Внести результат матча
          </Dialog.Title>

          {opponentList.length === 0 ? (
            <p className="text-[var(--tg-theme-hint-color)] mb-4">Все матчи с соперниками уже внесены.</p>
          ) : (
          <>
          <p className="text-sm font-medium mb-2 text-[var(--tg-theme-hint-color)]">
            Выберите соперника
          </p>
          <div className="grid grid-cols-2 gap-2 mb-4">
            {opponentList.map((p) => {
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
          {alreadyPlayedWithSelected && (
            <p className="text-amber-600 text-sm mb-2">Матч с этим соперником уже внесён. Выберите другого.</p>
          )}

          {selectedOpponent && !alreadyPlayedWithSelected && (
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2 text-[var(--tg-theme-hint-color)]">
                Счёт (вы — соперник)
              </label>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <p className="text-xs mb-1 opacity-80">Вы победили</p>
                  <div className="flex gap-1 flex-wrap">
                    {scoreOptionsWin.map(([a, b]) => (
                      <button
                        key={`${a}-${b}`}
                        type="button"
                        onClick={() => setScoreChoice([a, b])}
                        className={`py-2 px-3 rounded-lg text-sm font-medium border ${
                          scoreChoice?.[0] === a && scoreChoice?.[1] === b
                            ? 'border-[var(--tg-theme-button-color)] text-[var(--tg-theme-button-color)]'
                            : 'border-[var(--tg-theme-hint-color)]/40'
                        }`}
                        style={{
                          background: scoreChoice?.[0] === a && scoreChoice?.[1] === b
                            ? 'color: var(--tg-theme-button-color); border-color: var(--tg-theme-button-color);'
                            : undefined,
                        }}
                      >
                        {a}:{b}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs mb-1 opacity-80">Вы проиграли</p>
                  <div className="flex gap-1 flex-wrap">
                    {scoreOptionsLose.map(([a, b]) => (
                      <button
                        key={`${a}-${b}`}
                        type="button"
                        onClick={() => setScoreChoice([a, b])}
                        className={`py-2 px-3 rounded-lg text-sm font-medium border ${
                          scoreChoice?.[0] === a && scoreChoice?.[1] === b
                            ? 'border-[var(--tg-theme-button-color)]'
                            : 'border-[var(--tg-theme-hint-color)]/40'
                        }`}
                      >
                        {a}:{b}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {preview && !alreadyPlayedWithSelected && (
            <div
              className="mb-4 p-3 rounded-lg text-sm"
              style={{ background: 'var(--tg-theme-secondary-bg-color)' }}
            >
              <p className="font-medium">Превью</p>
              <p>Счёт: {preview.text}</p>
              <p>
                Изменение рейтинга: {preview.myDelta >= 0 ? '+' : ''}{preview.myDelta.toFixed(2)} → {preview.newRating.toFixed(2)}
              </p>
            </div>
          )}

          {error && (
            <p className="text-red-500 text-sm mb-4">{error}</p>
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
              onClick={handleConfirm}
              disabled={!preview || saving || alreadyPlayedWithSelected}
              className="flex-1 py-3 rounded-xl font-medium text-white disabled:opacity-50"
              style={{
                background: 'var(--tg-theme-button-color)',
                color: 'var(--tg-theme-button-text-color)',
              }}
            >
              {saving ? 'Сохранение...' : 'Подтвердить'}
            </button>
          </div>
          </>
          )}
        </Dialog.Panel>
      </div>
    </Dialog>
  )
}
