# Web-first rollout checklist

## 1) Database
- Apply migration: `database/migrations/014_players_web_auth.sql`.
- Verify columns in `players`: `auth_user_id`, `email`.

## 2) Supabase Auth
- Enable Email provider with Magic Link.
- Set Site URL to your primary frontend domain.
- Add redirect URLs for both domains: `https://app.example.com` and `https://backup.example.com`.

## 3) API
- Set env vars: `SUPABASE_URL`, `SUPABASE_KEY`, `JWT_SECRET`, `API_KEY`, `CORS_ORIGINS`.
- Include both domains in `CORS_ORIGINS`.
- Verify `/auth/web` and `/players/me` from Swagger.

## 4) Frontend
- Set env vars:
  - `VITE_SUPABASE_URL`
  - `VITE_SUPABASE_ANON_KEY`
  - `VITE_API_URL`
  - `VITE_TELEGRAM_BOT_NAME`
- Run `npm run build` and publish to primary + backup domains.

## 5) Smoke tests
- Open app in browser without Telegram and request magic link.
- Complete sign-in from email and verify home/rating/division pages load.
- Verify match submit/confirm works and ownership checks deny чужой `player_id`.
- Open Telegram Mini App and verify legacy flow still works.

## 6) Monitoring
- Track API 401/403 and `/auth/web` success rate.
- Add uptime checks for both domains and API `/health`.
