# 💰 Transparent Balance App

A secure, public-facing dashboard that displays your Suncorp bank balance using Basiq's Open Banking API under Australia's Consumer Data Right (CDR) framework.

## 🎯 Overview

This application provides a **read-only, public dashboard** showing a personal bank balance with:
- Secure server-side API integration
- Daily balance caching to minimize API calls
- Embeddable widget for website integration
- No sensitive data exposure

## 🔐 Security First

- ✅ All credentials stored server-side only
- ✅ No account numbers, user IDs, or metadata exposed
- ✅ Token refresh logic with automatic expiry handling
- ✅ Read-only public display with no user authentication flows
- ✅ Environment-based configuration

## 📁 Project Structure

```
TransparentBalanceApp/
├── app.py              # Flask backend with Basiq API integration
├── index.html          # Main dashboard with elegant UI
├── widget.html         # Embeddable widget example
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker container configuration
├── docker-compose.yml  # Docker Compose for easy deployment
├── .dockerignore       # Docker build optimization
├── .env.example        # Environment configuration template
├── README.md          # This file
├── CLAUDE.MD          # Project instructions
└── OVERVIEW.MD        # Project overview
```

## 🚀 Quick Start

### 🐳 Docker (Recommended)

#### 🚀 Quick Demo Options

**Option 1: Local Fake Data (No API calls)**
```bash
# 1. Edit .env.demo file:
#    DEMO_MODE=true
# 2. Start demo container
docker compose -f docker-compose.demo.yml up -d
open http://localhost:5001
```

**Option 2: Real Basiq Sandbox with Hooli Bank 🏦**
```bash
# 1. Get free sandbox credentials from https://dashboard.basiq.io/
# 2. Create demo user with Hooli bank connection (see guide below)
# 3. Edit .env.demo with your actual sandbox credentials:
#    DEMO_MODE=sandbox
#    BASIQ_API_KEY=your_sandbox_api_key_name
#    BASIQ_API_SECRET=your_sandbox_api_key_secret
#    BASIQ_USER_ID=your_demo_user_id_with_hooli
# 4. Start container (will now use real Basiq API)
docker compose -f docker-compose.demo.yml up -d
open http://localhost:5001
```

**🔄 Switching Between Modes:**
- Edit `.env.demo` and change `DEMO_MODE=true` (fake data) or `DEMO_MODE=sandbox` (real API)
- Restart container: `docker compose -f docker-compose.demo.yml restart`

#### 🏦 Production Setup (With Real Basiq Data)

For real bank data:

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your Basiq API key credentials

# 2. Start with Docker Compose
docker compose up -d

# 3. View your dashboard
open http://localhost:5001
```

### 🐍 Manual Python Setup

If you prefer running without Docker:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your Basiq API key credentials

# 3. Run the application
python app.py
```

Visit `http://localhost:5001` to see your dashboard.

## 🔧 API Endpoints

- `GET /get-balance` - Returns cached balance (24-hour cache)
- `GET /refresh-balance` - Forces fresh balance fetch
- `GET /` - Serves the main dashboard

### Response Format

```json
{
  "balance": 1542.55,
  "currency": "AUD",
  "last_updated": "2024-01-15T10:30:00",
  "status": "success"
}
```

## 🎨 Embedding the Widget

The balance widget can be embedded into any website. See `widget.html` for a complete example.

### Quick Embed

1. Copy the CSS, HTML, and JavaScript from the marked sections in `index.html`
2. Update the API URL to your production server
3. Paste into your website

Example:
```html
<!-- Copy the widget code from widget.html -->
<div class="balance-widget" id="balanceWidget">
  <!-- Widget content -->
</div>
```

## 📊 Features

- **Automatic Caching** - Fetches balance once per 24 hours
- **Manual Refresh** - Button to force immediate update
- **Responsive Design** - Works on desktop and mobile
- **Error Handling** - Graceful fallback for API issues
- **Status Indicators** - Visual feedback for connection status

## 🔄 Token Management

The app automatically handles:
- Access token refresh (hourly)
- Token expiry with 60-second buffer
- File-based token storage
- Consent expiration handling

## 📅 Basiq Integration

### 🔐 Creating Secure API Credentials

#### Step 1: Create Basiq Developer Account
1. Visit [Basiq Dashboard](https://dashboard.basiq.io/)
2. Sign up for free developer access
3. Log in with your developer credentials

#### Step 2: Create Application
1. Go to "Applications" → "Create Application"
2. Name it: `BalanceViewerReadOnly` or whatever.. 
3. Select environment:
   - **Sandbox** for testing with Hooli demo bank (FREE, 500 connection limit)
   - **Production** for live Suncorp data (AUD $0.39/month/user)

#### Step 3: Generate API Key
1. Within your application, go to "API Keys" tab
2. Click "Create Key"
3. **API Key Name**: `balance-key` (this becomes your `BASIQ_API_KEY`)
4. **Copy the API Key Secret immediately** (cannot retrieve later - this becomes your `BASIQ_API_SECRET`)

#### Step 4: Set Minimal Permissions (Security Critical)

**✅ Required Permissions for Balance-Only Access:**

Under **Accounts**:
- ✅ `GET /users/{userId}/accounts`
- ✅ `GET /users/{userId}/accounts/{accountId}`

Under **Actions** (required for data sync):
- ✅ `POST /users/{userId}/actions`
- ✅ `GET /users/{userId}/actions`
- ✅ `GET /users/{userId}/actions/{actionId}`
- ✅ `GET /actions/{actionId}/results`
- ✅ `GET /actions/{actionId}/results/{resultId}`

**❌ Disable Everything Else** for minimal attack surface.

#### Step 5: Security Best Practices
- Store API key and secret in `.env` file (never commit to Git)
- Use secrets manager in production (AWS Secrets Manager, etc.)
- Set strict read-only file permissions on config files
- Regularly rotate API key credentials

### 🏦 Connecting Bank Accounts

#### Option A: Hooli Demo Bank (Sandbox Testing) 🧪

**Perfect for testing without real bank credentials!**

1. **Complete API Setup** (Sandbox environment)
2. **Create Demo User**
   - Go to "Users" section in Basiq Dashboard
   - Click "Create User"
   - Name: `hooli-demo-user`
   - **Copy the User ID**

3. **Connect Hooli Demo Bank**
   - Click "Connect Account" in user details
   - Search for and select **"Hooli Bank"**
   - Use these test credentials:
     - **Username**: `Wentworth-Smith`
     - **Password**: `whislter`
   - Complete the demo authentication flow
   - **No real bank details required!**

#### Option B: Real Suncorp Account (Production) 🏦

**Important:** This is a **one-time private setup** - never expose this flow publicly.

1. **Complete API Setup** (Production environment)
2. **Create a User**
   - Go to "Users" section
   - Click "Create User" 
   - Give it a name like `suncorp-balance-user`
   - **Copy the User ID** - you'll need this for `BASIQ_USER_ID`

3. **Connect Real Suncorp Account**
   - In the user details, click "Connect Account"
   - Select "Suncorp Bank" from the institution list
   - **Enter your actual Suncorp online banking credentials**
   - Complete any multi-factor authentication
   - Grant consent for balance access (90-365 days)

4. **Verify Connection**
   - You should see your Suncorp account listed
   - Note the account ID and current balance
   - **Your User ID is now ready for the app**

#### Step 3: Add User ID to Environment
```bash
# Add this to your .env file (along with your API key credentials)
BASIQ_API_KEY=your_api_key_name
BASIQ_API_SECRET=your_api_key_secret
BASIQ_USER_ID=your_copied_user_id_here
```

#### Step 4: Test Connection
```bash
# Start your app and test
docker compose up -d
curl http://localhost:5001/get-balance
```

### Important Security Notes

- ⚠️ **This connection process should ONLY be done by you privately**
- ⚠️ **Never expose the connection flow in your public application**
- ⚠️ **Monitor consent expiration** (typically 90-365 days)
- ⚠️ **Keep your Basiq dashboard access secure**

### Environment Setup

1. Use sandbox for testing (free) or production (AUD $0.39/month/user)
2. Refer to [Basiq Documentation](https://api.basiq.io/docs/) for latest requirements
3. Monitor your usage in the Basiq dashboard

### Supported Banks

Currently configured for Suncorp Bank (`AU.SUNCORP`), but can be extended to other CDR-compliant banks.

## 🛠️ Customization

### Styling

Modify the CSS in `index.html` to match your website's design:
- Colors, fonts, and layout in `.balance-widget` class
- Responsive breakpoints
- Animation and transition effects

### Refresh Interval

Change the auto-refresh interval (default: 30 minutes):
```javascript
setInterval(() => widget.fetchBalance(), 30 * 60 * 1000); // 30 minutes
```

## 📝 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BASIQ_API_KEY` | Your Basiq API key name | Yes |
| `BASIQ_API_SECRET` | Your Basiq API key secret | Yes |
| `BASIQ_USER_ID` | User ID from connecting your bank account | Yes |
| `FLASK_ENV` | Flask environment (production/development) | No |
| `FLASK_DEBUG` | Enable Flask debug mode | No |

### Cache Files

- `balance_cache.json` - Stores the latest balance data
- `access_token.json` - Stores API access tokens with expiry

## 🔒 Security Considerations

- Never commit `.env` files to version control
- Use HTTPS in production
- Set appropriate file permissions for cache files
- Regularly rotate API credentials
- Monitor for consent expiration (90-365 days)

## 🌐 Deployment

### 🐳 Docker Deployment (Recommended)

For production with Docker:

```bash
# 1. Clone and configure
git clone <your-repo>
cd TransparentBalanceApp
cp .env.example .env
# Edit .env with production credentials

# 2. Deploy with Docker Compose
docker compose up -d

# 3. Set up reverse proxy (nginx/traefik) for HTTPS
# 4. Schedule daily refresh via cron
0 6 * * * docker exec suncorp-balance-dashboard curl -s http://localhost:5001/refresh-balance
```

### 🔧 Manual Deployment

For traditional server deployment:

1. Set `FLASK_ENV=production` in your environment
2. Use a production WSGI server (gunicorn, uWSGI)
3. Configure reverse proxy (nginx, Apache)
4. Set up SSL certificates
5. Schedule daily balance fetching via cron

Example cron job:
```bash
0 6 * * * curl -s http://localhost:5001/refresh-balance
```

### 🛟 Docker Commands

```bash
# View logs
docker compose logs -f

# Stop the application
docker compose down

# Rebuild after changes
docker compose up --build -d

# Execute commands in container
docker exec -it suncorp-balance-dashboard /bin/bash
```

## 📞 Support

- Check the [Basiq Documentation](https://api.basiq.io/docs/)
- Review CDR compliance requirements
- Monitor consent expiration dates

## ⚖️ Legal & Compliance

This application is designed for personal use under Australia's Consumer Data Right framework. Ensure compliance with:
- CDR privacy requirements
- Data handling obligations
- Consent management rules

---

Built with security and privacy as top priorities. 🔐