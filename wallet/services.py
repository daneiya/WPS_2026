
# Decimal is used for accurate financial calculations.
from decimal import Decimal

# Django utilities for database transactions and current date/time.
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

# DRF exception used to return validation errors from business logic.
from rest_framework.exceptions import ValidationError

# Import the wallet-related database models.
from .models import Wallet, Transaction, TransferRequest



# CONFIGURATION


# Maximum amount a user can transfer in one day.
# This is an initial example limit. Change it according to
# the daily transfer limit specified by your trainer.
DAILY_TRANSFER_LIMIT = Decimal('10000.00')



# HELPER FUNCTION: GET USER WALLET


def get_user_wallet(user):
    """
    Retrieve the wallet belonging to the authenticated user.

    If the user does not have a wallet, return a validation error.
    """

    try:
        # Find the wallet associated with the logged-in user.
        return Wallet.objects.get(user=user)

    except Wallet.DoesNotExist:
        # Stop the operation if the user has no wallet.
        raise ValidationError(
            {'wallet': 'Wallet does not exist for this user.'}
        )



# SERVICE 1: CREATE WALLET


def create_wallet(user):
    """
    Create a wallet for the given user.

    get_or_create() prevents the creation of duplicate wallets.
    If the user already has a wallet, the existing wallet is returned.
    """

    # Create the wallet with a zero balance if it does not exist.
    wallet, created = Wallet.objects.get_or_create(
        user=user,
        defaults={
            'balance': Decimal('0.00'),
            'is_frozen': False,
        }
    )

    # Return the wallet object.
    return wallet



# HELPER FUNCTION: CHECK WALLET STATUS


def check_wallet_status(wallet):
    """
    Check whether a wallet is frozen.

    Frozen wallets are not allowed to perform money operations.
    """

    if wallet.is_frozen:
        raise ValidationError(
            {'wallet': 'This wallet is frozen. Transactions are not allowed.'}
        )



# SERVICE 2: TOP-UP WALLET


@transaction.atomic
def top_up_wallet(user, amount, description=''):
    """
    Add money to the authenticated user's wallet.

    This is a mock top-up operation. No real bank or payment
    gateway is connected.

    Steps:
    1. Lock the user's wallet.
    2. Check whether the wallet is frozen.
    3. Add the amount to the balance.
    4. Create a TOPUP transaction record.
    """

    # Retrieve and lock the wallet during this database transaction.
    # select_for_update() prevents concurrent operations from
    # modifying the same wallet at the same time.
    try:
        wallet = Wallet.objects.select_for_update().get(user=user)

    except Wallet.DoesNotExist:
        raise ValidationError(
            {'wallet': 'Wallet does not exist for this user.'}
        )

    # Prevent top-ups into a frozen wallet.
    check_wallet_status(wallet)

    # Add the top-up amount to the existing wallet balance.
    wallet.balance += amount

    # Save the updated balance in the database.
    wallet.save(update_fields=['balance', 'updated_at'])

    # Create a transaction record for the top-up.
    transaction_record = Transaction.objects.create(
        wallet=wallet,
        transaction_type=Transaction.TransactionType.TOPUP,
        amount=amount,
        description=description or 'Wallet top-up'
    )

    # Return the updated wallet and transaction details.
    return wallet, transaction_record



# SERVICE 3: WITHDRAW MONEY


@transaction.atomic
def withdraw_money(user, amount, description=''):
    """
    Withdraw money from the authenticated user's wallet.

    Steps:
    1. Lock the wallet.
    2. Check whether the wallet is frozen.
    3. Check whether sufficient balance is available.
    4. Deduct the withdrawal amount.
    5. Create a WITHDRAWAL transaction record.
    """

    # Retrieve and lock the user's wallet.
    try:
        wallet = Wallet.objects.select_for_update().get(user=user)

    except Wallet.DoesNotExist:
        raise ValidationError(
            {'wallet': 'Wallet does not exist for this user.'}
        )

    # Check whether the wallet is frozen.
    check_wallet_status(wallet)

    # Check whether the wallet has enough money.
    if wallet.balance < amount:
        raise ValidationError(
            {'amount': 'Insufficient wallet balance.'}
        )

    # Deduct the withdrawal amount.
    wallet.balance -= amount

    # Save the updated wallet balance.
    wallet.save(update_fields=['balance', 'updated_at'])

    # Create a withdrawal transaction record.
    transaction_record = Transaction.objects.create(
        wallet=wallet,
        transaction_type=Transaction.TransactionType.WITHDRAWAL,
        amount=amount,
        description=description or 'Wallet withdrawal'
    )

    # Return the updated wallet and transaction record.
    return wallet, transaction_record



# HELPER FUNCTION: CHECK DAILY TRANSFER LIMIT


def check_daily_transfer_limit(sender_wallet, amount):
    """
    Check whether the sender has exceeded the daily transfer limit.

    Only completed outgoing transfers are counted.
    """

    # Get the current date using Django's timezone settings.
    today = timezone.localdate()

    # Calculate the total amount already transferred today.
    # TRANSFER_OUT records represent money sent by this wallet.
    daily_total = Transaction.objects.filter(
        wallet=sender_wallet,
        transaction_type=Transaction.TransactionType.TRANSFER_OUT,
        created_at__date=today
    ).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')

    # Check whether the new transfer would exceed the daily limit.
    if daily_total + amount > DAILY_TRANSFER_LIMIT:
        raise ValidationError({
            'amount': (
                f'Daily transfer limit of '
                f'{DAILY_TRANSFER_LIMIT} exceeded.'
            )
        })



# SERVICE 4: TRANSFER MONEY


@transaction.atomic
def transfer_money(sender_user, receiver_wallet_id, amount, description=''):
    """
    Transfer money from the authenticated user's wallet
    to another user's wallet.

    Steps:
    1. Identify the sender and receiver wallets.
    2. Lock both wallets in a consistent order.
    3. Check wallet status.
    4. Check sender balance.
    5. Check the daily transfer limit.
    6. Deduct money from the sender.
    7. Add money to the receiver.
    8. Create a transfer request.
    9. Create debit and credit transaction records.

    All database changes are committed together.
    If an error occurs, the complete operation is rolled back.
    """

    # Find the sender's wallet.
    try:
        sender_wallet_id = Wallet.objects.only('id').get(
            user=sender_user
        ).id

    except Wallet.DoesNotExist:
        raise ValidationError(
            {'wallet': 'Sender wallet does not exist.'}
        )

    # A user cannot transfer money to their own wallet.
    if sender_wallet_id == receiver_wallet_id:
        raise ValidationError(
            {'receiver_wallet_id': 'You cannot transfer money to your own wallet.'}
        )

    # Lock both wallets in ascending primary-key order.
    # Consistent locking order helps reduce deadlock risk when
    # two users transfer money to each other simultaneously.
    locked_wallets = list(
        Wallet.objects.select_for_update()
        .filter(pk__in=[sender_wallet_id, receiver_wallet_id])
        .order_by('pk')
    )

    # Convert the locked wallet list into a dictionary for easy access.
    wallets_by_id = {
        wallet.id: wallet for wallet in locked_wallets
    }

    # Ensure both wallets exist.
    if len(wallets_by_id) != 2:
        raise ValidationError(
            {'receiver_wallet_id': 'Sender or receiver wallet does not exist.'}
        )

    # Get the sender and receiver wallet objects.
    sender_wallet = wallets_by_id[sender_wallet_id]
    receiver_wallet = wallets_by_id[receiver_wallet_id]

    # Neither wallet can participate in a transfer if frozen.
    check_wallet_status(sender_wallet)
    check_wallet_status(receiver_wallet)

    # Check whether the sender has sufficient balance.
    if sender_wallet.balance < amount:
        raise ValidationError(
            {'amount': 'Insufficient wallet balance.'}
        )

    # Check whether the transfer exceeds the daily limit.
    check_daily_transfer_limit(sender_wallet, amount)

    # Deduct the transfer amount from the sender.
    sender_wallet.balance -= amount

    # Add the transfer amount to the receiver.
    receiver_wallet.balance += amount

    # Save both wallet balances.
    sender_wallet.save(update_fields=['balance', 'updated_at'])
    receiver_wallet.save(update_fields=['balance', 'updated_at'])

    # Create a transfer request with PENDING status.
    transfer_request = TransferRequest.objects.create(
        sender_wallet=sender_wallet,
        receiver_wallet=receiver_wallet,
        amount=amount,
        status=TransferRequest.TransferStatus.PENDING
    )

    # Create a debit transaction for the sender.
    # The amount is stored as positive; TRANSFER_OUT identifies
    # that money was deducted from this wallet.
    Transaction.objects.create(
        wallet=sender_wallet,
        transaction_type=Transaction.TransactionType.TRANSFER_OUT,
        amount=amount,
        reference_id=transfer_request.reference_id,
        related_wallet=receiver_wallet,
        description=description or 'Money transferred'
    )

    # Create a credit transaction for the receiver.
    # TRANSFER_IN identifies that money was added to this wallet.
    Transaction.objects.create(
        wallet=receiver_wallet,
        transaction_type=Transaction.TransactionType.TRANSFER_IN,
        amount=amount,
        reference_id=transfer_request.reference_id,
        related_wallet=sender_wallet,
        description=description or 'Money received'
    )

    # Mark the transfer request as completed.
    transfer_request.status = TransferRequest.TransferStatus.COMPLETED

    # Record the date and time of completion.
    transfer_request.completed_at = timezone.now()

    # Save the updated transfer request.
    transfer_request.save(
        update_fields=['status', 'completed_at']
    )

    # Return the completed transfer request.
    return transfer_request
