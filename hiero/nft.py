import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
    TransferTransaction,
    TokenId,
)
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenType
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
import json

load_dotenv()

def setup_client():
    """Initialize and set up the client with operator account"""
    # Initialize network and client
    network = Network(network='testnet')
    client = Client(network)

    # Set up operator account
    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    client.set_operator(operator_id, operator_key)
    
    return client, operator_id, operator_key

def create_test_account(client):
    """Create a new account for testing"""
    # Generate private key for new account
    new_account_private_key = PrivateKey.generate()
    new_account_public_key = new_account_private_key.public_key()
    client, operator_id, operator_key = setup_client()
    # Create new account with initial balance of 1 HBAR
    transaction = (
        AccountCreateTransaction()
        .set_key(new_account_public_key)
        .set_initial_balance(Hbar(1000))
        .freeze_with(client)
    )
    
    receipt = transaction.execute(client)
    
    # Check if account creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Account creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)
    
    # Get account ID from receipt
    account_id = receipt.account_id
    print(f"New account created with ID: {account_id}")
    
    return account_id, new_account_private_key

# The Astral Council
# Stellar Assembly SLA
# Celestial Board CLB
# Cosmic Community 
def create_nft(title, symbol):
    """Create a non-fungible token EG"""

    client, operator_id, operator_key = setup_client()
    transaction = (
        TokenCreateTransaction()
        .set_token_name(title)
        .set_token_symbol(symbol)
        .set_decimals(0)
        .set_initial_supply(0)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(10000000)
        .set_admin_key(operator_key)
        .set_supply_key(operator_key)
        .set_freeze_key(operator_key)
        .freeze_with(client)
    )
    
    receipt = transaction.execute(client)
    
    # Check if nft creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT creation failed with status: {ResponseCode(receipt.status).name}")
        return {
            'status':'failed'
        }
    
    # Get token ID from receipt
    nft_token_id = receipt.token_id
    print(f"NFT created with ID: {nft_token_id}")
    
    return {
        'token_id':nft_token_id,
        'status':'success',
    }

def mint_nft(nft_token_id, metadata):
    """Mint a non-fungible token"""
    client, operator_id, operator_key = setup_client()

    transaction = (
        TokenMintTransaction()
        .set_token_id(TokenId.from_string(nft_token_id))
        .set_metadata(metadata.encode("utf-8"))
        .freeze_with(client)
    )

    # Execute and get receipt
    receipt = transaction.execute(client)
    print(receipt)
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT minting failed with status: {ResponseCode(receipt.status).name}")
        return {
            'status':'failed',
            'message':ResponseCode(receipt.status).name
        }
        #sys.exit(1)
    
    print(f"NFT minted with serial number: {receipt.serial_numbers[0]}")
    
    return {
        'status':'success',
        'message':NftId(TokenId.from_string(nft_token_id), receipt.serial_numbers[0]),
        'serial':receipt.serial_numbers[0],
    }

def associate_nft(account_id, token_id, account_private_key, nft_id):
    """Associate a non-fungible token with an account"""
    # Associate the token_id with the new account
    client, operator_id, operator_key = setup_client()
    print(type(account_private_key))
    import re
    
    match = re.search(r"hex=([0-9a-fA-F]+)", account_private_key)
    if match:
        private_key_only = match.group(1)
        print(private_key_only)
    else:
        private_key_only = None
        print("No private key found")

    associate_transaction = (
        TokenAssociateTransaction()
        .set_account_id(AccountId.from_string(account_id))
        .add_token_id(TokenId.from_string(token_id))
        .freeze_with(client)
        .sign(PrivateKey.from_string(private_key_only)) # Has to be signed by new account's key
    )
    receipt = associate_transaction.execute(client)
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT association failed with status: {ResponseCode(receipt.status).name}")
        return None
    print("NFT successfully associated with account")
    # Transfer nft to the new account
    print(type(nft_id))
    transfer_transaction = (
        TransferTransaction()
        .add_nft_transfer(nft_id, operator_id, AccountId.from_string(account_id))
        .freeze_with(client)
    )
    
    receipt = transfer_transaction.execute(client)
    
    # Check if nft transfer was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT transfer failed with status: {ResponseCode(receipt.status).name}")
        return {
            'status':'failed',
            'message':f'NFT transfer failed with status: {ResponseCode(receipt.status).name}"'
        }
    
    print(f"Successfully transferred NFT to account {account_id}")
    return {
        'status':'success',
        'message':f"Successfully transferred NFT to account {account_id}"
    }