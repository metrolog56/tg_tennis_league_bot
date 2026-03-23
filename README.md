# 🏓 Лига настольного тенниса — Telegram Mini App

Приложение для управления лигой настольного тенниса: рейтинг, дивизионы, ввод результатов матчей. Telegram Bot + Mini App (React) + Supabase.

В лиге мы руководствуемся принципом **«Уважение в лиге»** 🤝 — к сопернику и к сыгранной игре. Подробнее: [docs/PRINCIPLES.md](docs/PRINCIPLES.md).

---

## Краткий регламент

- **Туры и дивизионы**: год разбит на туры по 1 месяцу; в каждом дивизионе 6–10 игроков, все играют друг с другом за месяц.
- **Формат матча**: Best of 5 (до 3 побед).
- **Очки**: победа = 2, поражение = 1, несыгранный = 0.
- **Ротация**: топ‑2 поднимаются вверх, последние‑2 спускаются вниз (если в дивизионе >8 игроков — по 3).
- **Новый игрок**: попадает в последний дивизион, начальный рейтинг = 100; пропуск тура не сбрасывает рейтинг.

### Рейтинг (ФНТР)

- Коэф. дивизиона (КД): дивизион 1 = 0.30, 2 = 0.27, 3 = 0.25, 4 = 0.22.
- Коэф. счёта (КС): 3:0 / 0:3 → 1.2; 3:1 / 1:3 → 1.0; 3:2 / 2:3 → 0.8.

```text
ПРв (победитель) = (100 – (РТВ – РТП)) / 10 * КД * КС
ПРп (проигравший) = –(100 – (РТВ – РТП)) / 20 * КД * КС
где РТВ — рейтинг победителя, РТП — рейтинг проигравшего.
```

### Техстек

- **Frontend**: React + Vite + Tailwind CSS (Telegram Mini App).
- **Backend Bot**: Python + aiogram 3.x.
- **БД**: Supabase (PostgreSQL).
- **Хостинг фронта**: GitHub Pages.
- **Хостинг бота**: Koyeb (worker‑сервис) или локально для разработки.
- **Авторизация**: Telegram (по `telegram_id`, без паролей).

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
VITE_API_URL=https://your-api.example.com
VITE_TELEGRAM_BOT_NAME=@your_bot
```

Для web-first входа включите **Supabase Auth (Email / Magic Link)** и примените миграцию
`database/migrations/014_players_web_auth.sql` (поля `players.auth_user_id`, `players.email`).
Пошаговый чек-лист выката: `docs/WEB_FIRST_ROLLOUT.md`.

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

Переменные окружения — те же, что у бота (`SUPABASE_URL`, `SUPABASE_KEY`). В API в **`SUPABASE_KEY`** должен быть ключ **service_role** (Supabase → Settings → API → service_role secret), не anon: мутации и проверки доступа выполняются от имени backend. Фронт использует только **anon** ключ (Settings → API → anon public) в своих переменных `VITE_SUPABASE_*`.

Опционально можно задать **`API_KEY`** — тогда запросы к API должны содержать заголовок `X-API-Key`. Для запросов из браузера (фронт, Mini App) задайте **`CORS_ORIGINS`** — через запятую список доверенных origin'ов (например `https://metrolog56.github.io,https://backup.metrolog56.ru,http://localhost:5173`). Для защиты от IDOR чувствительные операции требуют заголовок **`Authorization: Bearer <JWT>`**; идентичность игрока берётся только из токена (Bearer-only контракт). См. [docs/SECURITY_OWASP_ANALYSIS.md](docs/SECURITY_OWASP_ANALYSIS.md).

**Секреты в production:** в production обязательно задайте **`API_KEY`** (иначе проверка по X-API-Key отключена и API доступен без ключа). Если используете мгновенные уведомления — задайте **`NOTIFY_SECRET`** (общий с ботом), иначе возможна подделка запросов к боту и массовая отправка уведомлений.

**Ограничение частоты запросов (rate limiting):** для эндпоинтов `POST /auth/telegram` и `POST /matches/{id}/notify-pending` действует лимит 10 запросов в минуту с одного IP (по заголовку `X-Forwarded-For`, если API за прокси). При деплое нескольких инстансов API для точного лимита можно настроить ограничения на уровне nginx/облака или использовать хранилище Redis (см. slowapi).

**Мгновенное уведомление и обновление в реальном времени:** если нужна мгновенная отправка сообщения в Telegram сопернику (без ожидания планировщика раз в 2 мин) и обновление экрана у второго игрока без перезагрузки:
- Примените миграцию **`database/migrations/011_realtime_matches.sql`** в Supabase.
- В боте задайте `NOTIFY_LISTEN_PORT=8765` и `NOTIFY_SECRET` (общий секрет с API).
- В API задайте `BOT_NOTIFY_URL=http://<хост_бота>:8765` и тот же `NOTIFY_SECRET`.
- Во фронте задайте `VITE_API_URL` — базовый URL API (например `https://your-api.example.com`). Тогда после внесения результата фронт вызовет API, API запросит бота — соперник получит сообщение сразу; при открытом приложении данные обновятся по Realtime.

---

## 5. Web-first хостинг frontend (рекомендуется)

Для доступности в РФ лучше использовать Cloudflare Pages или Vercel + собственный домен.

1. Подключите репозиторий к Cloudflare Pages/Vercel.
2. Build command: `npm ci && npm run build`, output: `frontend/dist`.
3. Добавьте env vars из `frontend/.env.example` + `VITE_API_URL`.
4. Подключите домен `app.<ваш-домен>` и резервный `backup.<ваш-домен>`.
5. В `CORS_ORIGINS` API добавьте оба домена.

## 5.1. GitHub Pages для Mini App (дополнительно)

1. В репозитории на GitHub: **Settings → Pages**.
2. В разделе **Build and deployment** выберите **Source: GitHub Actions**.
3. В **Settings → Secrets and variables → Actions** добавьте секреты:
   - **VITE_SUPABASE_URL** — Project URL из Supabase.
   - **VITE_SUPABASE_KEY** — anon public ключ из Supabase.
4. После пуша в ветку **main** с изменениями в **frontend/** workflow соберёт проект и задеплоит его на GitHub Pages.
5. URL приложения будет: `https://<username>.github.io/<repo>/tennis-league/` (если в `vite.config.js` указано `base: '/tennis-league/'`).

Чтобы в сборке использовался `npm ci`, закоммитьте **`frontend/package-lock.json`** (создаётся после `npm install` в каталоге `frontend`).

---

## 5.2. Разработка: тесты и Swagger

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

После деплоя (push в main, выкат на Koyeb/GitHub Pages и т.д.):

1. **GitHub Actions** — откройте вкладку **Actions** в репозитории. Убедитесь, что workflow **Tests** (и при наличии **Deploy Frontend**) завершился успешно (зелёная галочка). Так вы убеждаетесь, что тесты и сборка проходят на актуальном коде.
2. **Фронт (GitHub Pages)** — откройте URL Mini App в браузере, проверьте загрузку главной, рейтинга и ввод результата (по возможности — быстрый smoke).
3. **REST API** — если API задеплоен, откройте `https://<ваш-api>/health` — должен вернуться `{"status":"ok"}`. Документация: `https://<ваш-api>/docs`; при включённом `API_KEY` проверьте вызов защищённого эндпоинта с заголовком `X-API-Key`.
4. **Бот** — напишите боту в Telegram команду (например `/start` или запрос рейтинга), убедитесь, что ответ приходит и ссылка на Mini App открывается.

При падении тестов в CI до релиза — исправьте код и запушьте снова; после релиза при проблемах проверьте логи деплоя (Actions) и переменные окружения.

---

## 6. Зарегистрировать Mini App в @BotFather

1. В [@BotFather](https://t.me/BotFather) выберите вашего бота.
2. Отправьте команду **/newapp** (или через меню: Bot Settings → Menu Button).
3. Укажите название и URL вашего Mini App (тот же **WEBAPP_URL**, например `https://yourusername.github.io/your-repo/tennis-league/`).
4. При необходимости привяжите Mini App к кнопке меню бота.

---

## 7. Деплой бота на Koyeb

Koyeb позволяет запускать фоновые **Worker**‑сервисы из Git‑репозитория или Docker‑образа; Supabase остаётся как есть, миграция БД не требуется.

### 7.1.1. Что понадобится

- Аккаунт на [koyeb.com](https://koyeb.com) (для доступа к бесплатному compute Koyeb требует привязку платёжного метода, но даёт ежемесячный бесплатный лимит).
- Репозиторий с проектом на GitHub (структура как в этом репо).
- Готовая Supabase‑БД (как описано выше).

Бот уже подготовлен к деплою: в каталоге `bot/` есть `Dockerfile`, `requirements.txt` и точка входа `main.py`, использующая long polling.

### 7.1.2. Шаги деплоя бота на Koyeb

1. **Подготовьте репозиторий**
   - Убедитесь, что изменения закоммичены и запушены в GitHub.
   - Проверьте локально:
     - `cd bot`
     - `pip install -r requirements.txt`
     - `python3 main.py`

2. **Создайте сервис в Koyeb**
   - Зайдите в панель Koyeb и нажмите **Create -> App**.
   - В качестве источника выберите **GitHub repository**, подключите свой репозиторий с проектом.
   - В настройках источника укажите:
     - **Branch**: ветка с продакшен‑кодом (обычно `main`).
     - **Build**:
       - Тип: **Dockerfile**.
       - Контекст: подкаталог `bot` (если Koyeb спрашивает рабочий каталог / workdir).
   - В разделе **Service type** выберите **Worker** (фоновый сервис без HTTP).

3. **Задайте переменные окружения**
   - В разделе **Environment variables** добавьте:
     - `BOT_TOKEN` — токен бота из @BotFather.
     - `SUPABASE_URL` — Project URL из Supabase.
     - `SUPABASE_KEY` — service_role ключ для бота.
     - `ADMIN_TELEGRAM_ID` — ваш Telegram ID.
     - `WEBAPP_URL` — URL Mini App на GitHub Pages.
     - (опционально) `NOTIFY_LISTEN_PORT`, `NOTIFY_SECRET` — если используете мгновенные уведомления через `notify_server.py` и API.

4. **Выберите регион**
   - В разделе **Region** выберите дата‑центр в Европе (например, Frankfurt/Amsterdam) — это будет ближе всего к России по задержкам.

5. **Разверните сервис**
   - Нажмите **Deploy** и дождитесь сборки и старта.
   - Откройте логи сервиса:
     - Убедитесь, что бот успешно подключился к Telegram и Supabase.
     - При ошибках (неверный токен, переменные окружения) они будут видны в логах.

После успешного деплоя бот будет работать как фоновый long polling‑процесс, который обрабатывает обновления и планировщик закрытия туров.

### 7.2. Один контейнер (API + бот) — один сервис Koyeb

Чтобы развернуть и API, и бота **одним сервисом** (один слот на Free tier, один URL для пинга, уведомления через localhost):

1. **Сборка:** в корне репозитория есть общий **`Dockerfile`** и **`docker/entrypoint.sh`**. В одном контейнере запускаются uvicorn (API на порту 8000) и бот (health бота на 8001, чтобы не конфликтовать с API).

2. **Создайте сервис в Koyeb**
   - Source: ваш репозиторий, ветка `main`.
   - Build: **Dockerfile**, расположение **`Dockerfile`** (корень репо), контекст сборки — корень репозитория.
   - **Service type:** **Web service** (чтобы был HTTP на порту 8000).
   - **Port:** 8000 (API и health-check Koyeb по эндпоинту `/health`).

3. **Переменные окружения** (один набор для контейнера):
   - Бот: `BOT_TOKEN`, `SUPABASE_URL`, `SUPABASE_KEY`, `ADMIN_TELEGRAM_ID`, `WEBAPP_URL`.
   - Для уведомлений: `NOTIFY_LISTEN_PORT=8765`, `NOTIFY_SECRET` (произвольный общий секрет).
   - API: `BOT_NOTIFY_URL=http://127.0.0.1:8765`, тот же `NOTIFY_SECRET`; при необходимости `API_KEY`, `CORS_ORIGINS` (URL фронта/Mini App через запятую), `TELEGRAM_BOT_TOKEN`, `JWT_SECRET` (если используете `/auth/telegram`).

4. **Фронт:** в переменных сборки Mini App задайте **`VITE_API_URL`** = публичный URL этого сервиса (например `https://<имя-сервиса>.koyeb.app`), без слэша в конце. Тогда запросы «Ищу игру», подтверждение матчей и т.д. пойдут через API, а API вызовет notify-сервер бота по localhost — уведомления в Telegram будут уходить без отдельного второго сервиса.

5. **Пробуждение (Free tier):** один раз в 5–15 минут пингуйте URL сервиса (например через [cron-job.org](https://cron-job.org)) — разбудится один контейнер, в нём работают и API, и бот.

Переменные уведомлений (`NOTIFY_LISTEN_PORT`, `NOTIFY_SECRET`, `BOT_NOTIFY_URL`) задаются только в окружении сервиса (Koyeb или локально в `bot/.env` / `api/.env` при раздельном запуске).

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

### Docker (бот, только бот)

```bash
cd bot
docker build -t tennis-league-bot .
docker run --env-file .env tennis-league-bot
```

### Docker (один контейнер: API + бот)

```bash
# Из корня репозитория
docker build -t tg-tennis-combined .
docker run -p 8000:8000 --env-file bot/.env tg-tennis-combined
# API: http://localhost:8000, /docs, /health. В контейнере также крутится бот.
# Для уведомлений задайте в env: NOTIFY_LISTEN_PORT=8765, NOTIFY_SECRET, BOT_NOTIFY_URL=http://127.0.0.1:8765
```

### Регламент и рейтинг

- Тур = 1 месяц; в дивизионе все играют друг с другом.
- Матч: до 3 побед (Best of 5). Очки: победа 2, поражение 1, несыгранный 0.
- Ротация: топ-2 вверх, последние 2 вниз (если в дивизионе >8 — по 3).
- Рейтинг по формулам ФНТР (КД по дивизиону, КС по счёту). Новый игрок: рейтинг 100, последний дивизион.

Подробнее — в разделе «Правила» в Mini App.

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
