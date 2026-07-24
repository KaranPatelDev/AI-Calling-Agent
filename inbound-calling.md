# Inbound Call Forwarding — Implementation Guide + Pricing + Dev Costing

## What this covers

Your Plivo number is virtual — no SIM card. To actually receive calls on it as a human, the number needs to **forward/bridge** incoming calls to your real mobile number. This document explains how that's implemented, what it costs (per-minute, both directions), and the full dev costing breakdown for the project.

> **This is now implemented** — `backend/app/routers/voice.py` has the `/voice/inbound` route, and `backend/app/config.py` has the `forward_to_number` setting. What's left is just configuration (below) using your own preowned number as the forwarding target.

## 1. How it works

```
Buyer/Seller dials your Plivo number
        │
        ▼
Plivo receives the call, hits your backend's "Answer URL" webhook
        │
        ▼
Backend returns Plivo XML: <Dial><Number>{your real mobile}</Number></Dial>
        │
        ▼
Plivo bridges the call to your real phone — it rings normally, you answer it like any call
```

No app, no SIM, no special hardware on your end — your existing mobile phone just rings.

## 2. Step-by-step implementation

### Step 1 — Add a `FORWARD_TO_NUMBER` setting
In `backend/app/config.py`, add a new setting for the real number to forward to:
```python
forward_to_number: str = ""
```
Add `FORWARD_TO_NUMBER=+91XXXXXXXXXX` to `backend/.env` / `.env.example` / Render's environment variables.

### Step 2 — Add the inbound webhook endpoint
In `backend/app/routers/voice.py`, add a new route Plivo will call whenever someone dials your number:
```python
@router.post("/inbound")
def inbound_call():
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<Response><Dial callerId="{settings.plivo_from_number}">'
        f'<Number>{settings.forward_to_number}</Number>'
        '</Dial></Response>'
    )
    return Response(content=xml, media_type="application/xml")
```
This tells Plivo: "bridge this inbound call to my real mobile number."

### Step 3 — Point the Plivo number at this endpoint
In the Plivo Console:
1. Go to **Phone Numbers** → select your purchased number.
2. Under **Application**, set the **Answer URL** to `https://your-backend-url/voice/inbound` (method: `POST`).
3. Save.

From this point on, any call to your Plivo number triggers this webhook automatically — no per-call setup needed.

### Step 4 — Test it
Call your Plivo number from any other phone. Your real mobile should ring within a couple of seconds. Answer it — you're now talking through the bridged call.

## 3. Pricing (India, Plivo — ballpark, confirm current rates at plivo.com/pricing)

### Buying the number
| Item | Ballpark cost |
|---|---|
| Indian voice-enabled virtual number | ~₹500–₹1,200 / month rental |

### Outbound calling (what the app already does — placing calls to buyers/sellers)
| Item | Ballpark cost |
|---|---|
| Outbound call, India domestic | ~₹0.30–₹0.50 / minute |

### Inbound calling (someone calling your Plivo number back)
| Item | Ballpark cost | Notes |
|---|---|---|
| Inbound call leg (Plivo receiving the call) | Often ~₹0.20–₹0.40 / minute, sometimes free/nominal depending on plan | The "someone dials your Plivo number" leg |
| **Forwarding leg** (Plivo dialing your real mobile via `<Dial>`) | ~₹0.30–₹0.50 / minute (same as a normal outbound call) | **Important**: forwarding a call is billed as a *second, separate outbound call* from Plivo to your real number — so one forwarded inbound call = inbound leg cost + outbound forwarding leg cost combined |

**Example**: a 2-minute inbound call that gets forwarded to your mobile costs roughly ₹1–₹1.80 total (both legs combined) — still very cheap, but worth knowing it's not just "free because it's inbound."

### One-time compliance cost (already covered in `plivo.md`, restated briefly)
DLT Principal Entity + template registration: ~₹5,000–₹10,000 one-time, needed regardless of inbound/outbound.

## 4. Developer costing breakdown (Grand Total: ₹25,000)

| # | Work item | Cost (₹) |
|---|---|---|
| 1 | Backend development — API, database models, auth, scheduler engine | 7,000 |
| 2 | Frontend development — all pages, custom design system, components | 8,000 |
| 3 | Telephony integration — Plivo outbound calling + inbound call forwarding (webhooks, script-to-voice pipeline, dial-forward to real number) | 4,500 |
| 4 | Advanced features — buyer/seller segmentation, script templating/placeholders, settings page | 2,500 |
| 5 | Deployment setup & configuration — Vercel/Render/Neon wiring (one-time setup, not recurring hosting bills) | 2,000 |
| 6 | Testing, documentation & handover (README, setup docs, source transfer) | 1,000 |
| | **Grand Total** | **₹25,000** |

Ongoing hosting/Plivo/Neon service costs remain the client's own recurring expense, separate from this figure(Currently free as not heavy usage).
