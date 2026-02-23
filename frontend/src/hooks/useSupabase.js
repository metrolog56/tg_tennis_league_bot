import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../api/supabase'

/**
 * Хук для данных из Supabase: рейтинг, мой дивизион, дивизион по id с матчами.
 */
export function useSupabase() {
  const [ratingList, setRatingList] = useState([])
  const [myDivision, setMyDivision] = useState(null)
  const [divisionWithMatches, setDivisionWithMatches] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadRating = useCallback(async () => {
    const { data, error: e } = await supabase
      .from('players')
      .select('id, name, rating')
      .order('rating', { ascending: false })
    if (e) {
      setError(e.message)
      return
    }
    setRatingList(data ?? [])
  }, [])

  const loadMyDivision = useCallback(async (telegramId) => {
    if (!telegramId) return
    const { data: player } = await supabase.from('players').select('id').eq('telegram_id', telegramId).single()
    if (!player) return
    const { data: dp } = await supabase
      .from('division_players')
      .select(`
        id, position, total_points, total_sets_won, total_sets_lost,
        division:divisions(id, number, coef, season:seasons(id, name))
      `)
      .eq('player_id', player.id)
      .order('created_at', { ascending: false })
      .limit(1)
      .single()
    if (!dp) return
    const divId = dp.division?.id
    if (!divId) return
    const { data: players } = await supabase
      .from('division_players')
      .select(`
        id, position, total_points, total_sets_won, total_sets_lost,
        player:players(id, name, rating)
      `)
      .eq('division_id', divId)
      .order('position')
    setMyDivision({
      division: dp.division,
      season: dp.division?.season,
      players: players ?? [],
    })
  }, [])

  const getDivision = useCallback(async (divisionId) => {
    setLoading(true)
    setError('')
    try {
      const { data: div, error: e1 } = await supabase
        .from('divisions')
        .select('id, number, coef')
        .eq('id', divisionId)
        .single()
      if (e1 || !div) {
        setError(e1?.message || 'Дивизион не найден')
        setDivisionWithMatches(null)
        return
      }
      const { data: dps } = await supabase
        .from('division_players')
        .select('id, position, player:players(id, name)')
        .eq('division_id', divisionId)
        .order('position')
      const { data: matches } = await supabase
        .from('matches')
        .select('id, player1_id, player2_id, sets_player1, sets_player2, status')
        .eq('division_id', divisionId)
      setDivisionWithMatches({
        ...div,
        division_players: dps ?? [],
        matches: matches ?? [],
      })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      setLoading(true)
      setError('')
      try {
        await loadRating()
        const tg = window.Telegram?.WebApp
        const uid = tg?.initDataUnsafe?.user?.id
        if (uid && !cancelled) await loadMyDivision(uid)
      } catch (e) {
        if (!cancelled) setError(e?.message || 'Ошибка загрузки')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    run()
    return () => { cancelled = true }
  }, [loadRating, loadMyDivision])

  return {
    ratingList,
    myDivision,
    divisionWithMatches,
    loading,
    error,
    getDivision,
    loadRating,
  }
}
