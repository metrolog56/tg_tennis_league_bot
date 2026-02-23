import { useState, useEffect } from 'react'
import {
  getPlayerByTelegramId,
  getCurrentSeason,
  getPlayerDivision,
  getDivisionStandings,
  getDivisionMatches,
} from '../api/supabase'
import MatchInput from '../components/MatchInput'

export default function Home({ telegramId }) {
  const [player, setPlayer] = useState(null)
  const [divisionData, setDivisionData] = useState(null)
  const [standings, setStandings] = useState([])
  const [matchesMatrix, setMatchesMatrix] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showMatchInput, setShowMatchInput] = useState(false)

  useEffect(() => {
    if (!telegramId) {
      setLoading(false)
      return
    }
    let cancelled = false
    async function load() {
      try {
        const p = await getPlayerByTelegramId(telegramId)
        if (cancelled) return
        setPlayer(p)
        if (!p) {
          setLoading(false)
          return
        }
        const season = await getCurrentSeason()
        if (!season) {
          setLoading(false)
          return
        }
        const divData = await getPlayerDivision(p.id, season.id)
        if (cancelled) return
        setDivisionData(divData)
        if (divData?.division?.id) {
          const [st, mat] = await Promise.all([
            getDivisionStandings(divData.division.id),
            getDivisionMatches(divData.division.id),
          ])
          if (!cancelled) {
            setStandings(st)
            setMatchesMatrix(mat)
          }
        }
      } catch (e) {
        if (!cancelled) setError(e?.message || 'Ошибка загрузки')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [telegramId])

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
      if (m.status !== 'played') continue
      const p1 = m.player1_id
      const p2 = m.player2_id
      if (p1 === myId) existingMatchesByOpponentId[p2] = 'played'
      else if (p2 === myId) existingMatchesByOpponentId[p1] = 'played'
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
      <p className="text-sm text-[var(--tg-theme-hint-color)] mb-4">
        {season.name} · Дивизион {division.number}
      </p>

      <div className="rounded-lg border border-[var(--tg-theme-hint-color)]/30 overflow-hidden mb-4">
        <table className="w-full text-sm">
          <thead style={{ background: 'var(--tg-theme-secondary-bg-color)' }}>
            <tr>
              <th className="text-left p-2">#</th>
              <th className="text-left p-2">Игрок</th>
              <th className="text-right p-2">Очки</th>
              <th className="text-right p-2">Сеты</th>
            </tr>
          </thead>
          <tbody>
            {standings.map((row, i) => {
              const p = row.player || {}
              const name = p.name || '—'
              const pts = row.total_points ?? 0
              const sets = `${row.total_sets_won ?? 0}-${row.total_sets_lost ?? 0}`
              const isMe = p.id === myId
              return (
                <tr
                  key={row.id}
                  className={isMe ? 'bg-[var(--tg-theme-button-color)]/10' : ''}
                >
                  <td className="p-2">{row.position ?? i + 1}</td>
                  <td className="p-2 font-medium">{name}{isMe ? ' (вы)' : ''}</td>
                  <td className="p-2 text-right">{pts}</td>
                  <td className="p-2 text-right">{sets}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

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
          onSaved={async () => {
            setShowMatchInput(false)
            if (!telegramId) return
            const [st, mat, p] = await Promise.all([
              getDivisionStandings(division.id),
              getDivisionMatches(division.id),
              getPlayerByTelegramId(telegramId),
            ])
            setStandings(st)
            setMatchesMatrix(mat)
            if (p) setPlayer(p)
          }}
        />
      )}
    </div>
  )
}
