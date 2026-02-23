/**
 * Таблица рейтинга (место, имя, рейтинг).
 */
export default function RatingTable({ players }) {
  if (!players?.length) return <p className="text-gray-500">Рейтинг пуст</p>

  return (
    <ul className="divide-y border rounded-lg overflow-hidden">
      {players.map((p, i) => (
        <li key={p.id} className="flex items-center justify-between p-3 bg-white">
          <span className="font-bold text-gray-500 w-8">{i + 1}</span>
          <span className="flex-1 font-medium">{p.name}</span>
          <span className="font-mono">{Number(p.rating ?? 0).toFixed(2)}</span>
        </li>
      ))}
    </ul>
  )
}
