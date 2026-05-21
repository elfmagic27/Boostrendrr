# Discord Boost Bot

A Discord bot for managing server boosts with token management, auto-boosting, an onliner system, a FastAPI/web panel backend, and webhook integrations for Sellpass/Sellix/Sellapp.

## Run & Operate

- **Run bot**: `python bot.py`
- **Auth system** (key management CLI): `python authsystem.py`
- **Web panel**: served at port 5000 (root `/`)
- **Health check**: `GET /health` — used for cron-job.org keepalive pings

## Stack

- Python 3.11
- discord.py, FastAPI, uvicorn, aiofiles, python-multipart
- Flask, websockets, pymongo[srv], tls-client, httpx, requests

## Railway Deployment

Deploy on Railway.com. Required environment variables:

| Variable              | Description                        |
|-----------------------|------------------------------------|
| `MONGODB_URI`         | MongoDB Atlas connection string    |
| `BOT_TOKEN`           | Discord bot token                  |
| `BOT_CLIENT_ID`       | Discord OAuth2 app client ID       |
| `BOT_CLIENT_SECRET`   | Discord OAuth2 app client secret   |
| `WEBHOOK_URL`         | Discord webhook URL for logs       |
| `PANEL_PASSWORD`      | Admin panel password               |
| `PORT`                | Auto-set by Railway (do not override) |

Railway will auto-detect `railway.json` or `Procfile` as the start command (`python bot.py`).

## Where things live

- `bot.py` — Main entrypoint (bot commands, boost logic, FastAPI routes, onliner)
- `db.py` — MongoDB abstraction layer (replaces all file I/O for tokens/keys/proxies)
- `authsystem.py` — CLI tool for generating/managing license keys
- `config/config.json` — App config (bot token, webhook URL, feature flags, port) — stays as file
- `config/onliner.json` — Onliner config (activity/status settings) — stays as file
- `templates/panel.html` — Web panel UI (stock check + key redemption)
- `templates/admin.html` — Admin panel UI
- `static/` — Static assets directory
- `railway.json` — Railway deployment config
- `Procfile` — Railway/Heroku start command

## MongoDB Collections (via db.py)

All persistent data lives in MongoDB. Collections:
- `tokens` — boost tokens (`type`: "1m" or "3m")
- `keys` — active license keys
- `used_keys` — used key history
- `oauth_tokens` — cached Discord OAuth tokens
- `proxies` — proxy list
- `boost_logs` — boost success/failure log

## Architecture decisions

- FastAPI runs on port 5000 (from `config/port` or `PORT` env var) via uvicorn alongside the Discord bot
- Web panel served directly by FastAPI at `/` — no separate frontend server needed
- Boosting jobs are dispatched to background threads and polled via `/api/status/{job_id}`
- All persistent data stored in MongoDB — no local file I/O for data
- Config files (config.json, onliner.json) stay as files — env vars supplement via `_secret()` mechanism
- `result.txt` is a transient temp file for DM token delivery — ephemeral storage is fine

## Product

- Discord bot that manages server boosting via Discord tokens
- Web panel for key redemption and stock checking without needing Discord
- Auto-boosting triggered via Sellpass/Sellix/Sellapp purchase webhooks
- Onliner keeps boost tokens active and online
- License key system with balance tracking

## Web Panel API Endpoints

- `GET /` — Customer web panel UI
- `GET /health` — Health check (for cron-job.org)
- `GET /api/stock` — Live 1m/3m token counts
- `POST /api/key-info` — `{"key": "..."}` → key details
- `POST /api/redeem` — `{"key": "...", "invite": "..."}` → starts boost job
- `GET /api/status/{job_id}` — Poll boost job result

## Admin Panel

- `GET /admin` — Admin login page (password from `config.panel_password`, default: `admin1234`)
- `POST /admin/login` — Auth → 24h session token
- `GET /admin/verify` — Verify session token
- `GET /admin/api/keys` — List active keys
- `DELETE /admin/api/key/{key}` — Delete one key
- `DELETE /admin/api/keys/all` — Delete all active keys
- `GET /admin/api/used-keys` — List used key history
- `DELETE /admin/api/used-keys/clear` — Clear used key history
- `POST /admin/api/generate-key` — Generate keys `{month, amount, quantity}`
- `POST /admin/api/upload-tokens` — Upload token file (multipart, type=1m|3m)
- `DELETE /admin/api/clear-stock/{1m|3m}` — Wipe a token stock file

## Captcha Solvers

Set `config.captcha_solver.use` to one of: `hcoptcha`, `capsolver`, `anticaptcha`, `kovasolver`, `voidsolver`
Add corresponding API key field in config.

| Solver      | Config key              | cap_service |
|-------------|-------------------------|-------------|
| hcoptcha    | `hcoptcha_api_key`      | 1           |
| capsolver   | `capsolver_api_key`     | 2           |
| anticaptcha | `anticaptcha_api_key`   | 3           |
| kovasolver  | `kovasolver_api_key`    | 5           |
| voidsolver  | `voidsolver_api_key`    | 4           |

## 24/7 Uptime via cron-job.org

1. Deploy/publish the project on Railway
2. Go to https://cron-job.org and create a free account
3. Create a new cron job:
   - URL: `https://YOUR-APP.up.railway.app/health`
   - Schedule: Every 5 minutes
4. This keeps the bot alive 24/7

## Gotchas

- `MONGODB_URI` must be set on Railway before deployment — the app will fail to read/write data without it
- Bot token must be set via `BOT_TOKEN` env var on Railway (or in `config/config.json` for Replit)
- `config/config.json` is still read at startup — env vars override it via the `_secret()` mechanism
- `tls_client` may have platform-specific issues on some Linux builds
