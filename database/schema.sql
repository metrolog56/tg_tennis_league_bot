-- =============================================
-- Лига настольного тенниса — полная схема БД
-- Supabase (PostgreSQL)
-- =============================================

-- Игроки
CREATE TABLE players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT UNIQUE NOT NULL,
    telegram_username VARCHAR(255),
    name VARCHAR(255) NOT NULL,
    rating DECIMAL(10,2) DEFAULT 100.00,
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Сезоны (туры — по месяцу)
CREATE TABLE seasons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    name VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'closed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(year, month)
);

-- Дивизионы
CREATE TABLE divisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    season_id UUID REFERENCES seasons(id) ON DELETE CASCADE,
    number INTEGER NOT NULL,
    coef DECIMAL(4,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(season_id, number)
);

-- Участники дивизиона
CREATE TABLE division_players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    division_id UUID REFERENCES divisions(id) ON DELETE CASCADE,
    player_id UUID REFERENCES players(id) ON DELETE CASCADE,
    position INTEGER,
    total_points INTEGER DEFAULT 0,
    total_sets_won INTEGER DEFAULT 0,
    total_sets_lost INTEGER DEFAULT 0,
    rating_delta DECIMAL(10,2) DEFAULT 0,
    UNIQUE(division_id, player_id)
);

-- Матчи
CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    division_id UUID REFERENCES divisions(id) ON DELETE CASCADE,
    player1_id UUID REFERENCES players(id),
    player2_id UUID REFERENCES players(id),
    sets_player1 INTEGER CHECK (sets_player1 BETWEEN 0 AND 3),
    sets_player2 INTEGER CHECK (sets_player2 BETWEEN 0 AND 3),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'played', 'not_played')),
    submitted_by UUID REFERENCES players(id),
    played_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(division_id, player1_id, player2_id),
    CHECK (player1_id != player2_id)
);

-- История рейтинга
CREATE TABLE rating_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES players(id),
    match_id UUID REFERENCES matches(id),
    season_id UUID REFERENCES seasons(id),
    rating_before DECIMAL(10,2),
    rating_delta DECIMAL(10,2),
    rating_after DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для частых запросов
CREATE INDEX idx_players_telegram_id ON players(telegram_id);
CREATE INDEX idx_players_rating ON players(rating DESC);
CREATE INDEX idx_seasons_year_month ON seasons(year, month);
CREATE INDEX idx_divisions_season_id ON divisions(season_id);
CREATE INDEX idx_division_players_division_id ON division_players(division_id);
CREATE INDEX idx_division_players_player_id ON division_players(player_id);
CREATE INDEX idx_matches_division_id ON matches(division_id);
CREATE INDEX idx_matches_player1_player2 ON matches(player1_id, player2_id);
CREATE INDEX idx_rating_history_player_id ON rating_history(player_id);
CREATE INDEX idx_rating_history_season_id ON rating_history(season_id);

-- RLS политики для Supabase
ALTER TABLE players ENABLE ROW LEVEL SECURITY;
ALTER TABLE seasons ENABLE ROW LEVEL SECURITY;
ALTER TABLE divisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE division_players ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE rating_history ENABLE ROW LEVEL SECURITY;

-- Читать могут все аутентифицированные
CREATE POLICY "Anyone can view players" ON players FOR SELECT USING (true);
CREATE POLICY "Anyone can view seasons" ON seasons FOR SELECT USING (true);
CREATE POLICY "Anyone can view divisions" ON divisions FOR SELECT USING (true);
CREATE POLICY "Anyone can view division_players" ON division_players FOR SELECT USING (true);
CREATE POLICY "Anyone can view matches" ON matches FOR SELECT USING (true);
CREATE POLICY "Anyone can view rating_history" ON rating_history FOR SELECT USING (true);
