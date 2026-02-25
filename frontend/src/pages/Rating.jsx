import { useState, useEffect } from 'react'
import { getTopRatingWithStats, getPlayerByTelegramId } from '../api/supabase'

export default function Rating({ telegramId }) {
  const [list, setList] = useState([])
  const [currentPlayerId, setCurrentPlayerId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const [top, player] = await Promise.all([
          getTopRatingWithStats(50),
          telegramId ? getPlayerByTelegramId(telegramId) : null,
        ])
        if (!cancelled) {
          setList(top || [])
          setCurrentPlayerId(player?.id ?? null)
        }
      } catch (e) {
        if (!cancelled) setError(e?.message || 'Ошибка загрузки')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
  }, [telegramId])

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

  const medal = (i) => (i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : null)

  return (
    <div className="p-4 min-w-[320px] max-w-lg mx-auto">
      <h1 className="text-xl font-bold mb-4">📊 Рейтинг</h1>

      <div className="rounded-lg border border-[var(--tg-theme-hint-color)]/30 overflow-hidden">
        <table className="w-full text-sm">
          <thead style={{ background: 'var(--tg-theme-secondary-bg-color)' }}>
            <tr>
              <th className="text-left p-2 w-12">#</th>
              <th className="text-left p-2">Игрок</th>
              <th className="text-right p-2">Рейтинг</th>
              <th className="text-right p-2">Игры</th>
              <th className="text-right p-2">В</th>
              <th className="text-right p-2">П</th>
              <th className="text-right p-2">%</th>
            </tr>
          </thead>
          <tbody>
            {list.map((row, i) => {
              const isCurrent = row.id === currentPlayerId
              const m = medal(i)
              const games = row.games != null ? Number(row.games) : null
              const wins = row.wins != null ? Number(row.wins) : null
              const losses = games != null && wins != null ? games - wins : null
              const pct = games != null && games > 0 && wins != null ? (wins / games * 100).toFixed(1) : null
              return (
                <tr
                  key={row.id}
                  className={isCurrent ? 'bg-[var(--tg-theme-button-color)]/15' : ''}
                >
                  <td className="p-2">
                    {m ? <span>{m}</span> : i + 1}
                  </td>
                  <td className="p-2 font-medium">
                    {row.name || '—'}{isCurrent ? ' (вы)' : ''}
                  </td>
                  <td className="p-2 text-right font-mono">
                    {Number(row.rating ?? 0).toFixed(2)}
                  </td>
                  <td className="p-2 text-right">{games != null ? games : '—'}</td>
                  <td className="p-2 text-right">{wins != null ? wins : '—'}</td>
                  <td className="p-2 text-right">{losses != null ? losses : '—'}</td>
                  <td className="p-2 text-right">{pct != null ? `${pct}%` : '—'}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {list.length === 0 && (
        <p className="text-[var(--tg-theme-hint-color)] mt-4">Рейтинг пуст.</p>
      )}
    </div>
  )
}
