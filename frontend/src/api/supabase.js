import { createClient } from '@supabase/supabase-js'
import { calculateMatchRating } from '../utils/ratingCalc'

const url = import.meta.env.VITE_SUPABASE_URL
const key = import.meta.env.VITE_SUPABASE_KEY || import.meta.env.VITE_SUPABASE_ANON_KEY

if (!url || !key) {
  console.warn('VITE_SUPABASE_URL or VITE_SUPABASE_KEY (or VITE_SUPABASE_ANON_KEY) not set')
}

export const supabase = createClient(url || '', key || '')

export async function getPlayerByTelegramId(telegramId) {
  const { data, error } = await supabase
    .from('players')
    .select('*')
    .eq('telegram_id', telegramId)
    .maybeSingle()
  if (error) throw error
  return data
}

export async function getCurrentSeason() {
  const { data, error } = await supabase
    .from('seasons')
    .select('*')
    .eq('status', 'active')
    .order('year', { ascending: false })
    .order('month', { ascending: false })
    .limit(1)
    .maybeSingle()
  if (error) throw error
  return data
}

export async function getPlayerDivision(playerId, seasonId) {
  if (!seasonId) {
    const season = await getCurrentSeason()
    if (!season) return null
    seasonId = season.id
  }
  const { data: divisions } = await supabase
    .from('divisions')
    .select('id')
    .eq('season_id', seasonId)
  if (!divisions?.length) return null
  for (const d of divisions) {
    const { data: dp } = await supabase
      .from('division_players')
      .select('*, division:divisions(*, season:seasons(*))')
      .eq('division_id', d.id)
      .eq('player_id', playerId)
      .maybeSingle()
    if (dp) {
      const { data: players } = await supabase
        .from('division_players')
        .select('*, player:players(*)')
        .eq('division_id', d.id)
      return {
        division: dp.division || dp.divisions,
        season: dp.division?.season || dp.divisions?.season,
        divisionPlayers: players || [],
      }
    }
  }
  return null
}

export async function getDivisionById(divisionId) {
  const { data: div, error } = await supabase
    .from('divisions')
    .select('*, season:seasons(*)')
    .eq('id', divisionId)
    .maybeSingle()
  if (error) throw error
  return div
}

export async function getDivisionStandings(divisionId) {
  const { data, error } = await supabase
    .from('division_players')
    .select(`
      id, position, total_points, total_sets_won, total_sets_lost, rating_delta,
      player:players(id, name, rating, telegram_id)
    `)
    .eq('division_id', divisionId)
    .order('position', { ascending: true, nullsFirst: false })
  if (error) throw error
  const rows = data || []
  if (rows.length && !rows.some(r => r.position != null)) {
    rows.sort((a, b) => (b.total_points || 0) - (a.total_points || 0) || ((b.total_sets_won || 0) - (b.total_sets_lost || 0)) - ((a.total_sets_won || 0) - (a.total_sets_lost || 0)))
  }
  return rows
}

export async function getDivisionMatches(divisionId) {
  const { data: matches, error } = await supabase
    .from('matches')
    .select('id, player1_id, player2_id, sets_player1, sets_player2, status')
    .eq('division_id', divisionId)
  if (error) throw error
  const { data: standings } = await supabase
    .from('division_players')
    .select('player_id, player:players(id, name)')
    .eq('division_id', divisionId)
  const players = (standings || []).map(s => s.player || { id: s.player_id }).filter(Boolean)
  const matrix = {}
  for (const m of matches || []) {
    const key1 = `${m.player1_id}-${m.player2_id}`
    const key2 = `${m.player2_id}-${m.player1_id}`
    const score = m.status === 'played' ? `${m.sets_player1}-${m.sets_player2}` : null
    const cell = {
      score,
      status: m.status,
      matchId: m.id,
      player1_id: m.player1_id,
      player2_id: m.player2_id,
      sets1: m.sets_player1,
      sets2: m.sets_player2,
    }
    matrix[key1] = matrix[key2] = cell
  }
  return { players, matches: matches || [], matrix }
}

export async function getTopRating(limit = 50) {
  const { data, error } = await supabase
    .from('players')
    .select('id, name, rating, telegram_id')
    .order('rating', { ascending: false })
    .limit(limit)
  if (error) throw error
  return data || []
}

/** Rating list with games/wins for stats columns. Uses player_stats view if available. */
export async function getTopRatingWithStats(limit = 50) {
  const { data, error } = await supabase
    .from('player_stats')
    .select('id, name, rating, telegram_id, games, wins')
    .order('rating', { ascending: false })
    .limit(limit)
  if (error) {
    const fallback = await getTopRating(limit)
    return (fallback || []).map((p) => ({ ...p, games: null, wins: null }))
  }
  return data || []
}

export async function submitMatchResult(divisionId, player1Id, player2Id, sets1, sets2, submittedBy = null) {
  let existing = null
  const { data: r1 } = await supabase
    .from('matches')
    .select('id, status')
    .eq('division_id', divisionId)
    .eq('player1_id', player1Id)
    .eq('player2_id', player2Id)
    .maybeSingle()
  if (r1) existing = r1
  if (!existing) {
    const { data: r2 } = await supabase
      .from('matches')
      .select('id, status')
      .eq('division_id', divisionId)
      .eq('player1_id', player2Id)
      .eq('player2_id', player1Id)
      .maybeSingle()
    if (r2) existing = r2
  }
  if (existing?.status === 'played') {
    throw new Error('Этот матч уже внесён.')
  }

  const division = await getDivisionById(divisionId)
  if (!division) throw new Error('Дивизион не найден.')
  const divisionCoef = Number(division.coef) || 0.25
  const seasonId = division.season?.id || division.season_id
  if (!seasonId) throw new Error('Сезон дивизиона не найден.')

  const [{ data: p1 }, { data: p2 }] = await Promise.all([
    supabase.from('players').select('id, rating').eq('id', player1Id).single(),
    supabase.from('players').select('id, rating').eq('id', player2Id).single(),
  ])
  const r1Val = Number(p1?.rating) ?? 100
  const r2Val = Number(p2?.rating) ?? 100

  const s1 = Number(sets1) || 0
  const s2 = Number(sets2) || 0
  const winnerId = s1 > s2 ? player1Id : player2Id
  const loserId = s1 > s2 ? player2Id : player1Id
  const winnerSets = s1 > s2 ? s1 : s2
  const loserSets = s1 > s2 ? s2 : s1
  const winnerRatingBefore = s1 > s2 ? r1Val : r2Val
  const loserRatingBefore = s1 > s2 ? r2Val : r1Val

  const { deltaWinner, deltaLoser } = calculateMatchRating(
    winnerRatingBefore,
    loserRatingBefore,
    winnerSets,
    loserSets,
    divisionCoef
  )
  const winnerRatingAfter = Math.round((winnerRatingBefore + deltaWinner) * 100) / 100
  const loserRatingAfter = Math.round((loserRatingBefore + deltaLoser) * 100) / 100

  const pointsWinner = 2
  const pointsLoser = 1

  const payload = {
    division_id: divisionId,
    player1_id: player1Id,
    player2_id: player2Id,
    sets_player1: sets1,
    sets_player2: sets2,
    status: 'played',
    played_at: new Date().toISOString(),
  }
  if (submittedBy) payload.submitted_by = submittedBy

  let matchRow
  if (existing?.id) {
    const { data, error } = await supabase
      .from('matches')
      .update(payload)
      .eq('id', existing.id)
      .select()
      .single()
    if (error) throw error
    matchRow = data
  } else {
    const { data, error } = await supabase
      .from('matches')
      .insert(payload)
      .select()
      .single()
    if (error) throw error
    matchRow = data
  }

  const matchId = matchRow.id

  const [winnerUpdate, loserUpdate] = await Promise.all([
    supabase.from('players').update({ rating: winnerRatingAfter }).eq('id', winnerId),
    supabase.from('players').update({ rating: loserRatingAfter }).eq('id', loserId),
  ])
  if (winnerUpdate.error) throw winnerUpdate.error
  if (loserUpdate.error) throw loserUpdate.error

  const { data: dpWinner, error: errDpWinner } = await supabase
    .from('division_players')
    .select('id, total_points, total_sets_won, total_sets_lost, rating_delta')
    .eq('division_id', divisionId)
    .eq('player_id', winnerId)
    .single()
  if (errDpWinner) throw errDpWinner
  const { data: dpLoser, error: errDpLoser } = await supabase
    .from('division_players')
    .select('id, total_points, total_sets_won, total_sets_lost, rating_delta')
    .eq('division_id', divisionId)
    .eq('player_id', loserId)
    .single()
  if (errDpLoser) throw errDpLoser

  if (dpWinner) {
    const { error: errUpWinner } = await supabase
      .from('division_players')
      .update({
        total_points: (dpWinner.total_points || 0) + pointsWinner,
        total_sets_won: (dpWinner.total_sets_won || 0) + winnerSets,
        total_sets_lost: (dpWinner.total_sets_lost || 0) + loserSets,
        rating_delta: Math.round(((dpWinner.rating_delta || 0) + deltaWinner) * 100) / 100,
      })
      .eq('id', dpWinner.id)
    if (errUpWinner) throw errUpWinner
  }
  if (dpLoser) {
    const { error: errUpLoser } = await supabase
      .from('division_players')
      .update({
        total_points: (dpLoser.total_points || 0) + pointsLoser,
        total_sets_won: (dpLoser.total_sets_won || 0) + loserSets,
        total_sets_lost: (dpLoser.total_sets_lost || 0) + winnerSets,
        rating_delta: Math.round(((dpLoser.rating_delta || 0) + deltaLoser) * 100) / 100,
      })
      .eq('id', dpLoser.id)
    if (errUpLoser) throw errUpLoser
  }

  const { error: errHistory } = await supabase.from('rating_history').insert([
    {
      player_id: winnerId,
      match_id: matchId,
      season_id: seasonId,
      rating_before: winnerRatingBefore,
      rating_delta: deltaWinner,
      rating_after: winnerRatingAfter,
    },
    {
      player_id: loserId,
      match_id: matchId,
      season_id: seasonId,
      rating_before: loserRatingBefore,
      rating_delta: deltaLoser,
      rating_after: loserRatingAfter,
    },
  ])
  if (errHistory) throw errHistory

  return matchRow
}
