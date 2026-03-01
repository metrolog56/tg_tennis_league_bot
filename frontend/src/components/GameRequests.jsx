import { useState, useEffect, useCallback } from 'react'
import { Dialog } from '@headlessui/react'
import {
  getActiveGameRequests,
  getMyGameRequests,
  createGameRequest,
  acceptGameRequest,
  cancelGameRequest,
} from '../api/supabase'

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const min = Math.floor(diff / 60000)
  if (min < 1) return 'только что'
  if (min < 60) return `${min} мин назад`
  const hours = Math.floor(min / 60)
  if (hours < 24) return `${hours} ч назад`
  return `${Math.floor(hours / 24)} д назад`
}

export default function GameRequests({ playerId, divisionId, hasDivision }) {
  const [requests, setRequests] = useState([])
  const [myRequests, setMyRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [actionId, setActionId] = useState(null)
  const [flash, setFlash] = useState('')

  const load = useCallback(async () => {
    try {
      const [active, mine] = await Promise.all([
        getActiveGameRequests(divisionId),
        getMyGameRequests(playerId),
      ])
      setRequests((active || []).filter((r) => r.player_id !== playerId))
      setMyRequests(mine || [])
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }, [playerId, divisionId])

  useEffect(() => { load() }, [load])

  const handleCreate = async (type) => {
    setShowCreate(false)
    try {
      await createGameRequest(playerId, type, divisionId)
      setFlash(type === 'division' ? 'Запрос на игру лиги создан!' : 'Запрос на дружескую игру создан!')
      await load()
    } catch (e) {
      setFlash(e?.message || 'Ошибка')
    }
  }

  const handleAccept = async (requestId) => {
    setActionId(requestId)
    try {
      await acceptGameRequest(requestId, playerId)
      setFlash('Вы откликнулись! Договоритесь о времени в личных сообщениях.')
      await load()
    } catch (e) {
      setFlash(e?.message || 'Ошибка')
    } finally {
      setActionId(null)
    }
  }

  const handleCancel = async (requestId) => {
    setActionId(requestId)
    try {
      await cancelGameRequest(requestId, playerId)
      await load()
    } catch {
      // silent
    } finally {
      setActionId(null)
    }
  }

  const myActive = myRequests.find((r) => r.status === 'active')
  const myAccepted = myRequests.filter((r) => r.status === 'accepted')
  const totalActive = requests.length + (myActive ? 1 : 0)

  if (loading) return null

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-base font-bold">
          Найти игру
          {totalActive > 0 && (
            <span
              className="ml-2 inline-flex items-center justify-center w-5 h-5 text-xs rounded-full font-medium"
              style={{ background: 'var(--app-accent)', color: 'var(--app-accent-text)' }}
            >
              {totalActive}
            </span>
          )}
        </h2>
      </div>

      {myAccepted.map((r) => (
        <div
          key={r.id}
          className="mb-2 p-3 rounded-xl border border-green-500/30 bg-green-500/10"
        >
          <p className="text-sm font-medium">
            {r.accepted_player?.name || 'Игрок'} откликнулся на вашу игру!
          </p>
          {r.accepted_player?.telegram_username && (
            <p className="text-sm text-[var(--app-hint)] mt-1">
              Telegram: @{r.accepted_player.telegram_username}
            </p>
          )}
        </div>
      ))}

      {myActive && (
        <div
          className="mb-2 p-3 rounded-xl border border-[var(--app-hint)]/30 flex items-center justify-between"
          style={{ background: 'var(--app-secondary-bg)' }}
        >
          <div>
            <p className="text-sm font-medium">
              Ваш запрос: {myActive.type === 'division' ? 'Игра лиги' : 'Дружеская'}
            </p>
            <p className="text-xs text-[var(--app-hint)]">{timeAgo(myActive.created_at)}</p>
          </div>
          <button
            type="button"
            onClick={() => handleCancel(myActive.id)}
            disabled={actionId === myActive.id}
            className="text-sm text-red-500 font-medium disabled:opacity-50"
          >
            Отменить
          </button>
        </div>
      )}

      {requests.length > 0 && (
        <div className="space-y-2 mb-3">
          {requests.map((r) => (
            <div
              key={r.id}
              className="p-3 rounded-xl border border-[var(--app-hint)]/30 flex items-center justify-between gap-2"
              style={{ background: 'var(--app-secondary-bg)' }}
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium truncate">{r.player?.name || 'Игрок'}</span>
                  <span
                    className="text-xs px-1.5 py-0.5 rounded-full whitespace-nowrap"
                    style={{
                      background: r.type === 'division'
                        ? 'var(--app-accent)'
                        : 'var(--app-hint)',
                      color: r.type === 'division'
                        ? 'var(--app-accent-text)'
                        : '#fff',
                    }}
                  >
                    {r.type === 'division' ? 'Лига' : 'Дружеская'}
                  </span>
                </div>
                <p className="text-xs text-[var(--app-hint)]">{timeAgo(r.created_at)}</p>
              </div>
              <button
                type="button"
                onClick={() => handleAccept(r.id)}
                disabled={actionId === r.id}
                className="text-sm font-medium px-3 py-1.5 rounded-lg shrink-0 disabled:opacity-50"
                style={{ background: 'var(--app-accent)', color: 'var(--app-accent-text)' }}
              >
                {actionId === r.id ? '...' : 'Сыграем'}
              </button>
            </div>
          ))}
        </div>
      )}

      {requests.length === 0 && !myActive && myAccepted.length === 0 && (
        <p className="text-sm text-[var(--app-hint)] mb-3">Пока нет активных запросов.</p>
      )}

      {!myActive && (
        <button
          type="button"
          onClick={() => setShowCreate(true)}
          className="w-full py-3 rounded-xl font-medium border-2 border-dashed border-[var(--app-accent)]/40 text-[var(--app-accent)]"
        >
          🏓 Хочу сыграть
        </button>
      )}

      {showCreate && (
        <Dialog open onClose={() => setShowCreate(false)} className="relative z-50">
          <div className="fixed inset-0 bg-black/50" aria-hidden="true" />
          <div className="fixed inset-0 flex items-center justify-center p-4">
            <Dialog.Panel
              className="w-full max-w-sm rounded-2xl p-5 shadow-xl"
              style={{ background: 'var(--app-bg)', color: 'var(--app-text)' }}
            >
              <Dialog.Title className="text-lg font-bold mb-4">Хочу сыграть</Dialog.Title>
              <div className="flex flex-col gap-3">
                {hasDivision && (
                  <button
                    type="button"
                    onClick={() => handleCreate('division')}
                    className="py-4 px-4 rounded-xl text-left border border-[var(--app-hint)]/30"
                    style={{ background: 'var(--app-secondary-bg)' }}
                  >
                    <p className="font-semibold">Игра лиги</p>
                    <p className="text-sm text-[var(--app-hint)]">Соперники из вашего дивизиона</p>
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => handleCreate('casual')}
                  className="py-4 px-4 rounded-xl text-left border border-[var(--app-hint)]/30"
                  style={{ background: 'var(--app-secondary-bg)' }}
                >
                  <p className="font-semibold">Дружеская игра</p>
                  <p className="text-sm text-[var(--app-hint)]">Увидят все участники лиги</p>
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="py-3 rounded-xl border border-[var(--app-hint)]/40 mt-1"
                >
                  Отмена
                </button>
              </div>
            </Dialog.Panel>
          </div>
        </Dialog>
      )}

      {flash && (
        <Dialog open onClose={() => setFlash('')} className="relative z-50">
          <div className="fixed inset-0 bg-black/50" aria-hidden="true" />
          <div className="fixed inset-0 flex items-center justify-center p-4">
            <Dialog.Panel
              className="w-full max-w-sm rounded-2xl p-6 shadow-xl"
              style={{ background: 'var(--app-bg)', color: 'var(--app-text)' }}
            >
              <p className="text-base mb-4">{flash}</p>
              <button
                type="button"
                onClick={() => setFlash('')}
                className="w-full py-3 rounded-xl font-medium"
                style={{ background: 'var(--app-accent)', color: 'var(--app-accent-text)' }}
              >
                ОК
              </button>
            </Dialog.Panel>
          </div>
        </Dialog>
      )}
    </div>
  )
}
