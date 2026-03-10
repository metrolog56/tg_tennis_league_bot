/**
 * Определение сценария матча на основе счёта и позиций игроков в таблице дивизиона.
 * Используется для генерации реакции-карточки после подтверждения результата.
 */

export const SCENARIOS = {
  UPSET_DOMINANT: 'UPSET_DOMINANT',
  UPSET_CLOSE:    'UPSET_CLOSE',
  UPSET:          'UPSET',
  CLOSE_BATTLE:   'CLOSE_BATTLE',
  EXPECTED_DOMINANT: 'EXPECTED_DOMINANT',
  EXPECTED:       'EXPECTED',
  EQUAL:          'EQUAL',
}

const REACTIONS = {
  [SCENARIOS.UPSET_DOMINANT]: {
    headline: 'Разгром! Сенсация дня',
    subline: 'Нижний в таблице разнёс лидера всухую',
    emoji: '🔥',
    gradient: ['#b91c1c', '#7f1d1d'],
  },
  [SCENARIOS.UPSET_CLOSE]: {
    headline: 'Невероятный камбэк!',
    subline: 'Андердог вырвал победу в пяти сетах',
    emoji: '💥',
    gradient: ['#c2410c', '#7c2d12'],
  },
  [SCENARIOS.UPSET]: {
    headline: 'Неожиданный поворот!',
    subline: 'Нижний в таблице одержал победу',
    emoji: '⚡',
    gradient: ['#b45309', '#78350f'],
  },
  [SCENARIOS.CLOSE_BATTLE]: {
    headline: 'Боевой матч!',
    subline: 'Пять сетов борьбы — победила стойкость',
    emoji: '💪',
    gradient: ['#0369a1', '#0c4a6e'],
  },
  [SCENARIOS.EXPECTED_DOMINANT]: {
    headline: 'Лидер не оставил шансов',
    subline: 'Безупречная игра и победа всухую',
    emoji: '🎾',
    gradient: ['#1d4ed8', '#1e3a8a'],
  },
  [SCENARIOS.EXPECTED]: {
    headline: 'Всё по плану',
    subline: 'Фаворит подтвердил свою позицию',
    emoji: '✅',
    gradient: ['#0f766e', '#134e4a'],
  },
  [SCENARIOS.EQUAL]: {
    headline: 'Равный бой',
    subline: 'Соперники достойны уважения',
    emoji: '🤝',
    gradient: ['#4f46e5', '#312e81'],
  },
}

/**
 * Определяет сценарий матча.
 *
 * @param {object} params
 * @param {number} params.winnerSets       - сеты победителя (3)
 * @param {number} params.loserSets        - сеты проигравшего (0/1/2)
 * @param {number} params.winnerPosition   - позиция победителя в таблице (1 = первое место)
 * @param {number} params.loserPosition    - позиция проигравшего в таблице
 * @returns {string} один из ключей SCENARIOS
 */
export function getMatchScenario({ winnerSets, loserSets, winnerPosition, loserPosition }) {
  const ws = Number(winnerSets)
  const ls = Number(loserSets)
  const wp = Number(winnerPosition) || 0
  const lp = Number(loserPosition) || 0

  const isClose = ws === 3 && ls === 2
  const isDominant = ws === 3 && ls === 0
  // upset: победитель стоит ниже в таблице (больший номер позиции = хуже)
  const isUpset = wp > lp && lp > 0 && wp > 0
  const isEqual = wp === lp || lp === 0 || wp === 0

  if (isUpset && isDominant) return SCENARIOS.UPSET_DOMINANT
  if (isUpset && isClose)    return SCENARIOS.UPSET_CLOSE
  if (isUpset)               return SCENARIOS.UPSET
  if (isClose)               return SCENARIOS.CLOSE_BATTLE
  if (!isEqual && isDominant) return SCENARIOS.EXPECTED_DOMINANT
  if (!isEqual)              return SCENARIOS.EXPECTED
  return SCENARIOS.EQUAL
}

/** Возвращает текст и цвета для заданного сценария. */
export function getScenarioReaction(scenario) {
  return REACTIONS[scenario] || REACTIONS[SCENARIOS.EQUAL]
}
