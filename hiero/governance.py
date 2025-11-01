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
from hiero_sdk_python import (
    Client,
    Network,
    AccountId,
    PrivateKey,
    TopicId,
    TopicCreateTransaction,
    TopicMessageSubmitTransaction,
)

import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))



def submit_message(message, topic):
    network = Network(network='testnet')
    client = Client(network)
    topic_id = TopicId.from_string(topic)

    client.set_operator(operator_id, operator_key)

    transaction = (
        TopicMessageSubmitTransaction(topic_id=topic_id, message=message)
        .freeze_with(client)
        .sign(operator_key)
    )

    try:
        receipt = transaction.execute(client)
        print(receipt)
        print(f"Message submitted to topic {topic_id}: {message}")
        return {
            'status':'success',
            'topic':topic_id
        }
    except Exception as e:
        print(f"Message submission failed: {str(e)}")
        return {
            'status':'failed',
            'message':f"Vote submission failed: {str(e)}"
        }


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
