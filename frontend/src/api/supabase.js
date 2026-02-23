import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL
const key = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!url || !key) {
  console.warn('VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY not set')
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
    matrix[key1] = matrix[key2] = { score, status: m.status, matchId: m.id, sets1: m.sets_player1, sets2: m.sets_player2 }
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

export async function submitMatchResult(divisionId, player1Id, player2Id, sets1, sets2) {
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
  const payload = {
    division_id: divisionId,
    player1_id: player1Id,
    player2_id: player2Id,
    sets_player1: sets1,
    sets_player2: sets2,
    status: 'played',
    played_at: new Date().toISOString(),
  }
  if (existing?.id) {
    const { data, error } = await supabase
      .from('matches')
      .update(payload)
      .eq('id', existing.id)
      .select()
      .single()
    if (error) throw error
    return data
  }
  const { data, error } = await supabase
    .from('matches')
    .insert(payload)
    .select()
    .single()
  if (error) throw error
  return data
}
