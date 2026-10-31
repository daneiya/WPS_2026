
# Import Django's path function to define URL patterns.
from django.urls import path

# Import the API views from views.py.
from .views import (
    CreateWalletView,
    WalletDetailView,
    TopUpView,
    WithdrawalView,
    TransferView,
    TransactionStatementView,
    WalletReconciliationView,
    WalletFreezeView,
    UserRegistrationView,
)


# Define all URL patterns for the wallet application.
urlpatterns = [

    # Create a wallet for the logged-in user.
    path(
        'create/',CreateWalletView.as_view(),name='create-wallet'),

    # View the logged-in user's wallet.
    path('',WalletDetailView.as_view(),name='wallet-detail'),

    # Add money to the wallet.
    path('topup/',TopUpView.as_view(),name='wallet-topup'),

    # Withdraw money from the wallet.
    path('withdraw/',WithdrawalView.as_view(),name='wallet-withdraw'    ),

    # Transfer money to another wallet.
    path('transfer/',TransferView.as_view(),name='wallet-transfer'),

    # View transaction history with date filtering and pagination.
    path('statement/',TransactionStatementView.as_view(),name='wallet-statement'),

    # Compare wallet balance with the transaction ledger.
    path('reconcile/',WalletReconciliationView.as_view(),name='wallet-reconcile'),

    # Admin endpoint to freeze or unfreeze a wallet.
    path('freeze/<int:wallet_id>/',WalletFreezeView.as_view(),name='wallet-freeze'),
    
    # Register a new user
    path('register/', UserRegistrationView.as_view(), name='user-register'),
]
