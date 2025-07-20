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
