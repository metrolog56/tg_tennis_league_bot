-- Поддержка VK: второй платформенный идентификатор
ALTER TABLE players ADD COLUMN IF NOT EXISTS vk_id BIGINT UNIQUE;
CREATE INDEX IF NOT EXISTS idx_players_vk_id ON players(vk_id);

-- Коды привязки аккаунтов (TG <-> VK)
CREATE TABLE IF NOT EXISTS link_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID NOT NULL REFERENCES players(id),
    code VARCHAR(6) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '10 minutes'),
    used BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_link_codes_code ON link_codes(code);

ALTER TABLE link_codes ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can view link_codes" ON link_codes FOR SELECT USING (true);
CREATE POLICY "Allow insert link_codes" ON link_codes FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow update link_codes" ON link_codes FOR UPDATE USING (true);
