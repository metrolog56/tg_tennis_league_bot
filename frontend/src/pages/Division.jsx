import { useState, useEffect } from 'react'
import {
  getCurrentSeason,
  getDivisionsBySeasonId,
  getDivisionMatches,
} from '../api/supabase'

function DivisionMatrix({ divisionNumber, matrixData }) {
  const players = matrixData?.players || []
  const matrix = matrixData?.matrix || {}

  const getScore = (p1Id, p2Id) => {
    if (p1Id === p2Id) return '—'
    const key = `${p1Id}-${p2Id}`
    const rev = `${p2Id}-${p1Id}`
    const cell = matrix[key] || matrix[rev]
    if (cell == null || cell.status !== 'played') return '—'
    const s1 = cell.sets1
    const s2 = cell.sets2
    if (s1 == null || s2 == null) return '—'
    const p1Sets = cell.player1_id === p1Id ? s1 : s2
    const p2Sets = cell.player1_id === p1Id ? s2 : s1
    return `${p1Sets}-${p2Sets}`
  }

  // Имя + инициал фамилии, чтобы различать одноимённых (напр. Дмитрий Б. и Дмитрий Р.)
  const displayName = (name) => {
    const parts = (name || '').trim().split(/\s+/).filter(Boolean)
    if (parts.length >= 2) return `${parts[0]} ${parts[1][0]}.`
    return name || '—'
  }

  if (!players.length) return null

  return (
    <div className="mb-8">
      <h2 className="text-lg font-semibold mb-2">Дивизион {divisionNumber}</h2>
      <div className="glass glass-table-wrap rounded-lg overflow-hidden">
        <div className="table-scroll">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr>
              <th className="p-1.5 text-left min-w-[60px] sticky left-0 z-10"></th>
              {players.map((p) => (
                <th key={p.id} className="p-1.5 text-center min-w-[44px] max-w-[70px] truncate" title={p.name}>
                  {displayName(p.name)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {players.map((p1) => (
              <tr key={p1.id}>
                <td className="p-1.5 font-medium sticky left-0 z-10 bg-[var(--tg-theme-bg-color)] border-r border-[var(--tg-theme-hint-color)]/20 min-w-[60px] truncate" title={p1.name}>
                  {displayName(p1.name)}
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
      </div>
    </div>
  )
}

export default function Division() {
  const [season, setSeason] = useState(null)
  const [divisions, setDivisions] = useState([])
  const [divisionMatrixMap, setDivisionMatrixMap] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const seasonRes = await getCurrentSeason()
        if (cancelled) return
        if (!seasonRes) {
          setLoading(false)
          return
        }
        setSeason(seasonRes)
        const divs = await getDivisionsBySeasonId(seasonRes.id)
        if (cancelled) return
        setDivisions(divs || [])
        const map = {}
        await Promise.all(
          (divs || []).map(async (d) => {
            const mat = await getDivisionMatches(d.id)
            if (!cancelled) map[d.id] = mat
          })
        )
        if (!cancelled) setDivisionMatrixMap(map)
      } catch (e) {
        if (!cancelled) setError(e?.message || 'Ошибка загрузки')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

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

  if (!season) {
    return (
      <div className="p-4 min-w-[320px]">
        <h1 className="text-xl font-bold mb-4">🏓 Дивизионы</h1>
        <p className="text-[var(--tg-theme-hint-color)]">Нет активного сезона.</p>
      </div>
    )
  }

  if (!divisions.length) {
    return (
      <div className="p-4 min-w-[320px]">
        <h1 className="text-xl font-bold mb-4">🏓 Дивизионы</h1>
        <p className="text-[var(--tg-theme-hint-color)]">Нет дивизионов в текущем сезоне.</p>
      </div>
    )
  }

  return (
    <div className="p-4 min-w-[320px] max-w-4xl mx-auto">
      <h1 className="text-xl font-bold mb-2">🏓 Дивизионы</h1>
      {season?.name && (
        <p className="text-sm text-[var(--tg-theme-hint-color)] mb-6">{season.name}</p>
      )}

      {divisions.map((d) => (
        <DivisionMatrix
          key={d.id}
          divisionNumber={d.number}
          matrixData={divisionMatrixMap[d.id]}
        />
      ))}
    </div>
  )
}
