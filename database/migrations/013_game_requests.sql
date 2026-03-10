-- Game requests: division challenges and open "looking for game" requests.
-- expires_at is computed by the API as the next 21:00 Moscow time (UTC+3).

CREATE TABLE IF NOT EXISTS game_requests (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requester_id         UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    target_player_id     UUID REFERENCES players(id) ON DELETE SET NULL,
    type                 VARCHAR(30) NOT NULL CHECK (type IN ('division_challenge', 'open_league', 'open_casual')),
    message              TEXT,
    status               VARCHAR(20) NOT NULL DEFAULT 'pending'
                         CHECK (status IN ('pending', 'accepted', 'cancelled', 'expired')),
    accepted_by_id       UUID REFERENCES players(id) ON DELETE SET NULL,
    season_id            UUID REFERENCES seasons(id) ON DELETE SET NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at           TIMESTAMPTZ NOT NULL,
    notification_sent_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_game_requests_status    ON game_requests(status);
CREATE INDEX IF NOT EXISTS idx_game_requests_requester ON game_requests(requester_id);
CREATE INDEX IF NOT EXISTS idx_game_requests_target    ON game_requests(target_player_id);
CREATE INDEX IF NOT EXISTS idx_game_requests_season    ON game_requests(season_id);
CREATE INDEX IF NOT EXISTS idx_game_requests_expires   ON game_requests(expires_at);
