# 🏓 Лига настольного тенниса — Telegram Mini App

Приложение для управления лигой настольного тенниса: рейтинг, дивизионы, ввод результатов матчей. Telegram Bot + Mini App (React) + Supabase.

В лиге мы руководствуемся принципом **«Уважение в лиге»** 🤝 — к сопернику и к сыгранной игре. Подробнее: [docs/PRINCIPLES.md](docs/PRINCIPLES.md).

## Структура проекта

```
tg_tennis_league_bot/
├── api/                  # REST API (FastAPI + Swagger)
├── bot/                  # Telegram-бот (Python, aiogram 3)
├── frontend/             # Mini App (React + Vite + Tailwind)
├── database/             # Схема и миграции БД (Supabase)
├── docs/                 # Документация (в т.ч. openapi-supabase.yaml)
├── scripts/              # Импорт из CSV и др.
├── .github/workflows/    # Деплой фронта на GitHub Pages
└── README.md
```

---

## 1. Создать бота в @BotFather

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram.
2. Отправьте `/newbot`, укажите имя и username бота.
3. Сохраните **токен** (например, `123456:ABC-DEF...`). Он понадобится для `BOT_TOKEN`.

---

## 2. Создать проект в Supabase

1. Зайдите на [supabase.com](https://supabase.com) и создайте новый проект.
2. В **SQL Editor** выполните скрипт из файла **`database/schema.sql`** целиком.
3. Если планируете импорт игроков из CSV с `telegram_id = NULL`, выполните миграцию:
   - **`database/migrations/002_allow_null_telegram_id.sql`**
4. (Опционально) Выполните **`database/seed.sql`** для тестовых данных.
5. Для столбцов «Игры», «В», «П», «%» на странице Рейтинг выполните **`database/migrations/006_player_stats_view.sql`** (создаёт представление `player_stats`).
6. Для обновления главной в реальном времени (когда соперник вносит результат) выполните **`database/migrations/011_realtime_matches.sql`** (добавляет таблицу `matches` в публикацию Realtime).
7. В настройках проекта (**Settings → API**) скопируйте:
   - **Project URL** → для `SUPABASE_URL`
   - **anon public** → для фронта и бота (или **service_role** только для бота, если нужны права на запись без RLS).
   - Если шаг 5 пропущен, страница Рейтинг покажет рейтинг без столбцов Игры/В/П/%.

---

## 3. Настроить .env файлы

### Бот (`bot/.env`)

Скопируйте `bot/.env.example` в `bot/.env` и заполните:

```env
BOT_TOKEN=ваш_токен_от_BotFather
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=ваш_anon_или_service_role_ключ
ADMIN_TELEGRAM_ID=ваш_telegram_id
WEBAPP_URL=https://yourusername.github.io/репозиторий/tennis-league/
```

- **ADMIN_TELEGRAM_ID** — ваш Telegram ID (например, из [@userinfobot](https://t.me/userinfobot)), для админ-команд и отчёта о закрытии тура.
- **WEBAPP_URL** — URL Mini App после деплоя на GitHub Pages.

**Саморегистрация по /start без миграции в Supabase:** если вы не применяете миграцию `003_allow_insert_players.sql`, в `SUPABASE_KEY` нужно указать ключ **service_role** (Supabase → Settings → API → service_role secret). Тогда RLS не блокирует вставку в таблицу `players`, и игроки смогут регистрироваться по команде /start. Ключ service_role храните только в `bot/.env`, не используйте его во фронтенде.

### Фронтенд (`frontend/.env`)

Скопируйте `frontend/.env.example` в `frontend/.env`:

```env
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=ваш_anon_ключ
```

---

## 4. Запустить бота локально

```bash
cd bot
pip install -r requirements.txt
python3 main.py
```

На macOS команда может называться `python3` (если `python` не найден). Бот запустится в режиме long polling. Планировщик каждый день в **23:55** проверяет, последний ли день месяца; если да — закрывает тур и создаёт следующий сезон с ротацией.

---

## 4.1. REST API (опционально)

В каталоге **api/** — REST API на FastAPI с автоматической документацией Swagger.

**Запуск (из корня репозитория):**

```bash
pip install -r api/requirements.txt
# Скопируйте api/.env.example в api/.env и укажите SUPABASE_URL, SUPABASE_KEY
uvicorn api.main:app --reload
```

- **Swagger UI (REST API):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Справка по операциям Supabase (фронт):** [http://localhost:8000/docs-supabase](http://localhost:8000/docs-supabase)

Переменные окружения — те же, что у бота (`SUPABASE_URL`, `SUPABASE_KEY`). Опционально можно задать `API_KEY` и тогда запросы к API должны содержать заголовок `X-API-Key`.

**Мгновенное уведомление и обновление в реальном времени:** если нужна мгновенная отправка сообщения в Telegram сопернику (без ожидания планировщика раз в 2 мин) и обновление экрана у второго игрока без перезагрузки:
- Примените миграцию **`database/migrations/011_realtime_matches.sql`** в Supabase.
- В боте задайте `NOTIFY_LISTEN_PORT=8765` и `NOTIFY_SECRET` (общий секрет с API).
- В API задайте `BOT_NOTIFY_URL=http://<хост_бота>:8765` и тот же `NOTIFY_SECRET`.
- Во фронте задайте `VITE_API_URL` — базовый URL API (например `https://your-api.example.com`). Тогда после внесения результата фронт вызовет API, API запросит бота — соперник получит сообщение сразу; при открытом приложении данные обновятся по Realtime.

---

## 5. Настроить GitHub Pages для frontend

1. В репозитории на GitHub: **Settings → Pages**.
2. В разделе **Build and deployment** выберите **Source: GitHub Actions**.
3. В **Settings → Secrets and variables → Actions** добавьте секреты:
   - **VITE_SUPABASE_URL** — Project URL из Supabase.
   - **VITE_SUPABASE_KEY** — anon public ключ из Supabase.
4. После пуша в ветку **main** с изменениями в **frontend/** workflow соберёт проект и задеплоит его на GitHub Pages.
5. URL приложения будет: `https://<username>.github.io/<repo>/tennis-league/` (если в `vite.config.js` указано `base: '/tennis-league/'`).

Чтобы в сборке использовался `npm ci`, закоммитьте **`frontend/package-lock.json`** (создаётся после `npm install` в каталоге `frontend`).

---

## 5.1. Разработка: тесты и Swagger

**Тесты**

- Запуск всех тестов из корня репозитория: **`make test`** (требуется Make).
- По отдельности: **`make test-api`** (API: проверка X-API-Key, эндпоинты), **`make test-bot`** (бот: расчёт рейтинга).
- Без Make: `PYTHONPATH=. python3 -m pytest api/tests -v` и `cd bot && python3 -m pytest tests -v`.

При пуше и pull request в **main** тесты автоматически запускаются в GitHub Actions (workflow **Tests** в `.github/workflows/tests.yml`). Перед коммитом удобно выполнять `make test` локально.

**Swagger (REST API)**

- Документация в **/docs** генерируется FastAPI из кода приложения. Отдельно «обновлять» Swagger не нужно: после изменений в роутерах и зависимостях достаточно перезапустить `uvicorn` (или использовать `--reload`) и обновить страницу `/docs`.
- Файл **docs/openapi-supabase.yaml** — ручная справочная спецификация операций фронта через Supabase; при изменении логики во фронте его при необходимости обновляют вручную.

**Рекомендации по ходу разработки**

1. Писать тесты для новой логики (API — в `api/tests/`, бот — в `bot/tests/`).
2. Перед коммитом запускать `make test` (или хотя бы тесты затронутого модуля).
3. После правок API проверять `/docs`: схема и кнопка Authorize (X-API-Key) подхватываются из кода автоматически.

**Проверка после релиза**

После деплоя (push в main, выкат на Railway/GitHub Pages и т.д.):

1. **GitHub Actions** — откройте вкладку **Actions** в репозитории. Убедитесь, что workflow **Tests** (и при наличии **Deploy Frontend**) завершился успешно (зелёная галочка). Так вы убеждаетесь, что тесты и сборка проходят на актуальном коде.
2. **Фронт (GitHub Pages)** — откройте URL Mini App в браузере, проверьте загрузку главной, рейтинга и ввод результата (по возможности — быстрый smoke).
3. **REST API** — если API задеплоен, откройте `https://<ваш-api>/health` — должен вернуться `{"status":"ok"}`. Документация: `https://<ваш-api>/docs`; при включённом `API_KEY` проверьте вызов защищённого эндпоинта с заголовком `X-API-Key`.
4. **Бот** — напишите боту в Telegram команду (например `/start` или запрос рейтинга), убедитесь, что ответ приходит и ссылка на Mini App открывается.

При падении тестов в CI до релиза — исправьте код и запушьте снова; после релиза при проблемах проверьте логи деплоя (Railway, Actions) и переменные окружения.

---

## 6. Зарегистрировать Mini App в @BotFather

1. В [@BotFather](https://t.me/BotFather) выберите вашего бота.
2. Отправьте команду **/newapp** (или через меню: Bot Settings → Menu Button).
3. Укажите название и URL вашего Mini App (тот же **WEBAPP_URL**, например `https://yourusername.github.io/your-repo/tennis-league/`).
4. При необходимости привяжите Mini App к кнопке меню бота.

---

## 7. Деплой бота на Railway

1. Установите [Railway CLI](https://docs.railway.app/develop/cli) (если ещё не установлен).
2. В каталоге проекта выполните:

```bash
railway login
railway init
```

3. Добавьте переменные окружения в Railway (Dashboard или `railway variables`):
   - `BOT_TOKEN`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `ADMIN_TELEGRAM_ID`
   - `WEBAPP_URL`

4. Деплой из каталога **bot**:

```bash
cd bot
railway up
```

Либо укажите в настройках сервиса Railway корень сборки **bot** и используйте приложенный **Dockerfile** (в `bot/Dockerfile`):

- **Build**: Dockerfile в `bot/`.
- **Start**: `python main.py`.

**Если деплой падает (crashed):**

1. **Variables** — в Railway не подставляется локальный `bot/.env`. В Dashboard → сервис бота → **Variables** добавьте вручную: `BOT_TOKEN`, `SUPABASE_URL`, `SUPABASE_KEY`, `ADMIN_TELEGRAM_ID`, `WEBAPP_URL`. Без них бот падает при старте.
2. **Root Directory** — сборка должна идти из папки **bot** (в настройках сервиса укажите Root Directory = `bot` или деплойте из `cd bot && railway up`).
3. **Тип сервиса** — бот использует long polling, а не HTTP. Если в Railway есть выбор **Worker** vs **Web**, выберите **Worker**, чтобы не требовать привязки к порту.
4. После изменений пересоберите и задеплойте, затем **Deployments** → последний деплой → **View Logs** — в логах будет видно причину падения (например, отсутствие переменной или ошибка Supabase).

---

## Дополнительно

### Импорт игроков из CSV (экспорт из Google Sheets)

Если вы экспортировали таблицу в CSV (Файл → Скачать → CSV):

```bash
# Из корня проекта
python scripts/import_from_sheets.py path/to/export.csv
```

В CSV должны быть колонки **Имя** (или `name`) и **Рейтинг** (или `rating`). Игроки создаются с `telegram_id = NULL`; при первом запуске бота пользователь регистрируется по `/start`, при необходимости можно связать запись по имени вручную или доработать логику в боте.

Перед импортом выполните миграцию **`database/migrations/002_allow_null_telegram_id.sql`**.

### Тестирование на iOS Simulator

Проверка вёрстки, safe area и стиля «стекло» на размерах iPhone без физического устройства:

1. Установите **Xcode** (сайт Apple или App Store). В комплекте идёт **iOS Simulator** (Xcode → Open Developer Tool → Simulator или в терминале: `open -a Simulator`).
2. В симуляторе откройте **Safari** и перейдите по URL Mini App:
   - локально: `http://localhost:5173` (предварительно запустите `npm run dev` в каталоге `frontend/`);
   - либо продовый URL после деплоя на GitHub Pages.
3. Проверьте адаптив, нижнюю навигацию и отступы safe area (во фронте используются `env(safe-area-inset-*)`).

Официальный клиент Telegram из App Store в симуляторе часто недоступен, поэтому типичный сценарий — тест по прямому URL в Safari. Для отладки веб-страницы на реальном iPhone подключите устройство к Mac и используйте Safari на Mac (меню Develop → выбор устройства).

### Docker (бот)

```bash
cd bot
docker build -t tennis-league-bot .
docker run --env-file .env tennis-league-bot
```

### Регламент и рейтинг

- Тур = 1 месяц; в дивизионе все играют друг с другом.
- Матч: до 3 побед (Best of 5). Очки: победа 2, поражение 1, несыгранный 0.
- Ротация: топ-2 вверх, последние 2 вниз (если в дивизионе >8 — по 3).
- Рейтинг по формулам ФНТР (КД по дивизиону, КС по счёту). Новый игрок: рейтинг 100, последний дивизион.

Подробнее — в разделе «Правила» в Mini App и в **context_project.md**.

### Проверка корректности расчёта рейтинга

Формулы ФНТР: ПРв = (100 – (РТВ – РТП)) / 10 × КД × КС, ПРп = –(100 – (РТВ – РТП)) / 20 × КД × КС. КД по дивизиону (1→0,30; 2→0,27; 3→0,25; 4→0,22), КС по разнице сетов (1 сет→0,8; 2 сета→1,0; 3 сета→1,2).

- **Юнит-тесты:** в `bot/tests/test_rating.py` проверяются КС и дельты (равные рейтинги 100:100, КД 0,30, счёты 3:0, 3:1, 3:2). Запуск: `cd bot && pytest tests/test_rating.py -v`.
- **Сверка с таблицей:** регламент и примеры начисления — [Регламент (Google Sheets)](https://docs.google.com/spreadsheets/d/1zVgV_8Ob8B0JyIpcGUlKa4aigmJDhVmy4TIX58qTsQI/edit?gid=650497012); рейтинг и набранные очки по турам — [Рейтинг (Google Sheets)](https://docs.google.com/spreadsheets/d/1zVgV_8Ob8B0JyIpcGUlKa4aigmJDhVmy4TIX58qTsQI/edit?gid=2046316003). Выберите матч с известными рейтингами до игры и счётом, вычислите ПРв/ПРп по формулам (или через калькулятор ФНТР × КД × КС) и сравните с записью в приложении: таблица `rating_history` или обновлённый `division_players.rating_delta` и `players.rating`.
- **Где считается:** при внесении результата матча — бот (Python: `bot/services/rating_calculator.py`) и Mini App (JS: `frontend/src/utils/ratingCalc.js`). Логика должна совпадать; округление до 2 знаков после запятой.

---

## Структура БД

```
                    ┌─────────────────┐
                    │     players     │
                    ├─────────────────┤
                    │ id (PK)         │
                    │ telegram_id UK  │
                    │ name, rating    │
                    │ is_admin        │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│    seasons      │  │ division_players│  │ rating_history  │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ id (PK)         │  │ id (PK)         │  │ id (PK)         │
│ year, month UK  │  │ division_id FK  │  │ player_id FK    │
│ name, status    │  │ player_id FK    │  │ match_id FK     │
└────────┬────────┘  │ position        │  │ season_id FK    │
         │            │ total_points    │  │ rating_before   │
         │            │ total_sets_*   │  │ rating_delta    │
         ▼            │ rating_delta   │  │ rating_after    │
┌─────────────────┐  └────────┬────────┘  └─────────────────┘
│   divisions     │           │
├─────────────────┤           │
│ id (PK)         │           │
│ season_id FK     │◄──────────┘
│ number, coef    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     matches     │
├─────────────────┤
│ id (PK)         │
│ division_id FK  │
│ player1_id FK   │
│ player2_id FK   │
│ sets_player1/2  │
│ status          │
│ submitted_by FK │
└─────────────────┘
```

- **players** — игроки (telegram_id, рейтинг, имя).
- **seasons** — туры по месяцам (year, month, status: active/closed).
- **divisions** — дивизионы сезона (number, coef КД).
- **division_players** — участники дивизиона (position, очки, сеты, rating_delta).
- **matches** — матчи (player1/2, счёт, status: pending/played/not_played).
- **rating_history** — история изменения рейтинга за матч.
