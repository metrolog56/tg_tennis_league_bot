import { useState } from 'react'
import { Listbox, Transition, Dialog } from '@headlessui/react'
import { Fragment } from 'react'
import { submitMatchResult } from '../api/supabase'
import { calculateMatchRating } from '../utils/ratingCalc'

function ChevronIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M10 3a1 1 0 01.707.293l3 3a1 1 0 01-1.414 1.414L10 5.414 7.707 7.707a1 1 0 01-1.414-1.414l3-3A1 1 0 0110 3z" clipRule="evenodd" />
    </svg>
  )
}

export default function MatchInput({
  divisionId,
  divisionCoef,
  currentPlayerId,
  currentPlayerRating,
  opponents,
  onClose,
  onSaved,
}) {
  const [selectedOpponent, setSelectedOpponent] = useState(null)
  const [scoreChoice, setScoreChoice] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const opponentList = opponents || []
  const myRating = Number(currentPlayerRating) || 100
  const oppRating = Number(selectedOpponent?.rating) || 100

  let preview = null
  if (scoreChoice && selectedOpponent) {
    const [mySets, oppSets] = scoreChoice
    const isWinner = mySets > oppSets
    const { deltaWinner, deltaLoser } = calculateMatchRating(
      isWinner ? myRating : oppRating,
      isWinner ? oppRating : myRating,
      isWinner ? mySets : oppSets,
      isWinner ? oppSets : mySets,
      divisionCoef
    )
    const myDelta = isWinner ? deltaWinner : deltaLoser
    preview = {
      text: `${mySets}:${oppSets}`,
      myDelta,
      newRating: myRating + myDelta,
    }
  }

  const handleConfirm = async () => {
    if (!selectedOpponent || !scoreChoice) return
    setError('')
    setSaving(true)
    try {
      const [sets1, sets2] = scoreChoice
      await submitMatchResult(
        divisionId,
        currentPlayerId,
        selectedOpponent.id,
        sets1,
        sets2
      )
      onSaved?.()
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
      <div className="fixed inset-0 flex items-end sm:items-center justify-center p-0 sm:p-4 min-w-[320px]">
        <Dialog.Panel
          className="w-full max-h-[90vh] overflow-y-auto rounded-t-2xl sm:rounded-2xl p-4 shadow-xl"
          style={{
            background: 'var(--tg-theme-bg-color)',
            color: 'var(--tg-theme-text-color)',
          }}
        >
          <Dialog.Title className="text-lg font-bold mb-4">
            Внести результат матча
          </Dialog.Title>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-1 text-[var(--tg-theme-hint-color)]">
              Соперник
            </label>
            <Listbox value={selectedOpponent} onChange={setSelectedOpponent}>
              <div className="relative">
                <Listbox.Button
                  className="relative w-full rounded-lg border border-[var(--tg-theme-hint-color)]/40 py-2.5 pl-3 pr-10 text-left focus:outline-none focus:ring-2 focus:ring-[var(--tg-theme-button-color)]"
                  style={{ background: 'var(--tg-theme-secondary-bg-color)' }}
                >
                  <span className="block truncate">
                    {selectedOpponent?.name || 'Выберите соперника'}
                  </span>
                  <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                    <ChevronIcon />
                  </span>
                </Listbox.Button>
                <Transition
                  as={Fragment}
                  leave="transition ease-in duration-100"
                  leaveFrom="opacity-100"
                  leaveTo="opacity-0"
                >
                  <Listbox.Options
                    className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded-lg py-1 shadow-lg focus:outline-none"
                    style={{
                      background: 'var(--tg-theme-bg-color)',
                      border: '1px solid var(--tg-theme-hint-color)',
                    }}
                  >
                    {opponentList.map((p) => (
                      <Listbox.Option
                        key={p.id}
                        value={p}
                        className={({ active }) =>
                          `relative cursor-pointer select-none py-2 pl-3 pr-9 rounded ${
                            active ? 'bg-[var(--tg-theme-secondary-bg-color)]' : ''
                          }`
                        }
                      >
                        <span className="block truncate">{p.name || '—'}</span>
                      </Listbox.Option>
                    ))}
                  </Listbox.Options>
                </Transition>
              </div>
            </Listbox>
          </div>

          {selectedOpponent && (
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

          {preview && (
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
              disabled={!preview || saving}
              className="flex-1 py-3 rounded-xl font-medium text-white disabled:opacity-50"
              style={{
                background: 'var(--tg-theme-button-color)',
                color: 'var(--tg-theme-button-text-color)',
              }}
            >
              {saving ? 'Сохранение...' : 'Подтвердить'}
            </button>
          </div>
        </Dialog.Panel>
      </div>
    </Dialog>
  )
}
