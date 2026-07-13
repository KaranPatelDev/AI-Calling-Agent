# Calling Agent — Build Plan

## Context

You want an app where you upload a list of receivers (PDF/Excel/manual text) plus a call script (upload or type), and the app calls each receiver and reads the script aloud. You also want to schedule a call for a future time (e.g. "call in 15 hours") instead of calling immediately.

Scope decisions already made with you:
- **Calling**: Twilio Programmable Voice places the call; the script is spoken via Twilio's built-in `<Say>` TTS (no ElevenLabs, no live conversation AI).
- **Interactivity**: One-way announcement only — no live back-and-forth conversation, no STT.
- **Auth**: Single-user app for now, protected by a shared secret, no signup/login system.

This is a greenfield repo (currently empty), so the plan below is the full initial build, not a diff against existing code.

## Architecture

```
React (Vercel) ──HTTPS──▶ FastAPI backend (Render) ──▶ Neon Postgres
                                │
                                ├─▶ Twilio REST API (place call)
                                └─◀ Twilio webhooks (TwiML fetch + status callback)
```

- **Backend**: Python + FastAPI + Uvicorn. One service, no microservices.
- **DB**: Postgres on Neon, accessed via SQLAlchemy 2.0 + Alembic migrations.
- **Scheduling**: `APScheduler` running in-process inside the FastAPI app, using `SQLAlchemyJobStore` pointed at the same Neon DB — jobs survive a backend restart/redeploy. No Celery/Redis; a single background scheduler is enough for one user placing calls.
- **File parsing**: `pandas` + `openpyxl` (Excel), `pdfplumber` (PDF text/table extraction), plus a manual-entry form — all normalize to a `{name, phone}` list.
- **TTS**: Twilio's `<Say>` verb reads the script text directly. No separate TTS service/dependency.
- **Frontend**: React + Vite, plain fetch calls to the backend, deployed to Vercel.
- **Auth**: a single shared `API_KEY` env var checked via a FastAPI dependency on every route; frontend stores it and sends it as a header. No user table, no JWT.

## Data model (single flat table — no Campaign/Contact split needed for v1)

`calls` table:
| column | type | notes |
|---|---|---|
| id | UUID/serial PK | |
| recipient_name | text | |
| phone_number | text | E.164 format |
| script_text | text | the script to be read for this call |
| scheduled_at | timestamptz | when to place the call (defaults to now) |
| status | text | `pending`, `scheduled`, `calling`, `completed`, `failed` |
| twilio_call_sid | text nullable | set once call is placed |
| error_message | text nullable | |
| created_at / updated_at | timestamptz | |

One upload (PDF/Excel/manual) with one script produces N rows in `calls`, each with its own `scheduled_at` (all the same time unless you stagger them).

## Backend endpoints

- `POST /api/parse-upload` — accepts a PDF or Excel file, returns parsed `[{name, phone}]` for the frontend to preview/edit before submitting.
- `POST /api/calls` — body: `{recipients: [{name, phone}], script_text, scheduled_at?}`. Creates `calls` rows. If `scheduled_at` is empty or in the past, calls are placed immediately (still routed through the scheduler so all placement logic is one path); otherwise an APScheduler job is registered for that timestamp.
- `GET /api/calls` — list calls with status, filterable, for a dashboard view.
- `POST /voice/twiml/{call_id}` — Twilio webhook; returns TwiML `<Response><Say>{script_text}</Say></Response>` for that call.
- `POST /voice/status/{call_id}` — Twilio status-callback webhook; updates `status`/`error_message` as the call progresses (ringing → completed/failed/no-answer).

Core call-placement function (used both for "call now" and for scheduled jobs): loads the `calls` row, calls Twilio's REST API with `url=/voice/twiml/{id}` and `status_callback=/voice/status/{id}`, stores the returned `call_sid`.

## Frontend pages

1. **New Call** — upload PDF/Excel or add recipients manually (name + phone rows); write or paste script text; choose "Call now" or pick a date/time (with a quick "+15 hours" style shortcut); submit.
2. **Dashboard** — table of all calls with status, scheduled time, and Twilio call outcome; simple polling or manual refresh.

Plain React + Vite, fetch-based API client, minimal CSS — no component library needed for this scope.

## Deployment

- **Frontend** → Vercel (Vite build), env var for backend API URL + shared API key.
- **Backend** → Render web service (not a serverless/cron function — it must stay running so APScheduler's in-memory timers and Twilio webhooks work). Needs a plan tier that doesn't spin down on idle, since Render's free tier sleeping would silently kill scheduled calls and drop incoming Twilio webhooks.
- **DB** → Neon Postgres, `DATABASE_URL` env var shared by the backend for both app data and the APScheduler jobstore.
- **Twilio** → account SID/auth token/phone number as backend env vars; Render's public URL is what you register as the webhook base for `/voice/twiml/...` and `/voice/status/...`.

## Progress (continuing implementation of this same plan)

Completed: backend core (config/db/models/schemas/auth), Twilio call placement + APScheduler wiring, API routers (calls/voice/uploads) + main.py, Alembic migration for `calls`, frontend scaffold (Vite React with New Call + Dashboard pages), backend `.env.example`/`render.yaml`, frontend `.env.example`, root `.gitignore`.

Remaining: root `README.md` with setup/deploy steps, then final verification (backend boots, frontend builds).

## Landing page (new addition)

Add a marketing landing page to the frontend as the root route, separate from the app's New Call/Dashboard screens (those move to `/app` or stay reachable after the API-key gate; landing page is public, no API key needed).

- **Hero section**: modern, minimalistic, "techy" but not busy — a dark, subtly-animated gradient/grid background (pure CSS: a soft radial gradient + faint grid lines or dot pattern, maybe one slow-moving gradient blob), bold headline, one-line subheading, single primary CTA button ("Get Started" → into the app). No stock photos, no clutter.
- **Sections below the fold** (SaaS-standard, informative, kept concise): how-it-works (3-4 steps: upload contacts → write script → schedule or call now → track results), key features grid (bulk upload PDF/Excel/CSV, script editor, scheduling, call status dashboard), and a closing CTA.
- Plain React component(s) + CSS (same stack as the rest of the frontend, no new dependencies, no animation library — CSS transitions/keyframes only).
- Files: `frontend/src/pages/Landing.jsx` + styles added to `frontend/src/index.css` (or a scoped `landing.css`); wire into the router in `App.jsx` as the `/` route, moving the existing New Call page to `/app`.

## Production-grade UI overhaul + dedicated Scheduler section (new addition)

Replaced the plain unstyled forms with a real app shell: dark sidebar (`components/Layout.jsx`, Dashboard/New Call/Scheduler nav via `NavLink` + `Outlet`), a full CSS design system in `index.css` (color tokens, cards, stat tiles, status badges, form/table styling). `New Call` is now call-now only; a new dedicated `/app/scheduler` page (`pages/Scheduler.jsx`) owns all future-dated scheduling plus a live "upcoming scheduled calls" list with per-row Cancel. Recipient upload/manual-entry logic extracted into `components/RecipientsEditor.jsx` and reused by both New Call and Scheduler. Backend gained `DELETE /api/calls/{id}` (`routers/calls.py`) + `cancel_call()` (`scheduler.py`) to cancel a pending/scheduled call and remove its APScheduler job; `CallStatus.CANCELLED` added to `models.py`.

## Suggested future enhancements (not yet scoped or approved)

Raised in response to "any suggestions to make this more advanced/optimised?" — none of these are committed work, just options to pick from:

- **Reliability**: retry-on-failure (auto re-queue a `failed` call N times with backoff), a "no-answer vs busy vs failed" distinction already exists in `voice.py`'s `_STATUS_MAP` but isn't surfaced differently in the UI yet.
- **Bulk scheduling ergonomics**: per-recipient stagger (e.g. call list of 50 people 30s apart instead of all at the exact same timestamp) to avoid Twilio rate limits and sounding like a robocall blast.
- **Script templating**: `{{name}}` placeholder in the script, substituted per recipient at call time — currently every recipient in a batch gets the identical script text.
- **Cost/usage visibility**: surface Twilio call duration/cost per call (Twilio's status callback payload includes duration) on the dashboard.
- **Recurring schedules**: "call this list every Monday at 9am" via a cron-style trigger in APScheduler instead of one-off `date` triggers.
- **Multi-recipient script reuse / templates library**: save a script as a named template to reuse across future batches instead of retyping.
- **Observability**: structured logging + a simple `/metrics` or admin view of scheduler job health (APScheduler jobs pending/misfired).
- **Performance**: for very large uploads (thousands of rows), batch-insert `calls` rows and stagger `schedule_call` registration instead of one APScheduler job per row.
- **Optimize the placeholder default: SQLAlchemyJobStore is a single global scheduler process** — if the app ever needs more than one backend instance (horizontal scaling), a shared jobstore with multiple worker processes needs a `misfire_grace_time` + locking strategy to avoid double-firing.

## Build order

1. Repo scaffold: `backend/` (FastAPI, SQLAlchemy models, Alembic) + `frontend/` (Vite React).
2. DB schema + Alembic migration for `calls`.
3. Twilio call placement + TwiML/status webhooks, tested with one hardcoded number.
4. `POST /api/calls` + APScheduler wiring (immediate and scheduled paths).
5. File upload parsing endpoint (PDF/Excel) + manual entry.
6. Frontend New Call + Dashboard pages wired to the API.
7. Shared API-key auth guard on backend + matching header on frontend.
8. Deploy: Neon → Render → Vercel, wire real Twilio credentials, end-to-end test a real scheduled call.

## Verification

- Unit-level: a script/test that inserts a `calls` row with `scheduled_at` a few seconds out and asserts APScheduler fires the placement function at the right time (no real Twilio call — mock the Twilio client).
- End-to-end: place one real call to your own phone via "Call now" and confirm the script is read; then schedule one a few minutes out and confirm it fires on time and the dashboard status updates via the Twilio status webhook.
