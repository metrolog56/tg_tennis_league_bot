-- Сессии/визиты с данными о клиенте (устройство, браузер, разрешение, язык)
CREATE TABLE IF NOT EXISTS client_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(id) ON DELETE SET NULL,
    platform VARCHAR(20),

    device_type VARCHAR(50),
    browser VARCHAR(100),
    browser_version VARCHAR(50),
    resolution VARCHAR(30),
    language VARCHAR(20),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_client_sessions_player_id ON client_sessions(player_id);
CREATE INDEX IF NOT EXISTS idx_client_sessions_created_at ON client_sessions(created_at);

ALTER TABLE client_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow insert client_sessions" ON client_sessions FOR INSERT WITH CHECK (true);
CREATE POLICY "Anyone can view client_sessions" ON client_sessions FOR SELECT USING (true);
