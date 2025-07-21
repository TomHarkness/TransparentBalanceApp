import os
import json
import time
import requests
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASIQ_API_URL = "https://au-api.basiq.io"
CACHE_FILE = "balance_cache.json"
TOKEN_FILE = "access_token.json"
DEMO_MODE = os.getenv('DEMO_MODE', 'false').lower() == 'true'

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
        return stored_token
    
    client_id = os.getenv('BASIQ_CLIENT_ID')
    client_secret = os.getenv('BASIQ_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        raise ValueError("Missing BASIQ_CLIENT_ID or BASIQ_CLIENT_SECRET environment variables")
    
    auth_url = f"{BASIQ_API_URL}/token"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    response = requests.post(auth_url, headers=headers, data=data)
    response.raise_for_status()
    
    token_info = response.json()
    access_token = token_info['access_token']
    expires_in = token_info.get('expires_in', 3600)
    
    store_token(access_token, expires_in)
    return access_token

def fetch_balance_from_basiq():
    """Fetch balance from Basiq API or return demo data"""
    if DEMO_MODE:
        # Return demo data for testing
        import random
        demo_balance = round(random.uniform(1200, 5000), 2)
        return {
            'balance': demo_balance,
            'currency': 'AUD',
            'last_updated': datetime.now().isoformat(),
            'status': 'success'
        }
    
    try:
        access_token = get_access_token()
        user_id = os.getenv('BASIQ_USER_ID')
        
        if not user_id:
            raise ValueError("Missing BASIQ_USER_ID environment variable")
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        # Get accounts
        accounts_url = f"{BASIQ_API_URL}/users/{user_id}/accounts"
        response = requests.get(accounts_url, headers=headers)
        response.raise_for_status()
        
        accounts_data = response.json()
        
        # Find Suncorp account and get balance
        for account in accounts_data.get('data', []):
            if account.get('institution', {}).get('id') == 'AU.SUNCORP':
                balance = float(account.get('balance', {}).get('current', 0))
                return {
                    'balance': balance,
                    'currency': 'AUD',
                    'last_updated': datetime.now().isoformat(),
                    'status': 'success'
                }
        
        return {'error': 'Suncorp account not found', 'status': 'error'}
        
    except Exception as e:
        return {'error': str(e), 'status': 'error'}

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

@app.route('/')
def index():
    """Serve the main dashboard page"""
    return render_template_string(open('index.html').read())

if __name__ == '__main__':
    app.run(debug=True, port=5000)