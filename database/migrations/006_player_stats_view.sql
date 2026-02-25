-- View for rating page: player + games played, wins (losses = games - wins).
-- Use: SELECT * FROM player_stats ORDER BY rating DESC
CREATE OR REPLACE VIEW player_stats AS
SELECT
  p.id,
  p.name,
  p.rating,
  p.telegram_id,
  COUNT(m.id) FILTER (WHERE m.status = 'played')::int AS games,
  COUNT(m.id) FILTER (WHERE m.status = 'played' AND (
    (m.player1_id = p.id AND m.sets_player1 > m.sets_player2) OR
    (m.player2_id = p.id AND m.sets_player2 > m.sets_player1)
  ))::int AS wins
FROM players p
LEFT JOIN matches m ON m.player1_id = p.id OR m.player2_id = p.id
GROUP BY p.id, p.name, p.rating, p.telegram_id;
