from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerViewSet, CreditApplicationViewSet, TransactionViewSet, LoanViewSet,
    RegisterCustomerAPIView, CheckEligibilityAPIView, CreateLoanAPIView, ViewLoanAPIView, ViewLoansByCustomerAPIView,
    UserRegistrationView, UserLoginView, UserProfileView, AdminUserListView, AdminLoanApprovalView, AdminDashboardView,
    register_ui
)
from django.http import JsonResponse

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'credit-applications', CreditApplicationViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'loans', LoanViewSet)

def api_v1_root(request):
    return JsonResponse({
        "message": "Welcome to the Credit System API v1.",
        "endpoints": [
            "/api/v1/register/",                # User registration
            "/api/v1/login/",                   # User login
            "/api/v1/profile/",                 # User profile
            "/api/v1/customers/",               # Customer CRUD
            "/api/v1/credit-applications/",     # Credit application CRUD
            "/api/v1/transactions/",            # Transaction CRUD
            "/api/v1/loans/",                   # Loan CRUD
            "/api/v1/register-customer",        # Register customer (custom)
            "/api/v1/check-eligibility",        # Check loan eligibility
            "/api/v1/create-loan",              # Create loan (custom)
            "/api/v1/view-loan/<loan_id>",      # View single loan
            "/api/v1/view-loans/<customer_id>", # View loans by customer
            "/api/v1/admin/users/",             # Admin: list users
            "/api/v1/admin/loans/<loan_id>/action/", # Admin: approve/reject loan
            "/api/v1/admin/dashboard/",         # Admin: dashboard
        ]
    })

urlpatterns = [
    path('register-ui/', register_ui, name='register-ui'),
    path('v1/', api_v1_root),
    path('v1/register/', UserRegistrationView.as_view(), name='user-register'),
    path('v1/login/', UserLoginView.as_view(), name='user-login'),
    path('v1/profile/', UserProfileView.as_view(), name='user-profile'),
    path('v1/admin/users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('v1/admin/loans/<int:loan_id>/action/', AdminLoanApprovalView.as_view(), name='admin-loan-action'),
    path('v1/admin/dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('v1/', include(router.urls)),
    path('v1/register-customer', RegisterCustomerAPIView.as_view(), name='register-customer'),
    path('v1/check-eligibility', CheckEligibilityAPIView.as_view(), name='check-eligibility'),
    path('v1/create-loan', CreateLoanAPIView.as_view(), name='create-loan'),
    path('v1/view-loan/<int:loan_id>', ViewLoanAPIView.as_view(), name='view-loan'),
    path('v1/view-loans/<int:customer_id>', ViewLoansByCustomerAPIView.as_view(), name='view-loans-by-customer'),
] 