import os
import json
import time
import requests
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASIQ_API_URL = "https://au-api.basiq.io"
CACHE_FILE = "balance_cache.json"
TOKEN_FILE = "access_token.json"
TRANSACTIONS_CACHE_FILE = "transactions_cache.json"
DEMO_MODE = os.getenv('DEMO_MODE', 'false').lower() == 'true'
DISPLAY_TRANSACTIONS = os.getenv('DISPLAY_TRANSACTIONS', 'false').lower() == 'true'
# Consent flow configuration
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')  # Change in production!
CONSENT_CALLBACK_URL = os.getenv('CONSENT_CALLBACK_URL', 'http://localhost:5000/admin/consent-callback')

def get_stored_token():
    """Load stored access token from file"""
    try:
        with open(TOKEN_FILE, 'r') as f:
            token_data = json.load(f)
            if datetime.now() < datetime.fromisoformat(token_data['expires_at']):
                return token_data['access_token']
    except (FileNotFoundError, KeyError, ValueError):
        pass
    return None

def store_token(access_token, expires_in):
    """Store access token with expiration time"""
    expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # 60s buffer
    token_data = {
        'access_token': access_token,
        'expires_at': expires_at.isoformat()
    }
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f)

def get_access_token():
    """Get fresh access token from Basiq API"""
    stored_token = get_stored_token()
    if stored_token:
        print(f"[DEBUG] Using stored access token")
        return stored_token
    
    api_key = os.getenv('BASIQ_API_KEY')
    api_secret = os.getenv('BASIQ_API_SECRET')
    
    print(f"[DEBUG] API Key: {api_key}")
    print(f"[DEBUG] API Secret: {'*' * (len(api_secret) - 8) + api_secret[-8:] if api_secret else 'None'}")
    
    if not api_key or not api_secret:
        raise ValueError("Missing BASIQ_API_KEY or BASIQ_API_SECRET environment variables")
    
    # Basiq uses Basic Authentication with the API key for token requests
    import base64
    
    # Use the pre-encoded API secret directly (it's already base64 encoded)
    encoded_credentials = api_secret
    
    auth_url = f"{BASIQ_API_URL}/token"
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded',
        'basiq-version': '3.0'
    }
    
    # Basiq may require scope parameter
    data = {
        'scope': 'SERVER_ACCESS'
    }
    
    print(f"[DEBUG] Requesting token from: {auth_url}")
    print(f"[DEBUG] Using Basic Auth with encoded credentials")
    
    response = requests.post(auth_url, headers=headers, data=data)
    print(f"[DEBUG] Token response status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"[ERROR] Token request failed: {response.status_code} - {response.text}")
        response.raise_for_status()
    
    token_info = response.json()
    print(f"[DEBUG] Token response keys: {list(token_info.keys())}")
    access_token = token_info['access_token']
    expires_in = token_info.get('expires_in', 3600)
    
    print(f"[DEBUG] Successfully obtained access token, expires in {expires_in} seconds")
    store_token(access_token, expires_in)
    return access_token

def fetch_balance_from_basiq():
    """Fetch balance from Basiq API or return demo data"""
    if DEMO_MODE == 'true':
        # Return local fake data for testing
        import random
        demo_balance = round(random.uniform(1200, 5000), 2)
        print(f"[DEBUG] Using local fake data: ${demo_balance}")
        return {
            'balance': demo_balance,
            'currency': 'AUD',
            'last_updated': datetime.now().isoformat(),
            'status': 'success'
        }
    elif DEMO_MODE == 'sandbox':
        print(f"[DEBUG] Using sandbox mode with Basiq API")
    
    try:
        print(f"[DEBUG] Fetching access token...")
        access_token = get_access_token()
        user_id = os.getenv('BASIQ_USER_ID')
        
        print(f"[DEBUG] User ID: {user_id}")
        
        if not user_id:
            raise ValueError("Missing BASIQ_USER_ID environment variable")
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        # Get accounts
        accounts_url = f"{BASIQ_API_URL}/users/{user_id}/accounts"
        print(f"[DEBUG] Calling Basiq API: {accounts_url}")
        
        response = requests.get(accounts_url, headers=headers)
        print(f"[DEBUG] Basiq API response status: {response.status_code}")
        print(f"[DEBUG] Basiq API response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"[ERROR] Basiq API error: {response.status_code} - {response.text}")
            return {'error': f'Basiq API error: {response.status_code}', 'status': 'error'}
        
        accounts_data = response.json()
        print(f"[DEBUG] Accounts data received: {accounts_data}")
        
        # Find account and get balance - configurable via environment variable
        target_institution = os.getenv('BASIQ_TARGET_INSTITUTION')
        if not target_institution:
            # Default fallback based on demo mode
            target_institution = 'AU.SUNCORP' if DEMO_MODE != 'sandbox' else 'AU00000'  # Hooli bank ID
        print(f"[DEBUG] Looking for institution: {target_institution}")
        
        if not accounts_data.get('data'):
            print(f"[ERROR] No accounts found in response")
            return {'error': 'No accounts found', 'status': 'error'}
        
        for account in accounts_data.get('data', []):
            # Institution can be either a string ID or an object with 'id' field
            institution = account.get('institution')
            if isinstance(institution, dict):
                institution_id = institution.get('id')
            else:
                institution_id = institution
            print(f"[DEBUG] Found account with institution: {institution_id}")
            
            if institution_id == target_institution or DEMO_MODE == 'sandbox':
                # In sandbox, use first available account
                balance_data = account.get('balance')
                # Balance can be either a string value or object with 'current' field
                if isinstance(balance_data, dict):
                    balance = float(balance_data.get('current', 0))
                else:
                    balance = float(balance_data or 0)
                print(f"[DEBUG] Found matching account with balance: ${balance}")
                return {
                    'balance': balance,
                    'currency': 'AUD',
                    'last_updated': datetime.now().isoformat(),
                    'status': 'success'
                }
        
        bank_name = 'Hooli' if DEMO_MODE == 'sandbox' else 'Suncorp'
        print(f"[ERROR] {bank_name} account not found in {len(accounts_data.get('data', []))} accounts")
        return {'error': f'{bank_name} account not found', 'status': 'error'}
        
    except Exception as e:
        print(f"[ERROR] Exception in fetch_balance_from_basiq: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e), 'status': 'error'}

def fetch_transactions_from_basiq():
    """Fetch recent transactions from Basiq API or return demo data"""
    if not DISPLAY_TRANSACTIONS:
        return {'error': 'Transactions display disabled', 'status': 'disabled'}
    
    if DEMO_MODE == 'true':
        # Return local fake transaction data for testing
        import random
        
        demo_transactions = []
        for i in range(15):  # Generate 15 demo transactions
            days_ago = random.randint(0, 90)
            date = datetime.now() - timedelta(days=days_ago)
            amount = round(random.uniform(-200, -10), 2)  # Mostly expenses
            if random.random() > 0.8:  # 20% chance of income
                amount = abs(amount) * random.uniform(5, 20)
            
            merchants = ['Woolworths', 'Coles', 'Shell', 'McDonald\'s', 'Netflix', 'Spotify', 
                        'Amazon', 'Uber', 'Coffee Club', 'IGA', 'Bunnings', 'Chemist Warehouse']
            
            demo_transactions.append({
                'id': f'demo_txn_{i}',
                'description': random.choice(merchants),
                'amount': amount,
                'postDate': date.isoformat(),
                'direction': 'debit' if amount < 0 else 'credit'
            })
        
        print(f"[DEBUG] Using demo transactions: {len(demo_transactions)} items")
        return {
            'transactions': demo_transactions,
            'last_updated': datetime.now().isoformat(),
            'status': 'success'
        }
    
    try:
        print(f"[DEBUG] Fetching transactions...")
        access_token = get_access_token()
        user_id = os.getenv('BASIQ_USER_ID')
        
        if not user_id:
            raise ValueError("Missing BASIQ_USER_ID environment variable")
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        # Get transactions with pagination
        transactions_url = f"{BASIQ_API_URL}/users/{user_id}/transactions"
        print(f"[DEBUG] Calling Basiq transactions API: {transactions_url}")
        
        # Add query parameters for recent transactions
        params = {
            'limit': 50,  # Get last 50 transactions
            'sort': '-postDate'  # Sort by most recent first
        }
        
        response = requests.get(transactions_url, headers=headers, params=params)
        print(f"[DEBUG] Basiq transactions API response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[ERROR] Basiq transactions API error: {response.status_code} - {response.text}")
            return {'error': f'Basiq transactions API error: {response.status_code}', 'status': 'error'}
        
        transactions_data = response.json()
        print(f"[DEBUG] Transactions data received: {len(transactions_data.get('data', []))} transactions")
        
        # Filter and sanitize transaction data for public display
        safe_transactions = []
        for txn in transactions_data.get('data', []):
            safe_transactions.append({
                'id': txn.get('id'),
                'description': txn.get('description', 'Unknown'),
                'amount': float(txn.get('amount', 0)),
                'postDate': txn.get('postDate'),
                'direction': txn.get('direction', 'unknown')
            })
        
        return {
            'transactions': safe_transactions,
            'last_updated': datetime.now().isoformat(),
            'status': 'success'
        }
        
    except Exception as e:
        print(f"[ERROR] Exception in fetch_transactions_from_basiq: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e), 'status': 'error'}

def get_cached_transactions():
    """Get transactions from cache file"""
    try:
        with open(TRANSACTIONS_CACHE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'error': 'No cached transactions found', 'status': 'error'}

def cache_transactions(transactions_data):
    """Save transactions to cache file"""
    with open(TRANSACTIONS_CACHE_FILE, 'w') as f:
        json.dump(transactions_data, f)

def create_basiq_user():
    """Create a new user in Basiq for consent flow"""
    try:
        access_token = get_access_token()
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'basiq-version': '3.0'
        }
        
        # Create user with minimal data
        user_data = {
            'email': f'user_{int(time.time())}@example.com',  # Unique email
            'mobile': '+61400000000'  # Placeholder mobile
        }
        
        create_user_url = f"{BASIQ_API_URL}/users"
        print(f"[DEBUG] Creating Basiq user: {create_user_url}")
        
        response = requests.post(create_user_url, headers=headers, json=user_data)
        print(f"[DEBUG] Create user response status: {response.status_code}")
        
        if response.status_code != 201:
            print(f"[ERROR] User creation failed: {response.status_code} - {response.text}")
            return None
            
        user_response = response.json()
        user_id = user_response.get('id')
        print(f"[DEBUG] Created user with ID: {user_id}")
        
        return user_id
        
    except Exception as e:
        print(f"[ERROR] Exception in create_basiq_user: {str(e)}")
        return None

def generate_client_token(user_id):
    """Generate CLIENT token bound to specific userId for consent flow"""
    try:
        api_key = os.getenv('BASIQ_API_KEY')
        api_secret = os.getenv('BASIQ_API_SECRET')
        
        if not api_key or not api_secret:
            raise ValueError("Missing BASIQ_API_KEY or BASIQ_API_SECRET environment variables")
        
        auth_url = f"{BASIQ_API_URL}/token"
        headers = {
            'Authorization': f'Basic {api_secret}',
            'Content-Type': 'application/x-www-form-urlencoded',
            'basiq-version': '3.0'
        }
        
        # Request CLIENT token bound to userId
        data = {
            'scope': 'CLIENT_ACCESS',
            'userId': user_id
        }
        
        print(f"[DEBUG] Requesting CLIENT token for user: {user_id}")
        
        response = requests.post(auth_url, headers=headers, data=data)
        print(f"[DEBUG] CLIENT token response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[ERROR] CLIENT token request failed: {response.status_code} - {response.text}")
            return None
        
        token_info = response.json()
        client_token = token_info.get('access_token')
        
        print(f"[DEBUG] Successfully generated CLIENT token")
        return client_token
        
    except Exception as e:
        print(f"[ERROR] Exception in generate_client_token: {str(e)}")
        return None

def get_cached_balance():
    """Get balance from cache file"""
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'error': 'No cached balance found', 'status': 'error'}

def cache_balance(balance_data):
    """Save balance to cache file"""
    with open(CACHE_FILE, 'w') as f:
        json.dump(balance_data, f)

@app.route('/get-balance')
def get_balance():
    """API endpoint to get current balance"""
    cached_data = get_cached_balance()
    
    # Return cached data if it exists and is recent (less than 24 hours old)
    if cached_data.get('status') == 'success':
        try:
            last_updated = datetime.fromisoformat(cached_data['last_updated'])
            if datetime.now() - last_updated < timedelta(hours=24):
                return jsonify(cached_data)
        except (KeyError, ValueError):
            pass
    
    # Fetch fresh data
    balance_data = fetch_balance_from_basiq()
    
    if balance_data.get('status') == 'success':
        cache_balance(balance_data)
    
    # Return only safe data (no sensitive info)
    safe_data = {
        'balance': balance_data.get('balance'),
        'currency': balance_data.get('currency', 'AUD'),
        'last_updated': balance_data.get('last_updated'),
        'status': balance_data.get('status')
    }
    
    if balance_data.get('status') == 'error':
        safe_data['error'] = 'Unable to fetch balance'
    
    return jsonify(safe_data)

@app.route('/get-transactions')
def get_transactions():
    """API endpoint to get recent transactions"""
    if not DISPLAY_TRANSACTIONS:
        return jsonify({'error': 'Transactions display disabled', 'status': 'disabled'})
    
    cached_data = get_cached_transactions()
    
    # Return cached data if it exists and is recent (less than 1 hour old)
    if cached_data.get('status') == 'success':
        try:
            last_updated = datetime.fromisoformat(cached_data['last_updated'])
            if datetime.now() - last_updated < timedelta(hours=1):
                return jsonify(cached_data)
        except (KeyError, ValueError):
            pass
    
    # Fetch fresh transaction data
    transactions_data = fetch_transactions_from_basiq()
    
    if transactions_data.get('status') == 'success':
        cache_transactions(transactions_data)
    
    # Return only safe transaction data (no account numbers, user IDs, etc.)
    safe_data = {
        'transactions': transactions_data.get('transactions', []),
        'last_updated': transactions_data.get('last_updated'),
        'status': transactions_data.get('status')
    }
    
    if transactions_data.get('status') == 'error':
        safe_data['error'] = 'Unable to fetch transactions'
    
    return jsonify(safe_data)

@app.route('/refresh-balance')
def refresh_balance():
    """Force refresh balance from API"""
    balance_data = fetch_balance_from_basiq()
    
    if balance_data.get('status') == 'success':
        cache_balance(balance_data)
    
    return jsonify({
        'balance': balance_data.get('balance'),
        'currency': balance_data.get('currency', 'AUD'),
        'last_updated': balance_data.get('last_updated'),
        'status': balance_data.get('status')
    })

@app.route('/admin/setup', methods=['GET', 'POST'])
def admin_setup():
    """Admin interface for setting up Basiq consent flow"""
    if DEMO_MODE:
        return jsonify({'error': 'Admin setup not available in demo mode', 'status': 'disabled'})
    
    # Simple password protection
    if request.method == 'POST':
        password = request.form.get('password')
        action = request.form.get('action')
        
        if password != ADMIN_PASSWORD:
            return render_template_string(ADMIN_SETUP_TEMPLATE, error='Invalid password')
        
        if action == 'create_user':
            # Step 1: Create user and generate consent URL
            user_id = create_basiq_user()
            if not user_id:
                return render_template_string(ADMIN_SETUP_TEMPLATE, error='Failed to create user')
            
            client_token = generate_client_token(user_id)
            if not client_token:
                return render_template_string(ADMIN_SETUP_TEMPLATE, error='Failed to generate CLIENT token')
            
            # Generate consent URL
            consent_url = f"https://consent.basiq.io/home?token={client_token}"
            
            return render_template_string(ADMIN_SETUP_TEMPLATE, 
                                          success=True,
                                          user_id=user_id,
                                          consent_url=consent_url)
    
    return render_template_string(ADMIN_SETUP_TEMPLATE)

@app.route('/admin/consent-callback')
def consent_callback():
    """Handle Basiq consent callback"""
    # Get consent response parameters
    consent_granted = request.args.get('success')
    user_id = request.args.get('userId')
    error = request.args.get('error')
    
    print(f"[DEBUG] Consent callback - Success: {consent_granted}, User ID: {user_id}, Error: {error}")
    
    if consent_granted == 'true' and user_id:
        # Store the user ID for production use
        with open('production_user_id.txt', 'w') as f:
            f.write(user_id)
        
        return render_template_string(CONSENT_SUCCESS_TEMPLATE, user_id=user_id)
    else:
        return render_template_string(CONSENT_ERROR_TEMPLATE, error=error or 'Consent was denied')

@app.route('/')
def index():
    """Serve the main dashboard page"""
    return render_template_string(open('index.html').read())

# HTML Templates for Admin Interface
ADMIN_SETUP_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Setup - Basiq Consent Flow</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
        .error { color: red; margin: 10px 0; }
        .success { color: green; margin: 10px 0; }
        input, button { margin: 5px 0; padding: 10px; }
        button { background: #007cba; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .consent-url { background: #f0f0f0; padding: 15px; margin: 15px 0; word-break: break-all; }
    </style>
</head>
<body>
    <h1>🔐 Basiq Consent Flow Setup</h1>
    <p><strong>⚠️ WARNING:</strong> This is a one-time setup process for production deployment.</p>
    
    {% if error %}
        <div class="error">❌ {{ error }}</div>
    {% endif %}
    
    {% if success %}
        <div class="success">✅ User created successfully!</div>
        <p><strong>User ID:</strong> {{ user_id }}</p>
        <p><strong>Next Steps:</strong></p>
        <ol>
            <li>Click the consent URL below to complete account connection</li>
            <li>Login with your Suncorp banking credentials</li>
            <li>Grant consent for balance access</li>
            <li>You'll be redirected back to confirm success</li>
        </ol>
        
        <div class="consent-url">
            <strong>Consent URL:</strong><br>
            <a href="{{ consent_url }}" target="_blank">{{ consent_url }}</a>
        </div>
        
        <p><em>⚠️ After completing consent, remove this admin route for security!</em></p>
    {% else %}
        <form method="post">
            <h3>Step 1: Authenticate</h3>
            <input type="password" name="password" placeholder="Admin Password" required>
            <br>
            <button type="submit" name="action" value="create_user">🚀 Start Consent Flow</button>
        </form>
        
        <div style="margin-top: 30px; padding: 15px; background: #f9f9f9;">
            <h4>🔐 Security Notes:</h4>
            <ul>
                <li>This creates a new user in Basiq for your production app</li>
                <li>You'll be redirected to Basiq's secure consent UI</li>
                <li>Your banking credentials never touch this server</li>
                <li>This route should be disabled after setup</li>
            </ul>
        </div>
    {% endif %}
</body>
</html>
"""

CONSENT_SUCCESS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Consent Granted - Success!</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }
        .success { color: green; font-size: 18px; }
        .user-id { background: #e8f5e8; padding: 15px; margin: 20px 0; border-radius: 8px; }
    </style>
</head>
<body>
    <h1>🎉 Account Connected Successfully!</h1>
    <div class="success">
        ✅ Your Suncorp account has been securely connected to the balance dashboard.
    </div>
    
    <div class="user-id">
        <strong>Production User ID:</strong><br>
        <code>{{ user_id }}</code><br>
        <small>(This has been saved to production_user_id.txt)</small>
    </div>
    
    <h3>Next Steps:</h3>
    <ol style="text-align: left;">
        <li>Add this User ID to your production environment variables</li>
        <li>Update your .env file: <code>BASIQ_USER_ID={{ user_id }}</code></li>
        <li>Remove or disable the /admin/setup route for security</li>
        <li>Your balance dashboard is now ready for production!</li>
    </ol>
    
    <p><a href="/">← Return to Balance Dashboard</a></p>
</body>
</html>
"""

CONSENT_ERROR_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Consent Failed</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }
        .error { color: red; font-size: 18px; }
    </style>
</head>
<body>
    <h1>❌ Account Connection Failed</h1>
    <div class="error">
        {{ error }}
    </div>
    
    <p>Please try the setup process again:</p>
    <p><a href="/admin/setup">← Return to Admin Setup</a></p>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True, port=5000)