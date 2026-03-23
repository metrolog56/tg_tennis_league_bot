-- Link league players with web-first authentication identity (Supabase Auth user id)
ALTER TABLE players
ADD COLUMN IF NOT EXISTS auth_user_id UUID UNIQUE;

ALTER TABLE players
ADD COLUMN IF NOT EXISTS email VARCHAR(255);

CREATE UNIQUE INDEX IF NOT EXISTS idx_players_auth_user_id ON players(auth_user_id);
CREATE INDEX IF NOT EXISTS idx_players_email ON players(email);
