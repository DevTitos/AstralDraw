import requests
import os
from dotenv import load_dotenv
load_dotenv()

# Configuration
TESTNET_MIRROR_URL = "https://testnet.mirrornode.hedera.com/api/v1"
YOUR_ACCOUNT_ID = os.getenv('OPERATOR_ID')
YOUR_TOKEN_ID = token_id = os.getenv('Token_ID')

def get_token_balance_for_account(account_id, token_id):
    """Get balance of a specific token for a given account"""
    url = f"{TESTNET_MIRROR_URL}/accounts/{account_id}/tokens"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        tokens = response.json().get('tokens', [])
        
        for token in tokens:
            if token['token_id'] == token_id:
                return int(token['balance'])
        return 0  # Token not found
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching balance: {e}")
        return None

def get_token_info(token_id):
    """Get token metadata including total supply"""
    url = f"{TESTNET_MIRROR_URL}/tokens/{token_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return {
            'name': data.get('name'),
            'symbol': data.get('symbol'),
            'total_supply': int(data.get('total_supply', 0)),
            'decimals': data.get('decimals', 0)
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching token info: {e}")
        return None
def get_token_transactions(token_id, account_id=None, limit=100):
    """Get all transactions involving a specific token"""
    url = f"{TESTNET_MIRROR_URL}/transactions/{account_id}"
    params = {'limit': limit}
    print(token_id)
    print(account_id)
    
    if account_id:
        params['account.id'] = account_id
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        transactions = []
        
        for tx in response.json().get('transactions', []):
            transactions.append({
                'transaction_id': tx['transaction_id'],
                'type': tx.get('name', 'Unknown'),
                'consensus_timestamp': tx['consensus_timestamp'],
                'sender': tx.get('account', ''),
                'amount': tx.get('amount', 0),
                'status': tx.get('result', 'UNKNOWN')
            })
        
        return transactions
    except requests.exceptions.RequestException as e:
        print(f"Error fetching transactions: {e}")
        return None
    
def get_all_token_holders(token_id, limit=100):
    """Get all accounts holding the specified token"""
    url = f"{TESTNET_MIRROR_URL}/tokens/{token_id}/balances"
    params = {'limit': limit}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return [
            {
                'account': entry['account'],
                'balance': int(entry['balance'])
            } for entry in response.json().get('balances', [])
        ]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching holders: {e}")
        return None

def display_balance_report():
    """Display comprehensive token balance report"""
    print("\n" + "="*50)
    print(f"TOKEN BALANCE REPORT (Testnet)")
    print("="*50)
    
    # 1. Show token info
    token_info = get_token_info(YOUR_TOKEN_ID)
    if not token_info:
        print("\n❌ Failed to retrieve token info")
        return
    
    print(f"\n🔹 Token: {token_info['name']} ({token_info['symbol']})")
    print(f"   Token ID: {YOUR_TOKEN_ID}")
    print(f"   Total Supply: {token_info['total_supply']}")
    print(f"   Decimals: {token_info['decimals']}")
    
    # 2. Show your balance
    your_balance = get_token_balance_for_account(YOUR_ACCOUNT_ID, YOUR_TOKEN_ID)
    if your_balance is not None:
        print(f"\n👤 Your Account: {YOUR_ACCOUNT_ID}")
        print(f"   Your Balance: {your_balance} tokens")
    
    # 3. Show all holders
    holders = get_all_token_holders(YOUR_TOKEN_ID)
    if holders:
        total_circulating = sum(h['balance'] for h in holders)
        print(f"\n📊 Holders ({len(holders)} accounts)")
        print(f"   Total Circulating: {total_circulating} tokens")
        
        print("\nTop Holders:")
        for holder in sorted(holders, key=lambda x: -x['balance'])[:5]:  # Show top 5
            print(f"   {holder['account']}: {holder['balance']:>12,} tokens")

def get_balance(id):
    #id = '0.0.6918174'
    url = f"https://testnet.mirrornode.hedera.com/api/v1/accounts/{id}/tokens"
    bal = requests.get(url=url)
    jsn = bal.json()
    tokens = jsn['tokens']
    balance = 0
    for token in tokens:
        if token['token_id'] == '0.0.6918197':
            balance = token['balance']
            return balance
    return balance

def transactions():
    url = f"https://testnet.mirrornode.hedera.com/api/v1/transactions"
    bal = requests.get(url=url)
    jsn = bal.json()
    print(jsn)