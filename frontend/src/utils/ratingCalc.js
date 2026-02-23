/**
 * Расчёт рейтинга по формулам ФНТР (дублирует бота для превью).
 * КС: 3:0/0:3 → 1.2, 3:1/1:3 → 1.0, 3:2/2:3 → 0.8
 * ПРв = (100 – (РТВ – РТП)) / 10 * КД * КС
 * ПРп = -(100 – (РТВ – РТП)) / 20 * КД * КС
 */

export function calculateScoreCoef(setsP1, setsP2) {
  const a = Number(setsP1)
  const b = Number(setsP2)
  if ((a === 3 && b === 0) || (a === 0 && b === 3)) return 1.2
  if ((a === 3 && b === 1) || (a === 1 && b === 3)) return 1.0
  if ((a === 3 && b === 2) || (a === 2 && b === 3)) return 0.8
  return 1.0
}

export function calculateMatchRating(winnerRating, loserRating, winnerSets, loserSets, kd) {
  const ks = calculateScoreCoef(winnerSets, loserSets)
  const base = (100 - (winnerRating - loserRating)) / 10
  const deltaWinner = Math.round(base * kd * ks * 100) / 100
  const deltaLoser = Math.round(-(base / 2) * kd * ks * 100) / 100
  return { deltaWinner, deltaLoser }
}

export function calcRatingDelta(ratingWinner, ratingLoser, divisionCoef, setsWinner, setsLoser) {
  return calculateMatchRating(ratingWinner, ratingLoser, setsWinner, setsLoser, divisionCoef)
}

/**
 * Превью изменения рейтинга для текущего игрока (для MatchInput).
 * @returns { { myDelta: number, newRating: number } | null } null если счёт невалидный (не Best of 5)
 */
export function previewRatingChange(myRating, opponentRating, mySets, oppSets, kd) {
  const a = Number(mySets)
  const b = Number(oppSets)
  const validScores = [[3, 0], [3, 1], [3, 2], [2, 3], [1, 3], [0, 3]]
  const valid = validScores.some(([x, y]) => x === a && y === b)
  if (!valid) return null
  const myR = Number(myRating) || 100
  const oppR = Number(opponentRating) || 100
  if (a > b) {
    const { deltaWinner, deltaLoser } = calculateMatchRating(myR, oppR, a, b, Number(kd) || 0.25)
    return { myDelta: deltaWinner, newRating: myR + deltaWinner }
  }
  if (b > a) {
    const { deltaWinner, deltaLoser } = calculateMatchRating(oppR, myR, b, a, Number(kd) || 0.25)
    return { myDelta: deltaLoser, newRating: myR + deltaLoser }
  }
  return null
}
