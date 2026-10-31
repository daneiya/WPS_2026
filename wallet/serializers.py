
# Import serializers from Django REST Framework.
from rest_framework import serializers

# Import the wallet models that we created in models.py.
from .models import Wallet, Transaction, TransferRequest



# SERIALIZER 1: WALLET SERIALIZER


# Converts Wallet model objects into JSON responses.
# Users can view their wallet details but cannot directly
# change the balance or frozen status through this serializer.
class WalletSerializer(serializers.ModelSerializer):

    class Meta:
        # Specifies which database model this serializer uses.
        model = Wallet

        # Fields that will be included in the API response.
        fields = [
            'id',
            'user',
            'balance',
            'is_frozen',
            'created_at',
            'updated_at',
        ]

        # Prevent users from modifying these fields through the API.
        read_only_fields = [
            'id',
            'user',
            'balance',
            'is_frozen',
            'created_at',
            'updated_at',
        ]



# SERIALIZER 2: TRANSACTION SERIALIZER


# Converts Transaction model objects into JSON responses.
# Transaction records are created by the backend, not directly
# by users through an API request.
class TransactionSerializer(serializers.ModelSerializer):

    class Meta:
        # Specifies the Transaction model.
        model = Transaction

        # Fields returned when displaying transaction details.
        fields = [
            'id',
            'wallet',
            'transaction_type',
            'amount',
            'reference_id',
            'related_wallet',
            'description',
            'created_at',
        ]

        # All transaction fields are read-only.
        # This prevents clients from creating or changing ledger entries.
        read_only_fields = fields



# SERIALIZER 3: TOP-UP SERIALIZER


# Validates the amount submitted when a user adds money
# to their wallet.
class TopUpSerializer(serializers.Serializer):

    # Accepts a decimal amount with a maximum of 12 digits
    # and 2 digits after the decimal point.
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01
    )

    # Optional description for the top-up request.
    description = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True
    )



# SERIALIZER 4: WITHDRAWAL SERIALIZER

# Validates the amount submitted when a user withdraws
# money from their wallet.
class WithdrawalSerializer(serializers.Serializer):

    # The withdrawal amount must be greater than zero.
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01
    )

    # Optional explanation for the withdrawal.
    description = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True
    )



# SERIALIZER 5: TRANSFER SERIALIZER


# Validates the details when a user transfers money
# from their wallet to another user's wallet.
class TransferSerializer(serializers.Serializer):

    # The receiver's wallet ID.
    # The receiver wallet must already exist in the database.
    receiver_wallet_id = serializers.PrimaryKeyRelatedField(
        queryset=Wallet.objects.all(),
        source='receiver_wallet'
    )

    # Amount to be transferred.
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01
    )

    # Optional description for the transfer.
    description = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True
    )

    # Check that the sender and receiver are different wallets.
    # The sender wallet will be obtained from the authenticated user
    # in the view/service layer, not from the request body.
    def validate(self, attrs):

        # Get the receiver wallet from the validated data.
        receiver_wallet = attrs['receiver_wallet']

        # If the authenticated sender wallet was provided in the context,
        # ensure the user is not transferring money to their own wallet.
        sender_wallet = self.context.get('sender_wallet')

        if sender_wallet and sender_wallet.pk == receiver_wallet.pk:
            raise serializers.ValidationError(
                'You cannot transfer money to your own wallet.'
            )

        return attrs



# SERIALIZER 6: TRANSFER REQUEST SERIALIZER


# Converts TransferRequest model objects into JSON responses.
# Used to display transfer details and their current status.
class TransferRequestSerializer(serializers.ModelSerializer):

    class Meta:
        # Specifies the TransferRequest model.
        model = TransferRequest

        # Fields returned in transfer details.
        fields = [
            'id',
            'sender_wallet',
            'receiver_wallet',
            'amount',
            'status',
            'reference_id',
            'created_at',
            'completed_at',
        ]

        # Transfer details are generated and managed by the backend.
        read_only_fields = fields
# Import Django's configured User model.
from django.contrib.auth import get_user_model

# Get the User model used by this project.
User = get_user_model()


# Serializer for registering a new user.
class UserRegistrationSerializer(serializers.ModelSerializer):

    # Accept a password but never return it in API responses.
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    class Meta:
        model = User

        # Fields required to create a new user.
        fields = ['id', 'username', 'email', 'password']

    # Create the user securely using Django's password hashing.
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
