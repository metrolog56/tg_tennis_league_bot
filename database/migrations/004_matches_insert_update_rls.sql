-- Разрешить вставку и обновление матчей из Mini App (anon-ключ).
-- Без этих политик при вводе результата матча возникает:
-- "new row violates row-level security policy for table 'matches'"
CREATE POLICY "Allow insert matches" ON matches
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow update matches" ON matches
  FOR UPDATE USING (true);
