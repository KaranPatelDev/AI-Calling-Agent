# Go-Live Checklist — Every Step From Here to a Working System

Follow these in order. Each step lists exactly what to do and what documents (if any) you need.

---

## Phase 1 — Business registration (do this first, everything else depends on it)

- [ ] **1.1** Go to the official Udyam Registration portal (udyamregistration.gov.in).
- [ ] **1.2** Have ready: your **Aadhaar number**, your **PAN card**, and basic business details (name, address, nature of business — e.g. "real estate lead outreach services").
- [ ] **1.3** Complete the Udyam registration form online.
- [ ] **1.4** Receive your **Udyam Registration Certificate** — typically same-day, sometimes instant.
- [ ] **1.5** Save the certificate as a PDF — you'll upload it twice (Plivo KYC in Phase 2, DLT in Phase 4).

## Phase 2 — Plivo account + KYC

- [ ] **2.1** Go to plivo.com and sign up for an account (email + phone verification).
- [ ] **2.2** In the Plivo Console, find the KYC / verification section.
- [ ] **2.3** Upload **document 1**: your Udyam Registration Certificate (from Phase 1).
- [ ] **2.4** Upload **document 2**: your **Business PAN** (your personal PAN, since you're a sole proprietor — confirm with Plivo support if they need it linked/labeled differently).
- [ ] **2.5** Double-check the business name on both documents matches exactly — mismatches are the most common rejection reason.
- [ ] **2.6** Submit and wait for approval — typically **15 minutes to 1 business day**.
- [ ] **2.7** Once approved, go to **Billing** in the Plivo Console and add a payment method + some starting credit (needed to call non-verified numbers and buy a number).

## Phase 3 — Buy your Plivo number

- [ ] **3.1** Plivo Console → **Phone Numbers → Buy Number**.
- [ ] **3.2** Filter country: **India (+91)**.
- [ ] **3.3** Confirm **Voice** capability is checked (not just SMS).
- [ ] **3.4** Purchase the number.
- [ ] **3.5** Write down the number in E.164 format (e.g. `+9198XXXXXXXX`) — this becomes `PLIVO_FROM_NUMBER`.

## Phase 4 — DLT Principal Entity + template registration

This is separate from Plivo — done through your telecom operator's DLT portal (Jio/Airtel/Vodafone Idea all run one; ask Plivo support which one they recommend, or use the operator of your own SIM).

- [ ] **4.1** Go to your chosen operator's DLT self-service portal (e.g., Airtel's or Jio's DLT portal — search "[operator name] DLT registration portal").
- [ ] **4.2** Register as a **Principal Entity (PE)**. Documents needed:
  - Business PAN
  - GST certificate — if you don't have one yet as a small sole proprietor, ask the DLT portal's support whether Udyam alone is accepted (varies by operator)
  - Udyam Registration Certificate
  - Your personal ID proof (Aadhaar/PAN) as the authorized signatory
- [ ] **4.3** Pay the one-time registration fee (~₹5,000–₹10,000, sometimes discounted/waived through provider onboarding).
- [ ] **4.4** Once PE registration is approved, register a **template/use-case** describing your call script's purpose (e.g., "informational follow-up call to real estate buyer/seller leads").
- [ ] **4.5** Wait for template approval (timeline varies — can be same-day to a couple weeks depending on the operator's queue).

> You don't have to wait for Phase 4 to finish before testing — you can do Phases 5–8 in parallel and test calls to your own verified number while DLT processes.

## Phase 5 — Configure the backend with real credentials

- [ ] **5.1** In Plivo Console → Dashboard, copy your **Auth ID** and **Auth Token**.
- [ ] **5.2** Open `backend/.env` on your machine and set:
  ```
  PLIVO_AUTH_ID=<paste your Auth ID>
  PLIVO_AUTH_TOKEN=<paste your Auth Token>
  PLIVO_FROM_NUMBER=<your purchased number from Phase 3>
  ```
- [ ] **5.3** Confirm `FORWARD_TO_NUMBER=+919510461387` is still set (already done).
- [ ] **5.4** Repeat the same 3 values in your **Render** service's environment variables dashboard (so production matches local).

## Phase 6 — Point the Plivo number at your backend

- [ ] **6.1** Plivo Console → **Phone Numbers** → select your purchased number.
- [ ] **6.2** Under **Application**, set **Answer URL** to:
  - Local testing: your ngrok URL + `/voice/inbound` (e.g. `https://xxxx.ngrok-free.app/voice/inbound`)
  - Production: `https://<your-render-url>/voice/inbound`
- [ ] **6.3** Set method to `POST`.
- [ ] **6.4** Save.

(Note: the *outbound* webhooks — `/voice/answer/{id}` and `/voice/hangup/{id}` — don't need manual configuration here; the backend already passes those automatically per-call.)

## Phase 7 — Restart and deploy

- [ ] **7.1** Locally: stop and restart the `uvicorn` process so it picks up the new `.env` values.
- [ ] **7.2** On Render: after setting the env vars in Phase 5.4, trigger a redeploy (or it may auto-redeploy on env var save).
- [ ] **7.3** Confirm `PUBLIC_BASE_URL` on Render is set to the exact Render service URL (e.g. `https://ai-calling-agent-qnva.onrender.com`) — this is what gets sent to Plivo as the webhook base for outbound calls.

## Phase 8 — Test everything

- [ ] **8.1** Health check: visit `https://<your-render-url>/health` — should return `{"ok":true}`.
- [ ] **8.2** Log in to the live frontend (`https://ai-calling-agent-five.vercel.app/`).
- [ ] **8.3** **Outbound test**: New Call → add yourself as a recipient with your own number → write a short script → Call now. Confirm your phone rings and reads the script aloud.
- [ ] **8.4** Check the Dashboard — confirm the call shows status `completed` after you hang up.
- [ ] **8.5** **Inbound test**: from a different phone, call your Plivo number (`PLIVO_FROM_NUMBER`). Confirm `9510461387` rings within a couple seconds.
- [ ] **8.6** **Scheduled call test**: use the Scheduler to queue a call a few minutes out, confirm it fires automatically and the Dashboard updates.

## Phase 9 — Go live for real

- [ ] **9.1** Confirm DLT template approval has come through (Phase 4).
- [ ] **9.2** Upload your real buyer/seller contact list (PDF/Excel/CSV) via New Call or Scheduler.
- [ ] **9.3** Start with a small batch first (10–20 contacts) to confirm real-world call quality and answer rates before scaling to your full list.

---

## Summary of documents you'll need, gathered once and reused

| Document | Used for |
|---|---|
| Aadhaar number | Udyam registration |
| PAN card (personal, doubling as business PAN) | Udyam registration, Plivo KYC, DLT registration |
| Udyam Registration Certificate | Plivo KYC, DLT registration |
| GST certificate (if you have one) | DLT registration (confirm if Udyam alone suffices without it) |

## Summary of one-time and recurring costs

| Item | Cost | When |
|---|---|---|
| Udyam registration | Free | One-time |
| Plivo KYC | Free | One-time |
| DLT Principal Entity + template registration | ~₹5,000–₹10,000 | One-time |
| Plivo number rental | ~₹500–₹1,200/month | Recurring |
| Outbound calls | ~₹0.30–₹0.50/minute | Per usage |
| Inbound calls (forwarded) | ~₹0.50–₹0.90/minute combined (both legs) | Per usage |
| Render hosting | ~$7/month (Starter plan) | Recurring |
