-- Разрешить вставку в players для регистрации по /start (anon или service_role)
CREATE POLICY "Allow insert players" ON players
  FOR INSERT WITH CHECK (true);
