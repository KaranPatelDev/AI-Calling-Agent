# Making CallFlow Fully Operational (India) — Plivo Setup + AI Voice + Pricing

> Note: exact prices and regulations change over time. The numbers/rules below are best-effort guidance to help you plan — always confirm current rates at plivo.com/pricing and compliance requirements with Plivo support or a telecom-compliance consultant before spending real money or calling real customers.

The app has been fully switched from Twilio to **Plivo** — `backend/app/plivo_client.py` places calls, and `backend/app/routers/voice.py` exposes the two webhooks Plivo needs (`/voice/answer/{id}` and `/voice/hangup/{id}`). Nothing else in the app changes based on the calling provider.

## 1. Why Plivo for India

- Self-serve signup — no sales call needed to get started, unlike some India-first providers.
- Supports Indian virtual numbers with outbound voice capability (unlike Twilio, which doesn't sell Indian local numbers).
- REST API is close enough to Twilio's shape that the whole migration was a contained change to 2 files (`plivo_client.py`, `routers/voice.py`) plus a config rename — nothing else in the app needed to change.
- Competitive per-minute domestic Indian rates compared to India-specific alternatives like Exotel/Knowlarity at small-to-moderate volume.

## 2. Setting up Plivo (step by step)

1. **Create an account** at plivo.com. Signup is self-serve (email + phone verification), no sales onboarding required to start.
2. **Get your credentials**: Plivo Console → Dashboard shows your **Auth ID** and **Auth Token** immediately — these go into `backend/.env` as `PLIVO_AUTH_ID` / `PLIVO_AUTH_TOKEN`.
3. **Buy a phone number**: Console → Phone Numbers → Buy Number. Search India (`+91`), filter for **Voice**-enabled numbers. This becomes `PLIVO_FROM_NUMBER` (E.164 format, e.g. `+9198XXXXXXXX`).
   - Trial/unverified accounts on Plivo typically restrict outbound calls to your own verified number until you add billing — similar caveat to Twilio's trial mode.
4. **Add billing**: add a payment method and top up credit to place calls to non-verified numbers.
5. **Webhook URLs**: same as before — the backend passes `answer_url` and `hangup_url` per call when placing it via the REST API (already wired in `plivo_client.py`). Plivo just needs `PUBLIC_BASE_URL` to be a real, internet-reachable address.
   - **Testing locally right now**: run `ngrok http 8010`, copy the `https://xxxx.ngrok-free.app` URL into `PUBLIC_BASE_URL` in `backend/.env`, restart the backend.
   - **Once deployed**: set `PUBLIC_BASE_URL` to your Render service URL instead.
6. **Verify end-to-end**: place a "Call now" to your own number and confirm the script is read aloud; check the Dashboard shows `completed` after you hang up.

## 3. Documents/details Plivo (and DLT registration) will ask for

- **KYC for the Plivo account itself**: typically a government ID and basic business details (name, email, phone) — lighter than full DLT registration, needed just to activate paid calling and buy a number.
- **DLT Principal Entity (PE) registration** (separate from Plivo, done via your telecom operator's DLT portal — Jio/Airtel/Vi all run one, Plivo's support can point you to the right one):
  - Business PAN
  - GST registration certificate (if applicable to your business)
  - Business registration proof (e.g., incorporation certificate, or proprietorship proof if unregistered/sole proprietor)
  - Authorized signatory ID proof
  - A declared "header"/entity name that will be associated with your calls
- **DLT template/use-case registration**: a description of the call's purpose/content (your script's intent, e.g., "informational follow-up to real estate inquiry") — needs approval before large-volume calling.

## 4. Indian telecom compliance (same rules apply regardless of provider)

- **DLT registration** is expected for commercial voice calls, same as SMS — see documents above.
- **NDNC / NCPR (National Do Not Call)**: numbers on India's DND list cannot legally receive **promotional** calls. If your buyer/seller calls are to people who already inquired (existing leads), this is generally treated as transactional/relationship communication rather than cold telemarketing — but keep basic consent records (e.g., their original inquiry) either way.
- **TRAI enforcement**: unregistered bulk commercial voice traffic is increasingly filtered/blocked by carriers in real time — register properly rather than risk your number/account being blocked.

## 5. AI voice options (unchanged in spirit, Plivo supports both paths)

### Option A — Plivo's built-in `<Speak>` voice (current setup, cheapest)
`routers/voice.py`'s `/voice/answer/{id}` returns `<Response><Speak>{script}</Speak></Response>` — Plivo's built-in TTS reads it. Plivo supports specifying a `voice` attribute for more natural-sounding options (including Indian-accented English); check Plivo's docs for currently supported voice names if you want to tune this.

### Option B — ElevenLabs voice (most natural-sounding)
Same integration shape as before, provider-agnostic:
1. Create an ElevenLabs account, get an API key.
2. Backend generates an MP3 per personalized script via ElevenLabs' TTS API.
3. `/voice/answer/{id}` returns `<Response><Play>{audio_url}</Play></Response>` instead of `<Speak>`.
4. Since scripts are personalized per-recipient (`{{name}}`/`{{company}}`), one MP3 is generated per call. ElevenLabs supports Hindi voices too if scripts aren't pure English.

Not yet built — a moderate addition (new ElevenLabs client + a way to serve generated audio + one change to `voice.py`).

### Option C — Real conversational AI (caller can talk, AI responds live)
A materially bigger build: Plivo's Audio Streaming (their Media-Streams equivalent) + real-time STT + an LLM + streaming TTS. Out of current scope (one-way announcements only, per the original plan decision).

## 6. Pricing (ballpark — confirm current rates at plivo.com/pricing)

### Plivo core costs
| Item | Ballpark cost | Notes |
|---|---|---|
| Indian virtual number (voice-enabled) | ~₹500–₹1,200 / month | Varies by number type |
| Outbound call (India domestic) | ~₹0.30–₹0.50 / minute | Billed per-minute |
| Built-in `<Speak>` voice | Free (bundled in call cost) | Default Plivo TTS |
| Account KYC / activation | Usually free, quick self-serve | Needed to exit trial limits |

**Example**: 500 calls/month, avg. 45 seconds each ≈ 375 minutes → roughly **₹110–₹190/month** in call charges, plus ~₹500–₹1,200/month for the number.

### DLT registration (one-time, separate from Plivo billing)
| Item | Ballpark cost |
|---|---|
| Principal Entity registration | Often ~₹5,000–₹10,000 one-time (sometimes discounted via provider onboarding) |
| Template/use-case registration | Usually free–nominal per template |

### ElevenLabs (only if you add Option B)
| Tier | Approx. price | Approx. included characters/month |
|---|---|---|
| Free | $0 | ~10k characters |
| Starter | ~$5/mo | ~30k characters |
| Creator | ~$22/mo | ~100k characters |
| Pro | ~$99/mo | ~500k characters |

A ~30-second script is roughly 400–500 characters, so cost scales with call volume (each personalized call generates unique audio), not just script count.

### Hosting (unchanged)
| Service | Ballpark cost |
|---|---|
| Neon Postgres | Free tier likely enough; paid tiers from ~$19/mo if outgrown |
| Render backend (Starter tier — must not be free, or scheduled calls/webhooks get dropped) | ~$7/month |
| Vercel frontend | Free tier is plenty |

### Rough all-in monthly estimate (India, a few hundred calls/month, standard Plivo voice)
**~₹1,300–₹2,200/month (~$16–$26)** including number rental, call minutes, and Render hosting — plus a one-time DLT registration cost the first month. Add ElevenLabs subscription on top if you want upgraded voice quality.

## 7. Final checklist — everything needed to go live

### Business / compliance
- [ ] Business PAN and GST details (for DLT Principal Entity registration)
- [ ] Decision on whether calls count as promotional or transactional/existing-lead follow-up (affects DND obligations)
- [ ] Basic consent record for your existing buyer/seller leads
- [ ] Comfort proceeding without a dedicated legal review, or a decision to get one before scaling volume

### Plivo account
- [ ] Plivo account created (self-serve signup)
- [ ] Auth ID + Auth Token copied into `backend/.env` as `PLIVO_AUTH_ID` / `PLIVO_AUTH_TOKEN`
- [ ] Indian voice-enabled number purchased, set as `PLIVO_FROM_NUMBER`
- [ ] Billing/payment method added (to exit trial/verified-only-number restrictions)
- [ ] DLT Principal Entity registration completed
- [ ] DLT template/use-case registered for your call script(s)

### AI voice decision
- [ ] Decision: keep Plivo's built-in voice (Option A, no extra cost) or add ElevenLabs (Option B, extra integration + subscription)
- [ ] If ElevenLabs: account + API key + chosen voice

### Infrastructure
- [ ] A publicly reachable backend URL — ngrok for testing now, or the deployed Render URL for real use, set as `PUBLIC_BASE_URL`
- [ ] Render account for backend hosting, on a non-sleeping (paid) tier
- [ ] Vercel account for frontend hosting
- [ ] Neon (already set up) remains the database

### Code (already done)
- [x] `backend/app/plivo_client.py` places calls via Plivo's REST API
- [x] `backend/app/routers/voice.py` exposes `/voice/answer/{id}` and `/voice/hangup/{id}` returning Plivo XML
- [x] `calls.provider_call_id` column (renamed from the old Twilio-specific column) stores Plivo's call UUID
- [ ] If ElevenLabs added later: new client module + a way to serve generated audio files + one change to `voice.py`'s XML response
