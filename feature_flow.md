# CallFlow — Features & Flow

A calling agent for Indian real-estate outreach: upload contacts, place/schedule AI voice calls in Hindi, track outcomes, and auto-handle callbacks. Stack: FastAPI + Neon Postgres (backend, Render) / React + Vite (frontend, Vercel) / Plivo (telephony).

## 1. Contacts & Scripts

- **Upload recipients** via PDF, Excel/CSV, or manual entry (`RecipientsEditor`) — name, phone, organization auto-detected from common column names.
- **Script editor** supports `{{name}}` / `{{company}}` placeholders (filled in per recipient at call time) and `[[slow]]...[[/slow]]` markup to slow down specific phrases.
- **Script library** (Settings page) — save unlimited named scripts, pick one from a dropdown when placing a call instead of retyping.
- **Buyer / Seller tagging** — every call/recipient is tagged, with default scripts per audience and dashboard filters.

## 2. Placing Calls

- **New Call** — call a list of recipients immediately.
- **Scheduler** — same thing but for a future date/time; shows an upcoming-calls list with per-row cancel.
- Both let you override the **speaking speed** per batch (`SpeedControl`); otherwise the global default (Settings) is used.
- **Flow**: `POST /api/calls` creates one `Call` row per recipient (status `pending`/`scheduled`) → commits to the DB → registers an APScheduler job (`schedule_call`) for the run time. At the scheduled moment, `execute_call()` calls Plivo (`plivo_client.place_call`), which rings the recipient and points Plivo at:
  - **Answer webhook** (`/voice/answer/{id}`) — returns Hindi TTS XML (`Polly.Aditi`, `hi-IN`, adjustable `<prosody rate>`) with the personalized script.
  - **Hangup webhook** (`/voice/hangup/{id}`) — classifies the outcome (see below).
  - **Machine-detection webhook** (`/voice/machine-detection/{id}`) — records if Plivo thinks a machine picked up (stored, not currently shown as a separate outcome — see §5).

## 3. Call Outcomes

Set on hangup, shown on the Dashboard:

| Status | Meaning |
|---|---|
| Completed | Call connected and ran through normally |
| Cut off | Recipient hung up well before the script could have finished (estimated via word-count vs. actual duration) |
| No answer | Recipient didn't pick up / busy / rejected |
| Not placed (Failed) | Call never connected — Plivo/network error |
| Scheduled | Still pending/queued for the future |

## 4. Inbound Calls (callbacks)

- When a called recipient calls the Plivo number back, `/voice/inbound` logs an `InboundCall` row (matched against past `Call.phone_number` by digits-only comparison, so a name/organization shows even though Plivo sends numbers without `+`) and forwards the call live to your real phone (`FORWARD_TO_NUMBER`) via `<Dial>`.
- `/voice/inbound-hangup` records duration/outcome and whether the forward was **missed** (no answer/busy/rejected).

## 5. Automatic Missed-Callback Retry

- If a callback was missed and auto-callback is enabled (Settings toggle), a retry `Call` is auto-scheduled ~24h later (pushed to Monday if that lands on a Sunday).
- This retry is **not** an AI script call — it dials the person and `<Dial>`s them straight to your real phone, exactly like the live inbound-forward flow. It's a normal human-to-human call, just automatically re-triggered.
- Shows up in the Scheduler's upcoming list like any other call (cancellable the same way).

## 6. Dashboard

- Stat tiles + percentages (answer rate, not-placed rate, etc.), Buyer vs Seller breakdown chart, calls-over-time trend chart (7d/30d).
- Outcome filter tabs (All / Successful / Not placed / No answer / Cut off / Scheduled) and audience filter (All / Buyers / Sellers).
- Inbound Interest table — every callback received, matched name/org, duration, status, and linked auto-callback schedule/status.
- Delete individual call history rows or clear all finished history.

## 7. Settings

- Default script per audience (Buyer/Seller), global speaking speed (%), auto-callback on/off toggle, script library CRUD.

## Known limitations (accepted, not bugs)

- **DLT (India telecom) registration is intentionally skipped** — accepted compliance risk for current volume.
- **Voicemail/answering-machine detection** is recorded (`Call.answered_by_machine`) but not surfaced as a separate outcome — Plivo's detection produced false positives on Hindi speech, so it's folded into "Completed" for now.
