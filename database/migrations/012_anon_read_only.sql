-- Anon key: only SELECT allowed. All writes go through API (service role).
-- See docs/SECURITY_OWASP_ANALYSIS.md and plan "Fix RLS allow-all Supabase".

DROP POLICY IF EXISTS "Allow insert players" ON players;
DROP POLICY IF EXISTS "Allow update players" ON players;

DROP POLICY IF EXISTS "Allow insert matches" ON matches;
DROP POLICY IF EXISTS "Allow update matches" ON matches;

DROP POLICY IF EXISTS "Allow update division_players" ON division_players;

DROP POLICY IF EXISTS "Allow insert rating_history" ON rating_history;

DROP POLICY IF EXISTS "Allow insert client_sessions" ON client_sessions;
