import logging
from hiero_sdk_python import Client, AccountId, PrivateKey, PrngTransaction
from django.conf import settings
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class AstralDrawRandomizer:
    """
    Handles generation of 6 provably fair random numbers (0-9) using Hedera's PRNG transaction.
    """

    def __init__(self):
        try:
            self.client = Client.for_testnet()
            self.client.set_operator(
                AccountId.fromString(settings.HEDERA_OPERATOR_ID),
                PrivateKey.fromString(settings.HEDERA_OPERATOR_KEY)
            )
        except Exception as e:
            logger.error(f"[AstralDrawRandomizer] Failed to initialize Hedera client: {e}")
            raise ValidationError("Could not initialize Hedera client. Check credentials.")

    def get_six_numbers(self):
        """
        Generates 6 random numbers between 0-9 inclusive using Hedera PRNG.
        Returns array of numbers + proof (transaction ID).
        """
        numbers = []

        try:
            for _ in range(6):
                prng_tx = (
                    PrngTransaction()
                    .setRange(10)  # range 0-9
                    .freezeWith(self.client)
                )

                tx_response = prng_tx.execute(self.client)
                receipt = tx_response.getReceipt(self.client)
                random_number = receipt.prng_number

                if random_number is None:
                    raise ValidationError("No random number returned from Hedera PRNG.")

                numbers.append(random_number)

            return {
                "numbers": numbers,
                "transaction_ids": [str(n.transactionId) for n in tx_response.children],
                "last_transaction_id": str(tx_response.transactionId)
            }

        except Exception as e:
            logger.error(f"[AstralDrawRandomizer] PRNG generation failed: {e}")
            raise ValidationError("Could not generate random numbers from Hedera.")
