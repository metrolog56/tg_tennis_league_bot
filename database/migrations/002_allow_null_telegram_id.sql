-- Разрешить telegram_id = NULL для импорта игроков (заполнится при первом /start)
ALTER TABLE players ALTER COLUMN telegram_id DROP NOT NULL;
