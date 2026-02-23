/**
 * Карточка игрока в списке дивизиона (место, имя, очки, сеты).
 */
export default function PlayerCard({ divisionPlayer }) {
  const p = divisionPlayer?.player
  const pos = divisionPlayer?.position
  const pts = divisionPlayer?.total_points ?? 0
  const sets = `${divisionPlayer?.total_sets_won ?? 0}-${divisionPlayer?.total_sets_lost ?? 0}`

  return (
    <div className="flex items-center justify-between p-3 border rounded-lg">
      <div className="flex items-center gap-2">
        <span className="font-bold text-gray-500 w-6">{pos ?? '—'}</span>
        <span className="font-medium">{p?.name ?? 'Игрок'}</span>
      </div>
      <div className="text-sm text-gray-600">
        {pts} очк. · {sets} сетов
      </div>
    </div>
  )
}
