export default function Rules() {
  return (
    <div className="p-4 min-w-[320px] max-w-lg mx-auto pb-8">
      <h1 className="text-xl font-bold mb-4">📋 Правила</h1>

      <section className="mb-6">
        <h2 className="text-lg font-semibold mb-2">Регламент лиги</h2>
        <ul className="list-disc pl-5 space-y-1 text-sm">
          <li>Лига длится календарный год, туры — по одному месяцу.</li>
          <li>В дивизионе 6–10 игроков, все играют друг с другом в рамках тура.</li>
          <li>Матч: до 3 побед (Best of 5). Допустимые счёты: 3:0, 3:1, 3:2, 2:3, 1:3, 0:3.</li>
          <li>Очки: победа — 2, поражение — 1, несыгранный матч — 0.</li>
          <li>Топ-2 по итогам тура поднимаются в дивизион выше, последние 2 — вниз (если в дивизионе больше 8 человек — последние 3).</li>
          <li>Новый игрок попадает в последний дивизион с начальным рейтингом 100.</li>
          <li>Пропуск тура: в следующем туре игрок участвует как обычно, рейтинг сохраняется.</li>
        </ul>
      </section>

      <section className="mb-6">
        <h2 className="text-lg font-semibold mb-2">Расчёт рейтинга (ФНТР)</h2>
        <p className="text-sm mb-2">
          Изменение рейтинга за матч зависит от коэффициента дивизиона (КД), коэффициента счёта (КС) и разницы рейтингов.
        </p>
        <p className="text-sm font-mono bg-[var(--tg-theme-secondary-bg-color)] p-3 rounded-lg mb-2">
          ПР<sub>победитель</sub> = (100 – (РТ<sub>поб</sub> – РТ<sub>проиг</sub>)) / 10 × КД × КС<br />
          ПР<sub>проигравший</sub> = –(100 – (РТ<sub>поб</sub> – РТ<sub>проиг</sub>)) / 20 × КД × КС
        </p>
        <p className="text-xs text-[var(--tg-theme-hint-color)]">
          РТ — рейтинг до матча. Округление до 2 знаков.
        </p>
      </section>

      <section className="mb-6">
        <h3 className="font-semibold mb-2">Коэффициент дивизиона (КД)</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border border-[var(--tg-theme-hint-color)]/30 rounded-lg overflow-hidden">
            <thead style={{ background: 'var(--tg-theme-secondary-bg-color)' }}>
              <tr>
                <th className="p-2 text-left">Дивизион</th>
                <th className="p-2 text-right">КД</th>
              </tr>
            </thead>
            <tbody>
              <tr><td className="p-2">1</td><td className="p-2 text-right">0.30</td></tr>
              <tr><td className="p-2">2</td><td className="p-2 text-right">0.27</td></tr>
              <tr><td className="p-2">3</td><td className="p-2 text-right">0.25</td></tr>
              <tr><td className="p-2">4</td><td className="p-2 text-right">0.22</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h3 className="font-semibold mb-2">Коэффициент счёта (КС)</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border border-[var(--tg-theme-hint-color)]/30 rounded-lg overflow-hidden">
            <thead style={{ background: 'var(--tg-theme-secondary-bg-color)' }}>
              <tr>
                <th className="p-2 text-left">Счёт матча</th>
                <th className="p-2 text-right">КС</th>
              </tr>
            </thead>
            <tbody>
              <tr><td className="p-2">3:0 или 0:3</td><td className="p-2 text-right">1.2</td></tr>
              <tr><td className="p-2">3:1 или 1:3</td><td className="p-2 text-right">1.0</td></tr>
              <tr><td className="p-2">3:2 или 2:3</td><td className="p-2 text-right">0.8</td></tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
