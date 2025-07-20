"""
URL configuration for credit_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from core.views import home
from django.conf import settings
from django.conf.urls.static import static
# Add drf-yasg imports
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.http import JsonResponse

schema_view = get_schema_view(
   openapi.Info(
      title="Credit System API",
      default_version='v1',
      description="API documentation for the Credit System",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

def api_root_redirect(request):
    return JsonResponse({"detail": "API root moved. Use /api/v1/ for all endpoints."}, status=301)

def api_root(request):
    return JsonResponse({
        "message": "Welcome to the Credit System API. See /api/v1/ for all endpoints.",
        "endpoints": [
            "/api/v1/register/",
            "/api/v1/login/",
            "/api/v1/profile/",
            "/api/v1/admin/users/",
            "/api/v1/admin/loans/<loan_id>/action/",
            "/api/v1/admin/dashboard/",
            "/api/v1/customers/",
            "/api/v1/credit-applications/",
            "/api/v1/transactions/",
            "/api/v1/loans/",
            "/api/v1/register-customer",
            "/api/v1/check-eligibility",
            "/api/v1/create-loan",
            "/api/v1/view-loan/<loan_id>",
            "/api/v1/view-loans/<customer_id>"
        ],
        "docs": {
            "swagger": "/swagger/",
            "redoc": "/redoc/"
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('api/', include('core.urls')),
    # API documentation endpoints
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
