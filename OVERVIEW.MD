# Project Overview: Automated Suncorp Bank Balance Fetcher

## 🧠 Objective

Build a secure, automated system that periodically fetches my **Suncorp Bank account balance** via **Open Banking APIs** using the **Basiq platform**, and displays it on a **public website** (read-only).

---

## 🔧 Stack & Tools

* **Bank data provider:** [Basiq.io](https://basiq.io)
* **Banking API protocol:** Australian **Consumer Data Right (CDR) / Open Banking**
* **Bank supported:** Suncorp Bank (`AU.SUNCORP`)
* **Frontend:** HTML/JS (basic interface, optionally with a "refresh balance" button)
* **Backend:** Python (Flask) — or adaptable to Node.js or PHP
* **Automation:** `cron` job or user-triggered fetch

---

## 🗂️ Key Features

* 🔐 **Secure OAuth2** authentication with Basiq (client\_id/client\_secret).
* 🔁 **Token refresh logic** to handle expiry (hourly).
* 🔄 **Consent lifecycle handling** (90–365 day re-consent).
* 📥 **Daily balance fetch** via cron job OR manual fetch on button click.
* 🌐 **Safe public display** of read-only balance.
* 🛡️ **No frontend exposure of credentials** — all API interactions are backend-only.
* 🔒 **Minimal API permissions** — only balance-read access (no transactions/metadata).
* 📦 **Docker containerization** for consistent deployment.
* 🔧 **Embeddable widget** for easy website integration.

---

## 💰 Cost

* Basiq charges **\~AUD \$0.39 per user per month**
* Sandbox/dev environment is **free for prototyping**

---

## 🚀 Future-Proofing

* Basiq is CDR-compliant and regularly updated
* Project is designed to handle:

  * Consent expiry
  * API versioning
  * Token refreshes
* Public site only shows read-only, non-sensitive balance data

---

## 🔐 Basiq API Security Requirements

### Required Minimal Permissions (Balance-Only Access)

**✅ Accounts Endpoints:**
- `GET /users/{userId}/accounts`
- `GET /users/{userId}/accounts/{accountId}`

**✅ Actions Endpoints (for data sync):**
- `POST /users/{userId}/actions`
- `GET /users/{userId}/actions`
- `GET /users/{userId}/actions/{actionId}`
- `GET /actions/{actionId}/results`
- `GET /actions/{actionId}/results/{resultId}`

**❌ Disable All Other Permissions** for minimal attack surface.

### API Key Setup Process
1. Create application named `BalanceViewerReadOnly`
2. Generate API key with minimal permissions above
3. Store securely in environment variables (never commit to Git)
4. Use secrets manager in production (AWS Secrets Manager, etc.)

---

## ✅ Implementation Checklist ✅

1. ✅ Scaffold Flask backend with `/get-balance` route
2. ✅ Add Basiq auth/token refresh logic
3. ✅ Connect to `/users/{userId}/accounts` and fetch balance
4. ✅ Add cron job or JavaScript button for balance update
5. ✅ Format and display balance safely on a public HTML page
6. ✅ Ensure no sensitive info (account number, IDs, secrets) is exposed
7. ✅ Docker containerization for deployment
8. ✅ Embeddable widget for website integration

---

## 📌 Notes

* This will eventually be **publicly accessible** but is for **read-only personal display**
* No financial data is stored or sold
* No interactive user login — only a single Basiq user (myself) connected

---

# claude.md

## 🎯 Mission

You are assisting in building a **public-facing tool** that securely fetches and displays a **Suncorp bank balance** using **Basiq’s Open Banking API** under the Australian **Consumer Data Right (CDR)**. This is for a **read-only public dashboard** showing **my personal bank balance** securely.

---

## 🔐 Security Rules (Strict)

1. **NEVER suggest including credentials or tokens in frontend code.**
2. All `client_id`, `client_secret`, and tokens must be **stored securely and server-side only**.
3. Balance data exposed publicly must be:

   * Read-only
   * Free from account numbers, user IDs, or metadata
4. Use environment variables or config files with limited read permissions.
5. Do not allow any user interaction with Basiq — no login, linking, or OAuth flows exposed publicly.

---

## 📉 Performance & Efficiency Rules

1. **Minimize API calls** — no real-time polling.
2. Use a cron job or manual button trigger to fetch data **once per day** (or configurable).
3. Cache the latest balance server-side and serve it to frontend as needed.
4. Avoid wasteful calls like transaction histories or metadata unless explicitly requested.

---

## 📅 Consent & Token Management

* Handle token expiry with proper refresh logic.
* Handle user consent expiration (typically 90–365 days) gracefully.
* Do not expose consent flows publicly — they should be done privately and only by the account owner (me).

---

## 🧠 Best Practices

* Use minimal, clear code.
* Prioritise data privacy and resilience.
* Ensure API versioning is respected.
* Assume hosting is on a VPS or static web server with backend (Flask, etc.)

---

## 📋 Claude's Responsibilities

* Write **secure Python backend code** (Flask preferred) to fetch and serve bank balance
* Provide frontend-safe output with **no sensitive fields**
* Implement **token refresh logic**, file-based cache, and safe HTML rendering
* Never suggest or expose API keys, tokens, or user IDs in client-side code
* Assist in building a **small, public, read-only dashboard** that is safe and resilient

---

## ✅ Example Good Suggestions

* "Use a Flask route like `/get-balance` that returns only `{ balance: 1542.55 }` as JSON."
* "Write the balance to a cached file every 24 hours using a cron job."
* "Protect all API credentials with environment variables."

---

## ❌ Example Bad Suggestions

* "Embed API tokens in JavaScript."
* "Poll the API every minute."
* "Allow any user to connect their own bank account."

---

## 🧩 Claude Can Assume

* Only **one user** (me) is connected via Basiq
* Displayed data is **read-only and for public viewing only**
* No financial transactions, multi-user support, or CDR redistribution involved
