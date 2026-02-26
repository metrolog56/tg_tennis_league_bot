-- Подтверждение результата вторым игроком: новый статус и отметка об уведомлении
ALTER TABLE matches DROP CONSTRAINT IF EXISTS matches_status_check;
ALTER TABLE matches ADD CONSTRAINT matches_status_check
  CHECK (status IN ('pending', 'played', 'not_played', 'pending_confirm'));

ALTER TABLE matches ADD COLUMN IF NOT EXISTS notification_sent_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;
