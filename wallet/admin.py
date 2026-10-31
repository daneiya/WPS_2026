
# Import Django's admin module to register and customize models.
from django.contrib import admin

# Import all four models from the current wallet application.
from .models import Wallet, Transaction, TransferRequest, IdempotencyKey



# WALLET ADMIN


# Customize how wallet records appear in Django Admin.
@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):

    # Fields displayed in the wallet list page.
    list_display = (
        'id',
        'user',
        'balance',
        'is_frozen',
        'created_at',
    )

    # Allow filtering wallets based on their frozen status.
    list_filter = ('is_frozen',)

    # Allow searching wallets using the username.
    search_fields = ('user__username',)

    # Make these fields read-only in the admin form.
    readonly_fields = ('created_at', 'updated_at')


# TRANSACTION ADMIN


# Customize how transaction records appear in Django Admin.
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):

    # Fields displayed in the transaction list page.
    list_display = (
        'id',
        'wallet',
        'transaction_type',
        'amount',
        'reference_id',
        'created_at',
    )

    # Allow filtering transactions by their type and date.
    list_filter = ('transaction_type', 'created_at')

    # Allow searching using transaction reference and wallet username.
    search_fields = (
        'reference_id',
        'wallet__user__username',
    )

    # Transaction records should not be manually modified.
    readonly_fields = (
        'wallet',
        'transaction_type',
        'amount',
        'reference_id',
        'related_wallet',
        'description',
        'created_at',
    )



# TRANSFER REQUEST ADMIN


# Customize how transfer requests appear in Django Admin.
@admin.register(TransferRequest)
class TransferRequestAdmin(admin.ModelAdmin):

    # Fields displayed in the transfer request list page.
    list_display = (
        'id',
        'sender_wallet',
        'receiver_wallet',
        'amount',
        'status',
        'reference_id',
        'created_at',
    )

    # Filter transfer requests based on their status and creation date.
    list_filter = ('status', 'created_at')

    # Allow searching using the transfer reference.
    search_fields = (
        'reference_id',
        'sender_wallet__user__username',
        'receiver_wallet__user__username',
    )

    # Prevent manual editing of financial transfer records.
    readonly_fields = (
        'sender_wallet',
        'receiver_wallet',
        'amount',
        'status',
        'reference_id',
        'created_at',
        'completed_at',
    )


# IDEMPOTENCY KEY ADMIN


# Customize how idempotency records appear in Django Admin.
@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(admin.ModelAdmin):

    # Fields displayed in the idempotency key list page.
    list_display = (
        'id',
        'user',
        'key',
        'response_status',
        'created_at',
    )

    # Allow filtering based on creation date.
    list_filter = ('created_at',)

    # Allow searching using username and idempotency key.
    search_fields = ('user__username', 'key')

    # These records should not be manually modified.
    readonly_fields = (
        'user',
        'key',
        'request_hash',
        'response_status',
        'response_body',
        'created_at',
    )
