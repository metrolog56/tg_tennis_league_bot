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
