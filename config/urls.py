# Import Django's admin module to enable the Django admin panel.
from django.contrib import admin

# Import path() to define URL patterns.
from django.urls import path, include

# Import JWT views to generate and refresh authentication tokens.
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Import views for generating API documentation.
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


# Define all the URL patterns for the project.
urlpatterns = [

    # Open the Django admin panel at /admin/.
    path('admin/', admin.site.urls),

    # Generate access and refresh tokens using username and password.
    # Endpoint: /api/token/
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

    # Generate a new access token using a valid refresh token.
    # Endpoint: /api/token/refresh/
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Generate the OpenAPI schema for all registered API endpoints.
    # Endpoint: /api/schema/
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Display interactive Swagger documentation for testing APIs.
    # Endpoint: /api/docs/
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Include all URL patterns defined inside the wallet application.
    # All wallet endpoints will start with /wallet/.
    path('api/wallet/', include('wallet.urls')),
]