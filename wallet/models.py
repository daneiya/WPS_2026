
# Used to generate unique reference IDs for transactions and transfers.
import uuid

# Provides access to Django's configured User model.
from django.conf import settings

# Provides Django's database model classes and field types.
from django.db import models

# Q is used to define database conditions and constraints.
from django.db.models import Q



# MODEL 1: WALLET


# Wallet stores the balance and status of each user's wallet.
class Wallet(models.Model):

    # One user can have only one wallet.
    # OneToOneField creates a one-to-one relationship with the User model.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # Delete the wallet if its user is deleted.
        related_name='wallet'      # Access wallet using user.wallet.
    )

    # Stores the wallet balance.
    # max_digits=12 allows up to 12 total digits.
    # decimal_places=2 allows two digits after the decimal point.
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

    # Indicates whether the wallet is frozen.
    # A frozen wallet should not be allowed to perform transactions.
    is_frozen = models.BooleanField(default=False)

    # Automatically stores the date and time when the wallet is created.
    created_at = models.DateTimeField(auto_now_add=True)

    # Automatically updates the date and time whenever the wallet is modified.
    updated_at = models.DateTimeField(auto_now=True)

    # Returns a readable wallet name in Django Admin and other displays.
    def __str__(self):
        return f"Wallet - {self.user.username}"



# MODEL 2: TRANSACTION


# Transaction stores every money movement in a wallet.
# Examples: top-up, money received, money transferred and withdrawal.
class Transaction(models.Model):

    # Defines the types of transactions allowed in the system.
    # TextChoices provides predefined choices for the transaction_type field.
    class TransactionType(models.TextChoices):
        TOPUP = 'TOPUP', 'Top Up'
        TRANSFER_IN = 'TRANSFER_IN', 'Transfer In'
        TRANSFER_OUT = 'TRANSFER_OUT', 'Transfer Out'
        WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'

    # Connects each transaction to the wallet involved.
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,  # Prevent deleting a wallet with transactions.
        related_name='transactions'  # Access transactions using wallet.transactions.
    )

    # Stores the type of transaction.
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices
    )

    # Stores the transaction amount.
    # DecimalField is used for accurate financial values.
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    # Generates a unique UUID reference for identifying a transaction.
    # db_index=True helps speed up searches using this field.
    reference_id = models.UUIDField(
        default=uuid.uuid4,
        db_index=True
    )

    # For transfers, this identifies the other wallet involved.
    # It is optional for top-ups and withdrawals.
    related_wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='related_transactions'
    )

    # Stores an optional description of the transaction.
    description = models.CharField(
        max_length=125,
        blank=True
    )

    # Automatically records when the transaction is created.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        # Displays the newest transactions first by default.
        ordering = ['-created_at']

        # Creates database indexes to make common searches faster.
        indexes = [
            models.Index(fields=['wallet', 'created_at']),
            models.Index(fields=['wallet', 'transaction_type']),
        ]

        # Database-level validation: transaction amount must be greater than zero.
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name='transaction_amount_positive'
            ),
        ]

    # Returns a readable transaction description.
    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"


# MODEL 3: TRANSFER REQUEST


# TransferRequest stores details about money transfers
# from one user's wallet to another user's wallet.
class TransferRequest(models.Model):

    # Defines the possible statuses of a transfer.
    class TransferStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    # Identifies the wallet sending the money.
    sender_wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name='sent_transfers'
    )

    # Identifies the wallet receiving the money.
    receiver_wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name='received_transfers'
    )

    # Stores the amount that the sender wants to transfer.
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    # Stores the current status of the transfer.
    # A new transfer starts with PENDING status.
    status = models.CharField(
        max_length=10,
        choices=TransferStatus.choices,
        default=TransferStatus.PENDING
    )

    # Generates a unique reference ID for each transfer request.
    reference_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    # Stores when the transfer request was created.
    created_at = models.DateTimeField(auto_now_add=True)

    # Stores when the transfer was successfully completed.
    # It remains empty until the transfer is completed.
    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:

        # Database-level validation for transfer requests.
        constraints = [

            # Transfer amount must be greater than zero.
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name='transfer_amount_positive'
            ),

            # Sender and receiver must be different wallets.
            models.CheckConstraint(
                condition=~Q(sender_wallet=models.F('receiver_wallet')),
                name='different_transfer_wallets'
            ),
        ]

    # Returns the transfer reference and its current status.
    def __str__(self):
        return f"Transfer {self.reference_id} - {self.status}"


# MODEL 4: IDEMPOTENCY KEY


# IdempotencyKey prevents duplicate processing of the same API request.
# Example: If a user clicks the Transfer button twice,
# the same request should not transfer money twice.
class IdempotencyKey(models.Model):

    # Connects the idempotency key to the user who made the request.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='idempotency_keys'
    )

    # Stores the unique key received from the Idempotency-Key HTTP header.
    key = models.CharField(max_length=255)

    # Stores a hash of the original request data.
    # This helps identify if the same key is reused with different data.
    request_hash = models.CharField(max_length=64)

    # Stores the HTTP status code of the original response.
    # It remains empty until a response is saved.
    response_status = models.PositiveSmallIntegerField(
        null=True,
        blank=True
    )

    # Stores the original API response as JSON.
    # It can be returned when the same request is received again.
    response_body = models.JSONField(
        null=True,
        blank=True
    )

    # Automatically records when the idempotency key is created.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        # The same user cannot use the same idempotency key more than once.
        # Different users can use the same key.
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'key'],
                name='unique_idempotency_key_per_user'
            )
        ]

    # Returns the username and idempotency key for readable display.
    def __str__(self):
        return f"{self.user.username} - {self.key}"
