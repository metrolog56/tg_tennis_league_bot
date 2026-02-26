import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  getPlayerByTelegramId,
  getCurrentSeason,
  getPlayerDivision,
  getDivisionStandings,
  getDivisionMatches,
  getPendingConfirmationForPlayer,
} from '../api/supabase'
import MatchInput from '../components/MatchInput'

export default function Home({ telegramId }) {
  const [player, setPlayer] = useState(null)
  const [divisionData, setDivisionData] = useState(null)
  const [standings, setStandings] = useState([])
  const [matchesMatrix, setMatchesMatrix] = useState(null)
  const [pendingConfirmation, setPendingConfirmation] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showMatchInput, setShowMatchInput] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const [flashMessage, setFlashMessage] = useState('')

  useEffect(() => {
    if (!telegramId) {
      setLoading(false)
      return
    }
    let cancelled = false
    async function load() {
      try {
        const [p, season] = await Promise.all([
          getPlayerByTelegramId(telegramId),
          getCurrentSeason(),
        ])
        if (cancelled) return
        setPlayer(p)
        if (!p || !season) {
          setLoading(false)
          return
        }
        const divData = await getPlayerDivision(p.id, season.id)
        if (cancelled) return
        setDivisionData(divData)
        if (divData?.division?.id) {
          const divisionId = divData.division.id
          const st = await getDivisionStandings(divisionId)
          if (!cancelled) {
            setStandings(st)
            setLoading(false)
          }
          const loadMatchesAndPending = () =>
            Promise.all([
              getDivisionMatches(divisionId),
              getPendingConfirmationForPlayer(p.id),
            ]).then(([mat, pending]) => {
              if (!cancelled) {
                setMatchesMatrix(mat)
                setPendingConfirmation(pending || [])
              }
            }).catch(() => {})
          loadMatchesAndPending()
        } else {
          setLoading(false)
        }
      } catch (e) {
        if (!cancelled) {
          setError(e?.message || 'Ошибка загрузки')
          setLoading(false)
        }
      }
    }
    load()
    return () => { cancelled = true }
  }, [telegramId])

  useEffect(() => {
    const msg = location.state?.message
    if (!msg || !player?.id || !divisionData?.division?.id) return
    setFlashMessage(msg)
    navigate(location.pathname, { replace: true, state: {} })
    const t = setTimeout(() => setFlashMessage(''), 4000)
    let cancelled = false
    Promise.all([
      getDivisionMatches(divisionData.division.id),
      getPendingConfirmationForPlayer(player.id),
    ]).then(([mat, pending]) => {
      if (!cancelled) {
        setMatchesMatrix(mat)
        setPendingConfirmation(pending || [])
      }
    }).catch(() => {})
    return () => { clearTimeout(t); cancelled = true }
  }, [location.state?.message, location.pathname, navigate, player?.id, divisionData?.division?.id])

  if (!telegramId) {
    const botName = import.meta.env.VITE_TELEGRAM_BOT_NAME || ''
    const telegramLink = botName ? `https://t.me/${botName.replace('@', '')}` : null
    return (
      <div className="p-4 min-w-[320px] max-w-lg mx-auto">
        <h1 className="text-xl font-bold mb-2">🏠 Главная</h1>
        <p className="text-[var(--tg-theme-text-color)] mb-3">
          Откройте приложение в Telegram, чтобы видеть свой дивизион и вносить результаты.
        </p>
        {telegramLink ? (
          <a
            href={telegramLink}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block py-2 px-4 rounded-xl font-medium text-white"
            style={{ background: 'var(--tg-theme-button-color)', color: 'var(--tg-theme-button-text-color)' }}
          >
            Открыть в Telegram
          </a>
        ) : (
          <p className="text-sm text-[var(--tg-theme-hint-color)]">
            Запустите Mini App из меню бота в Telegram.
          </p>
        )}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="p-4 min-w-[320px] max-w-lg mx-auto">
        <h1 className="text-xl font-bold mb-2">🏠 Главная</h1>
        <p className="text-[var(--tg-theme-hint-color)] mb-4">Загрузка...</p>
        <div className="rounded-lg border border-[var(--tg-theme-hint-color)]/30 overflow-hidden animate-pulse">
          <div className="h-10 bg-[var(--tg-theme-secondary-bg-color)]" />
          <div className="h-12 bg-[var(--tg-theme-bg-color)]" />
          <div className="h-12 bg-[var(--tg-theme-secondary-bg-color)]/50" />
          <div className="h-12 bg-[var(--tg-theme-bg-color)]" />
          <div className="h-12 bg-[var(--tg-theme-secondary-bg-color)]/50" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 min-w-[320px]">
        <p className="text-red-500">{error}</p>
      </div>
    )
  }

  if (!player) {
    return (
      <div className="p-4 min-w-[320px]">
        <p className="text-[var(--tg-theme-hint-color)]">Сначала зарегистрируйтесь в боте (/start).</p>
      </div>
    )
  }

  if (!divisionData?.division) {
    return (
      <div className="p-4 min-w-[320px]">
        <h1 className="text-xl font-bold mb-4">🏠 Главная</h1>
        <p className="text-[var(--tg-theme-hint-color)]">Вы пока не привязаны к дивизиону. Обратитесь к администратору.</p>
      </div>
    )
  }

  const division = divisionData.division
  const season = divisionData.season || {}
  const divisionPlayers = divisionData.divisionPlayers || []
  const myId = player.id

  const existingMatchesByOpponentId = {}
  if (matchesMatrix?.matches) {
    for (const m of matchesMatrix.matches) {
      const p1 = m.player1_id
      const p2 = m.player2_id
      if (m.status === 'played') {
        if (p1 === myId) existingMatchesByOpponentId[p2] = 'played'
        else if (p2 === myId) existingMatchesByOpponentId[p1] = 'played'
      } else if (m.status === 'pending_confirm' && m.submitted_by === myId) {
        if (p1 === myId) existingMatchesByOpponentId[p2] = 'pending_confirm'
        else if (p2 === myId) existingMatchesByOpponentId[p1] = 'pending_confirm'
      }
    }
  }
  const opponents = divisionPlayers
    .filter(d => (d.player?.id || d.player_id) !== myId)
    .map(d => d.player || { id: d.player_id })
    .filter(Boolean)

  const getCell = (p1Id, p2Id) => {
    if (!matchesMatrix?.matrix || p1Id === p2Id) return null
    const key = `${p1Id}-${p2Id}`
    const rev = `${p2Id}-${p1Id}`
    const cell = matchesMatrix.matrix[key] || matchesMatrix.matrix[rev]
    return cell
  }

  return (
    <div className="p-4 min-w-[320px] max-w-lg mx-auto">
      <h1 className="text-xl font-bold mb-2">🏠 Главная</h1>
      {flashMessage && (
        <p className="text-sm mb-3 px-3 py-2 rounded-lg" style={{ background: 'var(--tg-theme-button-color)', color: 'var(--tg-theme-button-text-color)' }}>
          {flashMessage}
        </p>
      )}
      <p className="text-sm text-[var(--tg-theme-hint-color)] mb-4">
        {season.name} · Дивизион {division.number}
      </p>

      <div className="rounded-lg border border-[var(--tg-theme-hint-color)]/30 overflow-hidden mb-4">
        <table className="w-full text-sm">
          <thead style={{ background: 'var(--tg-theme-secondary-bg-color)' }}>
            <tr>
              <th className="text-left p-2">Место</th>
              <th className="text-left p-2">Игрок</th>
              <th className="text-right p-2">Очки</th>
              <th className="text-right p-2">Сеты</th>
              <th className="text-right p-2">Дельта рейтинга</th>
            </tr>
          </thead>
          <tbody>
            {[...standings]
              .sort((a, b) => (b.total_points ?? 0) - (a.total_points ?? 0) || ((b.total_sets_won ?? 0) - (b.total_sets_lost ?? 0)) - ((a.total_sets_won ?? 0) - (a.total_sets_lost ?? 0)))
              .map((row, i) => {
              const p = row.player || {}
              const name = p.name || '—'
              const pts = row.total_points ?? 0
              const sets = `${row.total_sets_won ?? 0}-${row.total_sets_lost ?? 0}`
              const delta = row.rating_delta != null ? Number(row.rating_delta) : null
              const isMe = p.id === myId
              return (
                <tr
                  key={row.id}
                  className={isMe ? 'bg-[var(--tg-theme-button-color)]/10' : ''}
                >
                  <td className="p-2">{i + 1}</td>
                  <td className="p-2 font-medium">{name}{isMe ? ' (вы)' : ''}</td>
                  <td className="p-2 text-right">{pts}</td>
                  <td className="p-2 text-right">{sets}</td>
                  <td className="p-2 text-right">
                    {delta != null ? (delta >= 0 ? `+${delta.toFixed(2)}` : delta.toFixed(2)) : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {pendingConfirmation.length > 0 && (
        <div className="mb-4 p-3 rounded-lg border border-[var(--tg-theme-hint-color)]/30" style={{ background: 'var(--tg-theme-secondary-bg-color)' }}>
          <p className="text-sm font-medium mb-2">Ожидает подтверждения от вас</p>
          <ul className="space-y-1.5">
            {pendingConfirmation.map((m) => {
              const submitterName = divisionPlayers.find(
                (d) => (d.player?.id || d.player_id) === m.submitted_by
              )?.player?.name || 'Игрок'
              const score = `${m.sets_player1 ?? 0}:${m.sets_player2 ?? 0}`
              return (
                <li key={m.id}>
                  <a
                    href={`#/confirm-match/${m.id}`}
                    onClick={(e) => { e.preventDefault(); navigate(`/confirm-match/${m.id}`) }}
                    className="text-sm text-[var(--tg-theme-link-color)] underline"
                  >
                    {submitterName} внёс результат {score} — подтвердите
                  </a>
                </li>
              )
            })}
          </ul>
        </div>
      )}

      <div className="flex flex-col gap-2">
        <button
          type="button"
          onClick={() => setShowMatchInput(true)}
          className="w-full py-3 rounded-xl font-medium text-white"
          style={{ background: 'var(--tg-theme-button-color)', color: 'var(--tg-theme-button-text-color)' }}
        >
          ➕ Внести результат матча
        </button>
      </div>

      {showMatchInput && (
        <MatchInput
          divisionId={division.id}
          divisionCoef={Number(division.coef) || 0.25}
          currentPlayerId={myId}
          currentPlayerRating={Number(player.rating) || 100}
          opponents={opponents}
          existingMatchesByOpponentId={existingMatchesByOpponentId}
          onClose={() => setShowMatchInput(false)}
          onSaved={async (opponentName) => {
            setShowMatchInput(false)
            if (opponentName) {
              setFlashMessage(`Результат отправлен на подтверждение ${opponentName}. После подтверждения счёт и рейтинг обновятся.`)
              setTimeout(() => setFlashMessage(''), 5000)
            }
            if (!division?.id || !player?.id) return
            const [st, mat, pending] = await Promise.all([
              getDivisionStandings(division.id),
              getDivisionMatches(division.id),
              getPendingConfirmationForPlayer(player.id),
            ])
            setStandings(st)
            setMatchesMatrix(mat)
            setPendingConfirmation(pending || [])
          }}
        />
      )}
    </div>
  )
}
