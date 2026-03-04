-- Manual stats override for rating page.
-- Creates table manual_player_stats and updates player_stats view
-- to prefer manual values when they exist.

CREATE TABLE IF NOT EXISTS manual_player_stats (
  player_id UUID PRIMARY KEY REFERENCES players(id) ON DELETE CASCADE,
  games INTEGER NOT NULL,
  wins INTEGER NOT NULL
);

CREATE OR REPLACE VIEW player_stats AS
SELECT
  p.id,
  p.name,
  p.rating,
  p.telegram_id,
  COALESCE(mps.games,
           COUNT(m.id) FILTER (WHERE m.status = 'played'))::int AS games,
  COALESCE(mps.wins,
           COUNT(m.id) FILTER (WHERE m.status = 'played' AND (
             (m.player1_id = p.id AND m.sets_player1 > m.sets_player2) OR
             (m.player2_id = p.id AND m.sets_player2 > m.sets_player1)
           )))::int AS wins
FROM players p
LEFT JOIN matches m ON m.player1_id = p.id OR m.player2_id = p.id
LEFT JOIN manual_player_stats mps ON mps.player_id = p.id
GROUP BY
  p.id,
  p.name,
  p.rating,
  p.telegram_id,
  mps.games,
  mps.wins;

