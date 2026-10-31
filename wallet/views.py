
# Used to generate a consistent hash for duplicate request detection.
import hashlib
import json

# Decimal is used for accurate financial calculations.
from decimal import Decimal

# Django database transaction management.
from django.db import transaction

# Used to validate date query parameters.
from django.utils.dateparse import parse_date

# Django REST Framework API classes and responses.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.pagination import PageNumberPagination

# Import the serializers used to validate and display data.
from .serializers import (
    WalletSerializer,
    TransactionSerializer,
    TopUpSerializer,
    WithdrawalSerializer,
    TransferSerializer,
    TransferRequestSerializer,
)
# Import the registration serializer.
from .serializers import UserRegistrationSerializer

# Import the database models.
from .models import Wallet, Transaction, IdempotencyKey

# Import business logic from the service layer.
from .services import (
    create_wallet,
    get_user_wallet,
    top_up_wallet,
    withdraw_money,
    transfer_money,
)



# PAGINATION


# Controls how many transaction records are returned per page.
class TransactionPagination(PageNumberPagination):

    # Return 10 transactions on each page by default.
    page_size = 10

    # Allow the client to request a different page size.
    page_size_query_param = 'page_size'

    # Do not allow clients to request more than 100 records.
    max_page_size = 100



# API 1: CREATE WALLET
# POST /wallet/create/

class CreateWalletView(APIView):

    # Only authenticated users can create wallets.
    permission_classes = [IsAuthenticated]

    def post(self, request):

        # Create a wallet for the currently logged-in user.
        # get_or_create() in the service prevents duplicate wallets.
        wallet = create_wallet(request.user)

        # Convert the wallet model object into JSON.
        serializer = WalletSerializer(wallet)

        # Return the wallet details.
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )



# API 2: VIEW WALLET
# GET /wallet/


class WalletDetailView(APIView):

    # Only authenticated users can view their wallet.
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Retrieve the wallet belonging to the logged-in user.
        wallet = get_user_wallet(request.user)

        # Convert the wallet object into JSON.
        serializer = WalletSerializer(wallet)

        # Return the wallet information.
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )



# API 3: TOP-UP WALLET
# POST /wallet/topup/


class TopUpView(APIView):

    # Only authenticated users can add money to their wallets.
    permission_classes = [IsAuthenticated]

    def post(self, request):

        # Validate the amount and optional description.
        serializer = TopUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get the validated amount.
        amount = serializer.validated_data['amount']

        # Get the optional description.
        description = serializer.validated_data.get('description', '')

        # Call the service layer to perform the top-up.
        wallet, transaction_record = top_up_wallet(
            request.user,
            amount,
            description
        )

        # Prepare the response containing updated wallet information
        # and the newly created transaction.
        response_data = {
            'message': 'Wallet topped up successfully.',
            'wallet': WalletSerializer(wallet).data,
            'transaction': TransactionSerializer(transaction_record).data,
        }

        # Return a successful response.
        return Response(
            response_data,
            status=status.HTTP_200_OK
        )


# API 4: WITHDRAW MONEY
# POST /wallet/withdraw/


class WithdrawalView(APIView):

    # Only authenticated users can withdraw money.
    permission_classes = [IsAuthenticated]

    def post(self, request):

        # Validate the withdrawal request data.
        serializer = WithdrawalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract the validated amount.
        amount = serializer.validated_data['amount']

        # Extract the optional description.
        description = serializer.validated_data.get('description', '')

        # Call the service layer to process the withdrawal.
        wallet, transaction_record = withdraw_money(
            request.user,
            amount,
            description
        )

        # Prepare the response.
        response_data = {
            'message': 'Withdrawal successful.',
            'wallet': WalletSerializer(wallet).data,
            'transaction': TransactionSerializer(transaction_record).data,
        }

        # Return the updated wallet and transaction information.
        return Response(
            response_data,
            status=status.HTTP_200_OK
        )



# API 5: TRANSFER MONEY
# POST /wallet/transfer/


class TransferView(APIView):

    # Only authenticated users can transfer money.
    permission_classes = [IsAuthenticated]

    def post(self, request):

        # Read the idempotency key from the HTTP request header.
        # This key identifies a particular transfer request.
        idempotency_key = request.headers.get('Idempotency-Key')

        # Reject the request if the header is missing.
        if not idempotency_key:
            return Response(
                {'error': 'Idempotency-Key header is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate the transfer details.
        # The sender wallet is obtained from the logged-in user.
        sender_wallet = get_user_wallet(request.user)

        serializer = TransferSerializer(
            data=request.data,
            context={'sender_wallet': sender_wallet}
        )
        serializer.is_valid(raise_exception=True)

        # Get the validated receiver wallet and amount.
        receiver_wallet = serializer.validated_data['receiver_wallet']
        amount = serializer.validated_data['amount']

        # Get the optional transfer description.
        description = serializer.validated_data.get('description', '')

        # Convert the request body into a consistent JSON string.
        # Sorting keys ensures the same data produces the same hash.
        request_data = json.dumps(
            request.data,
            sort_keys=True,
            default=str
        )

        # Generate a SHA-256 hash of the request data.
        request_hash = hashlib.sha256(
            request_data.encode('utf-8')
        ).hexdigest()

        # Use a database transaction to save the idempotency record
        # and transfer operation together.
        with transaction.atomic():

            # Find an existing key or create a new one.
            # The unique constraint on (user, key) prevents duplicates.
            key_record, created = IdempotencyKey.objects.get_or_create(
                user=request.user,
                key=idempotency_key,
                defaults={
                    'request_hash': request_hash
                }
            )

            # Lock the idempotency record while processing this request.
            key_record = IdempotencyKey.objects.select_for_update().get(
                pk=key_record.pk
            )

            # Do not allow the same key to be reused with different data.
            if key_record.request_hash != request_hash:
                return Response(
                    {
                        'error': (
                            'This Idempotency-Key has already been '
                            'used with different request data.'
                        )
                    },
                    status=status.HTTP_409_CONFLICT
                )

            # If a successful response was already saved,
            # return the original response without transferring again.
            if key_record.response_body is not None:
                return Response(
                    key_record.response_body,
                    status=key_record.response_status
                )

            # Perform the actual money transfer.
            # The service handles balance checks, wallet locking,
            # daily limits and transaction creation.
            transfer_request = transfer_money(
                sender_user=request.user,
                receiver_wallet_id=receiver_wallet.id,
                amount=amount,
                description=description
            )

            # Convert the completed transfer into JSON.
            response_data = {
                'message': 'Money transferred successfully.',
                'transfer': TransferRequestSerializer(
                    transfer_request
                ).data
            }

            # Save the original response against the idempotency key.
            # A repeated request can return this same response.
            key_record.response_status = status.HTTP_201_CREATED
            key_record.response_body = response_data

            key_record.save(
                update_fields=[
                    'response_status',
                    'response_body'
                ]
            )

        # Return the completed transfer response.
        return Response(
            response_data,
            status=status.HTTP_201_CREATED
        )


# API 6: TRANSACTION STATEMENT
# GET /wallet/statement/


class TransactionStatementView(APIView):

    # Only authenticated users can view their transaction history.
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Retrieve the authenticated user's wallet.
        wallet = get_user_wallet(request.user)

        # Retrieve only transactions belonging to this wallet.
        transactions = Transaction.objects.filter(
            wallet=wallet
        ).order_by('-created_at')

        # Read optional start and end dates from the URL.
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')

        # Filter transactions from the specified start date.
        if from_date:

            parsed_from_date = parse_date(from_date)

            if parsed_from_date is None:
                return Response(
                    {'error': 'Invalid from date. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            transactions = transactions.filter(
                created_at__date__gte=parsed_from_date
            )

        # Filter transactions up to the specified end date.
        if to_date:

            parsed_to_date = parse_date(to_date)

            if parsed_to_date is None:
                return Response(
                    {'error': 'Invalid to date. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            transactions = transactions.filter(
                created_at__date__lte=parsed_to_date
            )

        # Reject a date range where the start is after the end.
        if from_date and to_date:
            if parsed_from_date > parsed_to_date:
                return Response(
                    {'error': 'From date cannot be after to date.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Create a paginator for the filtered transaction records.
        paginator = TransactionPagination()

        # Get the transactions for the requested page.
        page = paginator.paginate_queryset(
            transactions,
            request
        )

        # Convert the page of transaction objects into JSON.
        serializer = TransactionSerializer(page, many=True)

        # Return paginated transaction results.
        return paginator.get_paginated_response(serializer.data)


# API 7: WALLET RECONCILIATION
# GET /wallet/reconcile/


class WalletReconciliationView(APIView):

    # Only authenticated users can reconcile their own wallet.
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # Retrieve the authenticated user's wallet.
        wallet = get_user_wallet(request.user)

        # Start the expected balance at zero.
        expected_balance = Decimal('0.00')

        # Retrieve all ledger entries belonging to this wallet.
        transactions = Transaction.objects.filter(
            wallet=wallet
        )

        # Calculate the balance from the transaction history.
        for record in transactions:

            # Money entering the wallet increases the expected balance.
            if record.transaction_type in [
                Transaction.TransactionType.TOPUP,
                Transaction.TransactionType.TRANSFER_IN
            ]:
                expected_balance += record.amount

            # Money leaving the wallet decreases the expected balance.
            elif record.transaction_type in [
                Transaction.TransactionType.TRANSFER_OUT,
                Transaction.TransactionType.WITHDRAWAL
            ]:
                expected_balance -= record.amount

        # Compare the calculated balance with the stored wallet balance.
        is_reconciled = expected_balance == wallet.balance

        # Return both balances and the reconciliation result.
        return Response(
            {
                'wallet_id': wallet.id,
                'stored_balance': wallet.balance,
                'calculated_balance': expected_balance,
                'is_reconciled': is_reconciled,
                'message': (
                    'Wallet balance is correct.'
                    if is_reconciled
                    else 'Wallet balance does not match transaction history.'
                )
            },
            status=status.HTTP_200_OK
        )


# API 8: FREEZE OR UNFREEZE WALLET
# PATCH /wallet/freeze/<wallet_id>/


class WalletFreezeView(APIView):

    # Only staff/admin users can freeze or unfreeze wallets.
    permission_classes = [IsAdminUser]

    def patch(self, request, wallet_id):

        # Read the new frozen status from the request body.
        is_frozen = request.data.get('is_frozen')

        # Ensure that the client provides a Boolean value.
        if not isinstance(is_frozen, bool):
            return Response(
                {
                    'error': (
                        'is_frozen must be true or false.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Find the wallet using its primary key.
        try:
            wallet = Wallet.objects.get(pk=wallet_id)

        except Wallet.DoesNotExist:
            return Response(
                {'error': 'Wallet not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Update the wallet's frozen status.
        wallet.is_frozen = is_frozen

        # Save the updated status and modification time.
        wallet.save(
            update_fields=['is_frozen', 'updated_at']
        )

        # Return the updated wallet details.
        return Response(
            {
                'message': (
                    'Wallet frozen successfully.'
                    if is_frozen
                    else 'Wallet unfrozen successfully.'
                ),
                'wallet': WalletSerializer(wallet).data
            },
            status=status.HTTP_200_OK
        )



# API view for registering a new user.
class UserRegistrationView(APIView):

    # Allow anyone to register without logging in.
    permission_classes = []

    def post(self, request):

        # Validate the incoming registration data.
        serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():

            # Create the new user.
            user = serializer.save()

            # Return the newly created user's basic details.
            return Response(
                {
                    "message": "User registered successfully.",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email
                    }
                },
                status=status.HTTP_201_CREATED
            )

        # Return validation errors if the data is invalid.
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )