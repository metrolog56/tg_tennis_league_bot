# Postman — Tennis League API

Коллекция запросов для REST API лиги настольного тенниса.

## Импорт

1. Откройте Postman.
2. **Import** → **File** → выберите `Tennis-League-API.postman_collection.json`.
3. Коллекция появится в боковой панели.

Альтернатива: импорт из OpenAPI — в Postman **Import** → **Link** и укажите `http://localhost:8000/openapi.json` (при запущенном API). После импорта нужно вручную добавить заголовки `X-API-Key`, `Authorization: Bearer {{access_token}}` и примеры тел запросов.

## Переменные коллекции

Задайте значения в **Collection** → **Tennis League API** → вкладка **Variables**:

| Переменная     | Описание |
|----------------|----------|
| `baseUrl`      | Базовый URL API, по умолчанию `http://localhost:8000`. |
| `apiKey`       | Значение заголовка `X-API-Key`. Нужен, если на сервере задан `API_KEY`. |
| `access_token` | JWT после успешного `POST /auth/telegram` или `POST /auth/web` (заголовок `Authorization: Bearer {{access_token}}`). |
| `divisionId`   | UUID дивизиона — для запросов к дивизиону и при submit/confirm матча. |
| `seasonId`     | UUID сезона — для запросов по сезону и фильтра заявок на игру. |
| `matchId`      | UUID матча — для confirm/reject/notify. |
| `requestId`    | UUID заявки на игру — для accept/cancel. |

Секреты (API key, JWT) в коллекцию не подставляйте — храните их в переменных окружения Postman или в .env вне репозитория.

## Структура коллекции

- **Auth** — root, health, обмен Telegram initData на JWT.
- **Players** — игрок по telegram_id, рейтинг, обновление имени.
- **Seasons** — текущий сезон, дивизионы сезона.
- **Divisions** — дивизион, турнирная таблица, матчи (матрица).
- **Matches** — pending, один матч, submit/confirm/reject, notify, админ recalc и consistency report.
- **Game requests** — создание, список, accept, cancel.
- **Client sessions** — запись сессии (аналитика).

Полное описание API: [Swagger](http://localhost:8000/docs), OpenAPI: `GET /openapi.json`.
