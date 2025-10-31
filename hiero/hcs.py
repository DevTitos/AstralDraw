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

# Astral Draw
# The Launchpad
# The Cosmic Clock
# The Nebula Split
# The Galactic Forum
def create_topic():
    network = Network(network='testnet')
    client = Client(network)

    client.set_operator(operator_id, operator_key)

    transaction = (
        TopicCreateTransaction(
            memo="The Galactic Forum",
            admin_key=operator_key.public_key()
        )
        .freeze_with(client)
        .sign(operator_key)
    )

    try:
        receipt = transaction.execute(client)
        if receipt and receipt.topicId:
            print(f"Topic created with ID: {receipt.topic_id}")
            return receipt.topicId
        else:
            print("Topic creation failed: Topic ID not returned in receipt.")
    except Exception as e:
        print(f"Topic creation failed: {str(e)}")

def submit_message(message):
    network = Network(network='testnet')
    client = Client(network)
    topic_id = TopicId.from_string(os.getenv('TOPIC_ID'))

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
