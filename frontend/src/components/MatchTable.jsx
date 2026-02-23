/**
 * Матричная таблица результатов матчей дивизиона.
 * Строки и столбцы — игроки, ячейка — счёт или кнопка для ввода.
 */
export default function MatchTable({ division, onSelectMatch }) {
  const players = division?.division_players?.map((dp) => dp.player)?.filter(Boolean) || []
  const matches = division?.matches || []

  const getMatch = (p1Id, p2Id) =>
    matches.find(
      (m) =>
        (m.player1_id === p1Id && m.player2_id === p2Id) ||
        (m.player1_id === p2Id && m.player2_id === p1Id)
    )

  if (!players.length) return <p className="text-gray-500">Нет участников</p>

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr>
            <th className="border p-1 text-left w-24"></th>
            {players.map((p) => (
              <th key={p.id} className="border p-1 text-center truncate max-w-[60px]" title={p.name}>
                {p.name?.split(' ')[0] || '—'}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {players.map((p1) => (
            <tr key={p1.id}>
              <td className="border p-1 truncate max-w-[80px]" title={p1.name}>{p1.name?.split(' ')[0] || '—'}</td>
              {players.map((p2) => {
                if (p1.id === p2.id) return <td key={p2.id} className="border p-1 bg-gray-100">—</td>
                const match = getMatch(p1.id, p2.id)
                const isP1First = match?.player1_id === p1.id
                const score = match?.status === 'played'
                  ? `${match.sets_player1}:${match.sets_player2}`
                  : match?.status === 'not_played'
                    ? '×'
                    : '·'
                return (
                  <td key={p2.id} className="border p-1 text-center">
                    <button
                      type="button"
                      className="w-full py-1 hover:bg-gray-100 rounded"
                      onClick={() => onSelectMatch?.({ ...match, division_id: division?.id, player1: p1, player2: p2 })}
                    >
                      {score}
                    </button>
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
