-- Запросы на игру ("Хочу сыграть")
CREATE TABLE IF NOT EXISTS game_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID NOT NULL REFERENCES players(id),
    division_id UUID REFERENCES divisions(id),
    type VARCHAR(20) NOT NULL CHECK (type IN ('division', 'casual')),
    status VARCHAR(20) DEFAULT 'active'
        CHECK (status IN ('active', 'accepted', 'expired', 'cancelled')),
    accepted_by UUID REFERENCES players(id),
    notification_sent_at TIMESTAMP WITH TIME ZONE,
    accepted_notification_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '12 hours')
);

CREATE INDEX IF NOT EXISTS idx_game_requests_status ON game_requests(status);
CREATE INDEX IF NOT EXISTS idx_game_requests_player_id ON game_requests(player_id);
CREATE INDEX IF NOT EXISTS idx_game_requests_division_id ON game_requests(division_id);

ALTER TABLE game_requests ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can view game_requests" ON game_requests FOR SELECT USING (true);
CREATE POLICY "Allow insert game_requests" ON game_requests FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow update game_requests" ON game_requests FOR UPDATE USING (true);
