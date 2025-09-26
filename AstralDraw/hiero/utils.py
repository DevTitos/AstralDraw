from hiero_sdk_python import (
    Client,
    Network,
    AccountId,
    PrivateKey,
    AccountCreateTransaction,
    ResponseCode,
    TokenCreateTransaction,
    Network,
    TokenType,
    SupplyType,
    AccountCreateTransaction,
)

import os, sys
from dotenv import load_dotenv

load_dotenv()

operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))

def create_new_account(name):
    network = Network(network='testnet')
    client = Client(network)
    client.set_operator(operator_id, operator_key)

    new_account_private_key = PrivateKey.generate("ed25519")
    new_account_public_key = new_account_private_key.public_key()

    transaction = (
        AccountCreateTransaction()
        .set_key(new_account_public_key)
        .set_initial_balance(1000000000)  # 1 HBAR in tinybars
        .set_account_memo(f"{name}'s account")
        .freeze_with(client)
    )

    transaction.sign(operator_key)

    try:
        receipt = transaction.execute(client)
        print(f"Transaction status: {receipt.status}")

        if receipt.status != ResponseCode.SUCCESS:
            status_message = ResponseCode(receipt.status).name
            print(f"Transaction failed with status: {status_message}")
            return False
            #raise Exception(f"Transaction failed with status: {status_message}")

        new_account_id = receipt.account_id
        if new_account_id is not None:
            print(f"Account creation successful. New Account ID: {new_account_id}")
            print(f"New Account Private Key: {new_account_private_key.to_string()}")
            print(f"New Account Public Key: {new_account_public_key.to_string()}")
            return new_account_id, new_account_private_key, new_account_public_key
        else:
            print("AccountID not found in receipt. Account may not have been created.")
            return False
            #raise Exception("AccountID not found in receipt. Account may not have been created.")

    except Exception as e:
        print(f"Account creation failed: {str(e)}")
        #sys.exit(1)
        return None