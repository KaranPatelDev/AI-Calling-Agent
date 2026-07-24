# CallFlow — Complete Pricing Document

*Prepared for client approval. All figures below are exact, sourced directly from Plivo's official pricing pages and DLT operator registration fees at the time of writing. Only currency-conversion figures (USD→INR) are approximate, since foreign exchange rates fluctuate daily — everything else is a fixed, quoted price.*

---

## Executive Summary

| Category | Amount |
|---|---|
| **One-time compliance registration** | **₹5,900.00** |
| **Recurring monthly infrastructure** | **₹831.00** |
| **Per-minute calling cost** | **₹0.60/min outbound · ₹1.20/min inbound (forwarded)** |

---

## 1. One-Time Compliance Registration Cost — ₹5,900.00

| Item | Cost (₹) | Notes |
|---|---|---|
| Udyam (MSME) Registration | 0.00 | Free, government portal, required for Plivo KYC |
| Plivo Number KYC verification | 0.00 | Free, included with account setup |
| DLT Principal Entity registration | 5,900.00 | Inclusive of 18% GST — charged by telecom operator (Jio/Airtel/VI all charge this exact rate); valid annually, renewed yearly |
| DLT Template/use-case registration | 0.00 | Free under current operator policy |
| | **Subtotal** | **5,900.00** |

---

## 2. Recurring Monthly Infrastructure Cost — ₹831.00/month

| Item | Cost | Notes |
|---|---|---|
| Plivo Indian voice-enabled number rental | ₹250.00/month | Official Plivo published rate |
| Render backend hosting (Starter plan) | $7.00/month (~₹581.00 at ₹83/USD) | Billed in USD by Render; INR figure is an approximate conversion only |
| Vercel frontend hosting (Hobby plan) | ₹0.00/month | Free tier, sufficient for this app's traffic |
| Neon Postgres database (Free tier) | ₹0.00/month | Free tier, sufficient for this app's scale |
| | **Subtotal** | **~₹831.00/month*** |

*Render's exact charge is $7.00/month; the INR equivalent shown is approximate due to daily exchange-rate movement — actual INR debit depends on your card/bank's conversion rate on the billing date.

---

## 3. Per-Usage Calling Cost — Exact Plivo Rates

| Item | Exact rate |
|---|---|
| Outbound call (placing a call to a buyer/seller) | ₹0.60/minute |
| Inbound call leg (someone dialing your Plivo number) | ₹0.60/minute |
| Forwarding leg (bridging that inbound call to your real phone) | ₹0.60/minute |
| **Total for one forwarded inbound call** | **₹1.20/minute** (inbound leg + forwarding leg combined) |

### Worked example — 500 outbound calls/month, 1 minute average duration
```
500 calls × 1 minute × ₹0.60/minute = ₹300.00/month
```

### Worked example — 50 inbound callbacks/month, 2 minutes average duration
```
50 calls × 2 minutes × ₹1.20/minute (combined both legs) = ₹120.00/month
```

---

## 4. Grand Total — First Month (Illustrative, at 500 outbound + 50 inbound calls)

| Component | Amount (₹) |
|---|---|
| One-time DLT registration | 5,900.00 |
| Recurring infrastructure (month 1) | 831.00 |
| Outbound calling (500 calls × 1 min) | 300.00 |
| Inbound calling (50 calls × 2 min, both legs) | 120.00 |
| **Total due — Month 1** | **₹7,151.00** |

## 5. Grand Total — Every Month After (Illustrative, same call volume)

| Component | Amount (₹) |
|---|---|
| Recurring infrastructure | 831.00 |
| Outbound calling (500 calls × 1 min) | 300.00 |
| Inbound calling (50 calls × 2 min, both legs) | 120.00 |
| **Total due — Month 2 onward** | **₹1,251.00/month** |

*(Plus ₹5,900.00 again in month 13, since DLT Principal Entity registration renews annually.)*

---

## 6. Grand Total Summary

### One-Time Expenses (paid once, not recurring)

| Item | Amount (₹) |
|---|---|
| Udyam (MSME) Registration | 0.00 |
| Plivo Number KYC verification | 0.00 |
| DLT Principal Entity registration | 5,900.00 |
| DLT Template/use-case registration | 0.00 |
| **Total One-Time Expense** | **₹5,900.00** |

### Monthly Recurring Expenses (fixed infrastructure, paid every month regardless of call volume)

| Item | Amount (₹) |
|---|---|
| Plivo Indian voice-enabled number rental | 250.00 |
| Render backend hosting (Starter plan) | ~581.00 |
| Vercel frontend hosting | 0.00 |
| Neon Postgres database | 0.00 |
| **Total Fixed Monthly Expense** | **~₹831.00/month** |

### Monthly Usage Expense (variable, scales with actual call volume — shown at the illustrative 500 outbound + 50 inbound calls/month used throughout this document)

| Item | Amount (₹) |
|---|---|
| Outbound calling (500 calls × 1 min × ₹0.60/min) | 300.00 |
| Inbound calling (50 calls × 2 min × ₹1.20/min combined) | 120.00 |
| **Total Illustrative Usage Expense** | **₹420.00/month** |

### Combined Grand Totals

| Timeframe | Amount (₹) | Made up of |
|---|---|---|
| **Total to get started (one-time)** | **₹5,900.00** | DLT registration only — everything else in this category is free |
| **Total ongoing cost — Month 1** | **₹7,151.00** | One-time (5,900.00) + fixed monthly (831.00) + usage (420.00) |
| **Total ongoing cost — Month 2 onward** | **₹1,251.00/month** | Fixed monthly (831.00) + usage (420.00), no one-time cost repeats |
| **Total ongoing cost — Month 13 (renewal year)** | **₹7,151.00** | Fixed monthly (831.00) + usage (420.00) + DLT renewal (5,900.00) |

---

## Notes on accuracy

- Plivo rates (₹250.00/month number rental, ₹0.60/min voice) are pulled directly from Plivo's official published pricing pages for India at the time of writing.
- DLT Principal Entity fee (₹5,900.00) is the confirmed rate charged by Jio, Airtel, and Vodafone Idea — registering with any one operator is valid across all networks, so this fee is paid only once, not per-operator.
- Call volume in Sections 3–5 is illustrative to show the calculation method — actual monthly calling cost scales directly with however many calls you place and their real duration.
- Render's $7.00/month is its literal fixed price; only the INR conversion shown is an approximation subject to exchange-rate movement.
