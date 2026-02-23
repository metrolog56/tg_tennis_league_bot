import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import {
  getPlayerByTelegramId,
  getPlayerDivision,
  getDivisionById,
  getDivisionStandings,
  getDivisionMatches,
  getCurrentSeason,
} from '../api/supabase'

export default function Division({ telegramId }) {
  const { id: paramId } = useParams()
  const [divisionId, setDivisionId] = useState(paramId || null)
  const [division, setDivision] = useState(null)
  const [season, setSeason] = useState(null)
  const [standings, setStandings] = useState([])
  const [matrixData, setMatrixData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        if (paramId) {
          setDivisionId(paramId)
          const [divRes, st, mat] = await Promise.all([
            getDivisionById(paramId),
            getDivisionStandings(paramId),
            getDivisionMatches(paramId),
          ])
          if (cancelled) return
          if (divRes) {
            setDivision(divRes)
            setSeason(divRes.season || null)
          }
          setStandings(st)
          setMatrixData(mat)
          setLoading(false)
          return
        }
        if (!telegramId) {
          setLoading(false)
          return
        }
        const player = await getPlayerByTelegramId(telegramId)
        if (!player) {
          setLoading(false)
          return
        }
        const seasonRes = await getCurrentSeason()
        if (!seasonRes) {
          setLoading(false)
          return
        }
        setSeason(seasonRes)
        const divData = await getPlayerDivision(player.id, seasonRes.id)
        if (cancelled) return
        if (!divData?.division) {
          setLoading(false)
          return
        }
        setDivision(divData.division)
        setSeason(divData.season || seasonRes)
        setDivisionId(divData.division.id)
        const [st, mat] = await Promise.all([
          getDivisionStandings(divData.division.id),
          getDivisionMatches(divData.division.id),
        ])
        if (!cancelled) {
          setStandings(st)
          setMatrixData(mat)
        }
      } catch (e) {
        if (!cancelled) setError(e?.message || 'Ошибка загрузки')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [telegramId, paramId])

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

  if (!matrixData?.players?.length) {
    return (
      <div className="p-4 min-w-[320px]">
        <h1 className="text-xl font-bold mb-4">🏓 Дивизион</h1>
        <p className="text-[var(--tg-theme-hint-color)]">Нет данных дивизиона.</p>
      </div>
    )
  }

  const players = matrixData.players
  const matrix = matrixData.matrix || {}

  const getScore = (p1Id, p2Id) => {
    if (p1Id === p2Id) return '—'
    const key = `${p1Id}-${p2Id}`
    const rev = `${p2Id}-${p1Id}`
    const cell = matrix[key] || matrix[rev]
    if (!cell?.score) return '—'
    return cell.score
  }

  const shortName = (name) => (name || '').split(' ')[0] || '—'

  return (
    <div className="p-4 min-w-[320px] max-w-4xl mx-auto">
      <h1 className="text-xl font-bold mb-2">🏓 Дивизион</h1>
      {season?.name && (
        <p className="text-sm text-[var(--tg-theme-hint-color)] mb-4">{season.name}</p>
      )}

      <div className="table-scroll mb-6">
        <table className="w-full text-sm border-collapse">
          <thead style={{ background: 'var(--tg-theme-secondary-bg-color)' }}>
            <tr>
              <th className="p-1.5 text-left min-w-[60px] sticky left-0 z-10 bg-[var(--tg-theme-secondary-bg-color)]"></th>
              {players.map((p) => (
                <th key={p.id} className="p-1.5 text-center min-w-[44px] max-w-[70px] truncate" title={p.name}>
                  {shortName(p.name)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {players.map((p1) => (
              <tr key={p1.id}>
                <td className="p-1.5 font-medium sticky left-0 z-10 bg-[var(--tg-theme-bg-color)] border-r border-[var(--tg-theme-hint-color)]/20 min-w-[60px] truncate" title={p1.name}>
                  {shortName(p1.name)}
                </td>
                {players.map((p2) => (
                  <td
                    key={p2.id}
                    className="p-1.5 text-center border border-[var(--tg-theme-hint-color)]/20 min-w-[44px]"
                  >
                    {p1.id === p2.id ? '—' : getScore(p1.id, p2.id)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 className="text-lg font-semibold mb-2">Турнирная таблица</h2>
      <div className="rounded-lg border border-[var(--tg-theme-hint-color)]/30 overflow-hidden">
        <table className="w-full text-sm">
          <thead style={{ background: 'var(--tg-theme-secondary-bg-color)' }}>
            <tr>
              <th className="text-left p-2">Место</th>
              <th className="text-left p-2">Игрок</th>
              <th className="text-right p-2">Очки</th>
              <th className="text-right p-2">Сеты</th>
              <th className="text-right p-2">Δ рейтинга</th>
            </tr>
          </thead>
          <tbody>
            {standings.map((row, i) => {
              const p = row.player || {}
              const pts = row.total_points ?? 0
              const sw = row.total_sets_won ?? 0
              const sl = row.total_sets_lost ?? 0
              const delta = row.rating_delta != null ? Number(row.rating_delta) : null
              return (
                <tr key={row.id}>
                  <td className="p-2">{row.position ?? i + 1}</td>
                  <td className="p-2 font-medium">{p.name || '—'}</td>
                  <td className="p-2 text-right">{pts}</td>
                  <td className="p-2 text-right">{sw}-{sl}</td>
                  <td className="p-2 text-right">
                    {delta != null ? (delta >= 0 ? `+${delta.toFixed(2)}` : delta.toFixed(2)) : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
