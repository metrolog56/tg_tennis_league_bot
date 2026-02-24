-- Разрешить Mini App (anon) обновлять рейтинг игроков и очки в дивизионе при вводе результата матча.
CREATE POLICY "Allow update players" ON players FOR UPDATE USING (true);

CREATE POLICY "Allow update division_players" ON division_players FOR UPDATE USING (true);

CREATE POLICY "Allow insert rating_history" ON rating_history FOR INSERT WITH CHECK (true);
