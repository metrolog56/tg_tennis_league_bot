-- =============================================
-- 14 тестовых игроков для проверки дивизионов
-- Дивизион 1 уже создан и active. Дивизион 2 создаётся при необходимости.
-- =============================================

-- Создать дивизион 2 в текущем активном сезоне, если его ещё нет
INSERT INTO divisions (season_id, number, coef)
SELECT id, 2, 0.27
FROM seasons
WHERE status = 'active'
ORDER BY year DESC, month DESC
LIMIT 1
ON CONFLICT (season_id, number) DO NOTHING;

-- 14 игроков (telegram_id 200001–200014). При конфликте по telegram_id — обновляем имя и рейтинг
INSERT INTO players (id, telegram_id, telegram_username, name, rating) VALUES
  ('b1000001-0001-0001-0001-000000000001', 200001, 'test01', 'Тест Игрок 1', 120.00),
  ('b1000001-0001-0001-0001-000000000002', 200002, 'test02', 'Тест Игрок 2', 115.00),
  ('b1000001-0001-0001-0001-000000000003', 200003, 'test03', 'Тест Игрок 3', 110.00),
  ('b1000001-0001-0001-0001-000000000004', 200004, 'test04', 'Тест Игрок 4', 105.00),
  ('b1000001-0001-0001-0001-000000000005', 200005, 'test05', 'Тест Игрок 5', 100.00),
  ('b1000001-0001-0001-0001-000000000006', 200006, 'test06', 'Тест Игрок 6', 98.00),
  ('b1000001-0001-0001-0001-000000000007', 200007, 'test07', 'Тест Игрок 7', 95.00),
  ('b1000001-0001-0001-0001-000000000008', 200008, 'test08', 'Тест Игрок 8', 92.00),
  ('b1000001-0001-0001-0001-000000000009', 200009, 'test09', 'Тест Игрок 9', 90.00),
  ('b1000001-0001-0001-0001-00000000000a', 200010, 'test10', 'Тест Игрок 10', 88.00),
  ('b1000001-0001-0001-0001-00000000000b', 200011, 'test11', 'Тест Игрок 11', 85.00),
  ('b1000001-0001-0001-0001-00000000000c', 200012, 'test12', 'Тест Игрок 12', 82.00),
  ('b1000001-0001-0001-0001-00000000000d', 200013, 'test13', 'Тест Игрок 13', 80.00),
  ('b1000001-0001-0001-0001-00000000000e', 200014, 'test14', 'Тест Игрок 14', 78.00)
ON CONFLICT (telegram_id) DO UPDATE SET
  name = EXCLUDED.name,
  rating = EXCLUDED.rating,
  telegram_username = EXCLUDED.telegram_username;

-- Привязать игроков 1–8 к дивизиону 1, игроков 9–14 к дивизиону 2 (активный сезон)
INSERT INTO division_players (division_id, player_id)
SELECT d.id, p.id
FROM divisions d
CROSS JOIN (
  VALUES
    ('b1000001-0001-0001-0001-000000000001'::uuid),
    ('b1000001-0001-0001-0001-000000000002'::uuid),
    ('b1000001-0001-0001-0001-000000000003'::uuid),
    ('b1000001-0001-0001-0001-000000000004'::uuid),
    ('b1000001-0001-0001-0001-000000000005'::uuid),
    ('b1000001-0001-0001-0001-000000000006'::uuid),
    ('b1000001-0001-0001-0001-000000000007'::uuid),
    ('b1000001-0001-0001-0001-000000000008'::uuid)
) AS p(id)
WHERE d.season_id = (SELECT id FROM seasons WHERE status = 'active' ORDER BY year DESC, month DESC LIMIT 1)
  AND d.number = 1
ON CONFLICT (division_id, player_id) DO NOTHING;

INSERT INTO division_players (division_id, player_id)
SELECT d.id, p.id
FROM divisions d
CROSS JOIN (
  VALUES
    ('b1000001-0001-0001-0001-000000000009'::uuid),
    ('b1000001-0001-0001-0001-00000000000a'::uuid),
    ('b1000001-0001-0001-0001-00000000000b'::uuid),
    ('b1000001-0001-0001-0001-00000000000c'::uuid),
    ('b1000001-0001-0001-0001-00000000000d'::uuid),
    ('b1000001-0001-0001-0001-00000000000e'::uuid)
) AS p(id)
WHERE d.season_id = (SELECT id FROM seasons WHERE status = 'active' ORDER BY year DESC, month DESC LIMIT 1)
  AND d.number = 2
ON CONFLICT (division_id, player_id) DO NOTHING;
