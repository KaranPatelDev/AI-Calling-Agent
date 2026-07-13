# Calling Agent

Upload contacts (PDF/Excel/CSV or manual entry), write a script, and place or schedule automated voice calls that read the script aloud via Plivo.

## Stack

- **Backend**: FastAPI + SQLAlchemy + Alembic + APScheduler + Plivo, deployed to Render.
- **Frontend**: React + Vite, deployed to Vercel.
- **Database**: Postgres on Neon.

## Local setup

### Backend

```
cd backend
python -m venv .venv && .venv\Scripts\activate   # or source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL, API_KEY, Plivo creds
alembic upgrade head
uvicorn app.main:app --reload
```

For local Plivo webhooks to reach your machine, expose it with a tunnel (e.g. `ngrok http 8000`) and set `PUBLIC_BASE_URL` to the tunnel URL.

### Frontend

```
cd frontend
npm install
cp .env.example .env   # set VITE_API_URL to your backend URL
npm run dev
```

On first load the app asks for the API key (same value as backend's `API_KEY`); it's stored in `localStorage`.

## Deployment

1. **Neon**: create a Postgres project, copy the connection string into `DATABASE_URL`.
2. **Render**: create a web service from `backend/` (uses `render.yaml`), set env vars from `.env.example`. Use a paid plan tier — a free/sleeping instance will drop scheduled calls and Plivo webhooks.
3. **Plivo**: buy a phone number, set `PLIVO_AUTH_ID` / `PLIVO_AUTH_TOKEN` / `PLIVO_FROM_NUMBER`, and set `PUBLIC_BASE_URL` to the Render service URL. See `plivo.md` for full setup steps, pricing, and required documents.
4. **Vercel**: deploy `frontend/`, set `VITE_API_URL` to the Render service URL.

## Notes

- Calls are one-way announcements only (Plivo `<Speak>` reads the script; no live conversation/STT).
- Scheduling uses APScheduler with a Postgres-backed job store, so scheduled calls survive a backend restart.
- Single shared `API_KEY` protects all `/api/*` routes; there is no multi-user login.
