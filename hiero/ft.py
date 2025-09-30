import os
import sys
from dotenv import load_dotenv
from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    TokenCreateTransaction,
    Network,
    TokenType,
    SupplyType,
    TokenId,
    TransferTransaction,
    AccountCreateTransaction,
    TokenAssociateTransaction,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
load_dotenv()
import re
operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
token_id = TokenId.from_string(os.getenv('Token_ID'))
nbl_id = AccountId.from_string(os.getenv('NBL_ID'))
nbl_key = PrivateKey.from_string_ed25519(os.getenv('NBL_KEY'))

def fund_pool(recipient_id, amount, account_private_key):
    network = Network(network='testnet')
    client = Client(network)
    
    client.set_operator(operator_id, operator_key)
    match = re.search(r"hex=([0-9a-fA-F]+)", account_private_key)
    if match:
        private_key_only = match.group(1)
        print(private_key_only)
    else:
        private_key_only = None
        print("No private key found")
    transaction = (
        TransferTransaction()
        .add_token_transfer(token_id, AccountId.from_string(recipient_id), -amount)
        .add_token_transfer(token_id, nbl_id, amount)
        .freeze_with(client)
        .sign(PrivateKey.from_string(private_key_only))
    )

    try:
        receipt = transaction.execute(client)
        print("Token transfer successful.")
        return {
            "status":"success",
            "receipt":receipt,
        }
    except Exception as e:
        print(f"Token transfer failed: {str(e)}")
        return {
            "status":"failed",
            "error":str(e),
        }
    
def transfer_tokens(recipient_id, amount):
    network = Network(network='testnet')
    client = Client(network)
    
    client.set_operator(operator_id, operator_key)
    recp_id = AccountId.from_string(recipient_id)
    transaction = (
        TransferTransaction()
        .add_token_transfer(token_id, operator_id, -amount)
        .add_token_transfer(token_id, recp_id, amount)
        .freeze_with(client)
        .sign(operator_key)
    )

    try:
        receipt = transaction.execute(client)
        print("Token transfer successful.")
        print(receipt)
        return {
            "status":"success",
            "receipt":receipt,
        }
    except Exception as e:
        print(f"Token transfer failed: {str(e)}")
        return {
            "status":"failed",
            "error":str(e),
        }


def associate_token(recipient_id_new, recipient_key_new):
    network = Network(network='testnet')
    client = Client(network)
    client.set_operator(operator_id, operator_key)

    transaction = (
        TokenAssociateTransaction()
        .set_account_id(recipient_id_new)
        .add_token_id(token_id)
        .freeze_with(client)
        .sign(recipient_key_new)
    )

    try:
        receipt = transaction.execute(client)
        print("Token association successful.")
    except Exception as e:
        print(f"Token association failed: {str(e)}")



def create_token_fungible_finite():
    """Function to create a finite fungible token."""
    # Network Setup
    network = Network(network='testnet')
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))

    # 2. Generate Keys On-the-Fly
    # =================================================================
    print("\nGenerating new admin and supply keys for the token...")
    admin_key = PrivateKey.generate_ed25519()
    supply_key = PrivateKey.generate_ed25519()
    pause_key = PrivateKey.generate_ed25519()
    freeze_key = PrivateKey.generate_ed25519()
    print(f"✅ Keys generated successfully.\nADMIN KEY: {admin_key}\nSUPPLY KEY: {supply_key}\nPAUSE_KEY: {pause_key}\nFREEZE KEY: {freeze_key}")
    # Set the operator for the client
    client.set_operator(operator_id, operator_key)
    # Create the token creation transaction
    # In this example, we set up a default empty token create transaction, then set the values
    transaction = (
        TokenCreateTransaction()
        .set_token_name("ASTRAL TOKEN")
        .set_token_symbol("ASTRA")
        .set_decimals(2)
        .set_initial_supply(100000000)  # TokenType.FUNGIBLE_COMMON must have >0 initial supply. Cannot exceed max supply
        .set_treasury_account_id(operator_id) # Also known as treasury account
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(1000000000)
        .set_admin_key(admin_key)
        .set_supply_key(supply_key)
        .set_freeze_key(freeze_key)
        .freeze_with(client) # Freeze the transaction. Returns self so we can sign.

    )
    
    #if supply_key:
    #    transaction.set_supply_key(supply_key)
    #if pause_key:
    #    transaction.set_pause_key(pause_key)
    # Required signature by treasury (operator)
    transaction.sign(operator_key)
    # Sign with adminKey if provided
    if admin_key:
        transaction.sign(admin_key)
    try:
        # Execute the transaction and get the receipt
        receipt = transaction.execute(client)
        if receipt and receipt.token_id:
            print(f"Finite fungible token created with ID: {receipt.token_id}")
        else:
            print("Finite fungible token creation failed: Token ID not returned in receipt.")
            sys.exit(1)
    except Exception as e:
        print(f"Token creation failed: {str(e)}")
        sys.exit(1)

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

#associate_token(recipient_id_new=nbl_id, recipient_key_new=nbl_key)
#transfer_tokens(recipient_id=nbl_id, amount=1000000)