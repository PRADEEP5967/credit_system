from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Customer, CreditApplication, Transaction, Loan
from .serializers import CustomerSerializer, CreditApplicationSerializer, TransactionSerializer, LoanSerializer, CustomerRegistrationSerializer, LoanEligibilitySerializer, CreateLoanSerializer, UserRegistrationSerializer, UserProfileSerializer
from django.utils import timezone
from datetime import datetime
import math
from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAdminUser
import logging
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import requests

logger = logging.getLogger('api')

# Create your views here.

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['age', 'monthly_salary', 'approved_limit']
    search_fields = ['first_name', 'last_name', 'phone_number']
    ordering_fields = ['age', 'monthly_salary', 'approved_limit']

class CreditApplicationViewSet(viewsets.ModelViewSet):
    queryset = CreditApplication.objects.all()
    serializer_class = CreditApplicationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'amount']
    search_fields = ['status']
    ordering_fields = ['amount', 'submitted_at', 'reviewed_at']

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['amount']
    search_fields = ['amount']
    ordering_fields = ['amount']

class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['loan_amount', 'interest_rate', 'tenure']
    search_fields = ['loan_amount', 'interest_rate']
    ordering_fields = ['loan_amount', 'interest_rate', 'tenure']

class RegisterCustomerAPIView(APIView):
    def post(self, request):
        serializer = CustomerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            customer = serializer.save()
            response_data = {
                'customer_id': customer.id,
                'name': f"{customer.first_name} {customer.last_name}",
                'age': customer.age,
                'monthly_income': int(customer.monthly_salary),
                'approved_limit': int(customer.approved_limit),
                'phone_number': customer.phone_number,
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- Modern Credit Score Logic Helpers ---
CREDIT_SCORE_WEIGHTS = {
    'on_time': 40,
    'num_loans': 15,
    'current_year': 15,
    'volume': 20,
}
APPROVAL_THRESHOLDS = [
    (50, 0),    # >50, any interest rate
    (30, 12),   # 30-50, >12%
    (10, 16),   # 10-30, >16%
    (0, None),  # <10, not approved
]

def calculate_credit_score(loans, approved_limit):
    """Calculate credit score based on loan history."""
    now = timezone.now().date()
    current_year = now.year
    # 1. Past loans paid on time
    total_emis = sum(l.tenure for l in loans)
    total_paid_on_time = sum(l.emis_paid_on_time for l in loans)
    on_time_ratio = (total_paid_on_time / total_emis) if total_emis else 1
    score_on_time = on_time_ratio * CREDIT_SCORE_WEIGHTS['on_time']
    # 2. Number of loans taken in past
    score_num_loans = min(len(loans), 10) / 10 * CREDIT_SCORE_WEIGHTS['num_loans']
    # 3. Loan activity in current year
    score_current_year = min(len([l for l in loans if l.start_date.year == current_year]), 5) / 5 * CREDIT_SCORE_WEIGHTS['current_year']
    # 4. Loan approved volume
    total_loan_volume = sum(l.loan_amount for l in loans)
    score_volume = min(total_loan_volume / approved_limit, 1) * CREDIT_SCORE_WEIGHTS['volume'] if approved_limit else 0
    return score_on_time + score_num_loans + score_current_year + score_volume

def get_approval_and_rate(credit_score, interest_rate):
    """Determine approval and corrected interest rate based on score."""
    for threshold, min_rate in APPROVAL_THRESHOLDS:
        if credit_score > threshold:
            if min_rate is None:
                return False, 16  # Not approved, lowest slab
            if min_rate == 0 or interest_rate > min_rate:
                return True, interest_rate if interest_rate >= min_rate else min_rate
            else:
                return False, min_rate
    return False, 16

def calculate_emi(principal, rate, tenure):
    """Calculate EMI using compound interest formula."""
    r = (rate / 12) / 100
    n = tenure
    if r > 0:
        emi = principal * r * math.pow(1 + r, n) / (math.pow(1 + r, n) - 1)
    else:
        emi = principal / n
    return round(emi, 2)

class CheckEligibilityAPIView(APIView):
    def post(self, request):
        data = request.data
        customer_id = data.get('customer_id')
        loan_amount = data.get('loan_amount')
        interest_rate = data.get('interest_rate')
        tenure = data.get('tenure')
        # Fetch customer and loans
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
        loans = Loan.objects.filter(customer=customer)
        now = timezone.now().date()
        # Check if current debt exceeds approved limit
        current_debt = sum(l.loan_amount for l in loans if l.end_date >= now)
        if current_debt > (customer.approved_limit or 0):
            credit_score = 0
        else:
            credit_score = calculate_credit_score(loans, customer.approved_limit or 0)
        # Check if EMIs exceed 50% of salary
        current_emis = sum(l.monthly_payment for l in loans if l.end_date >= now)
        new_emi = calculate_emi(loan_amount, interest_rate, tenure)
        if customer.monthly_salary and (current_emis + new_emi) > 0.5 * customer.monthly_salary:
            return Response({
                'customer_id': customer_id,
                'approval': False,
                'interest_rate': interest_rate,
                'corrected_interest_rate': interest_rate,
                'tenure': tenure,
                'monthly_installment': new_emi,
                'reason': 'EMIs exceed 50% of monthly salary'
            }, status=status.HTTP_200_OK)
        # Approval logic
        approval, corrected_interest_rate = get_approval_and_rate(credit_score, interest_rate)
        corrected_emi = calculate_emi(loan_amount, corrected_interest_rate, tenure)
        response = {
            'customer_id': customer_id,
            'approval': approval,
            'interest_rate': interest_rate,
            'corrected_interest_rate': corrected_interest_rate,
            'tenure': tenure,
            'monthly_installment': corrected_emi,
        }
        if not approval:
            response['reason'] = 'Loan not approved by policy'
        return Response(response, status=status.HTTP_200_OK)

class CreateLoanAPIView(APIView):
    def post(self, request):
        serializer = CreateLoanSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        customer_id = data['customer_id']
        loan_amount = data['loan_amount']
        interest_rate = data['interest_rate']
        tenure = data['tenure']
        # Fetch customer
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
        # Check eligibility (reuse logic from CheckEligibilityAPIView)
        eligibility_request = {
            'customer_id': customer_id,
            'loan_amount': loan_amount,
            'interest_rate': interest_rate,
            'tenure': tenure,
        }
        eligibility_view = CheckEligibilityAPIView()
        eligibility_response = eligibility_view.post(request._request)
        eligibility_data = eligibility_response.data
        if not eligibility_data.get('approval', False):
            return Response({
                'loan_id': None,
                'customer_id': customer_id,
                'loan_approved': False,
                'message': eligibility_data.get('reason', 'Loan not approved'),
                'monthly_installment': eligibility_data.get('monthly_installment', 0),
            }, status=status.HTTP_200_OK)
        # Create loan
        from datetime import date, timedelta
        start_date = date.today()
        end_date = start_date + timedelta(days=30*tenure)
        loan = Loan.objects.create(
            customer=customer,
            loan_id=Loan.objects.count() + 1,
            loan_amount=loan_amount,
            tenure=tenure,
            interest_rate=eligibility_data['corrected_interest_rate'],
            monthly_payment=eligibility_data['monthly_installment'],
            emis_paid_on_time=0,
            start_date=start_date,
            end_date=end_date,
        )
        # Update customer current_debt
        customer.current_debt = (customer.current_debt or 0) + loan_amount
        customer.save()
        return Response({
            'loan_id': loan.loan_id,
            'customer_id': customer_id,
            'loan_approved': True,
            'message': 'Loan approved',
            'monthly_installment': eligibility_data['monthly_installment'],
        }, status=status.HTTP_201_CREATED)

class ViewLoanAPIView(APIView):
    def get(self, request, loan_id):
        try:
            loan = Loan.objects.get(loan_id=loan_id)
        except Loan.DoesNotExist:
            return Response({'error': 'Loan not found'}, status=status.HTTP_404_NOT_FOUND)
        customer = loan.customer
        response = {
            'loan_id': loan.loan_id,
            'customer': {
                'id': customer.customer_id,
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'phone_number': customer.phone_number,
                'age': customer.age,
            },
            'loan_amount': float(loan.loan_amount),
            'interest_rate': float(loan.interest_rate),
            'monthly_installment': float(loan.monthly_payment),
            'tenure': loan.tenure,
        }
        return Response(response, status=status.HTTP_200_OK)

class ViewLoansByCustomerAPIView(APIView):
    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
        loans = Loan.objects.filter(customer=customer)
        now = timezone.now().date()
        loan_list = []
        for loan in loans:
            # Calculate repayments_left
            total_emis = loan.tenure
            # Assume EMIs paid on time is up to today
            months_passed = max(0, (now.year - loan.start_date.year) * 12 + (now.month - loan.start_date.month))
            repayments_left = max(0, total_emis - months_passed)
            loan_list.append({
                'loan_id': loan.loan_id,
                'loan_amount': float(loan.loan_amount),
                'interest_rate': float(loan.interest_rate),
                'monthly_installment': float(loan.monthly_payment),
                'repayments_left': repayments_left,
            })
        return Response(loan_list, status=status.HTTP_200_OK)

class UserRegistrationView(APIView):
    permission_classes = []
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])
        return Response({'token': token.key})

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

class AdminUserListView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        users = User.objects.all()
        data = UserProfileSerializer(users, many=True).data
        return Response(data)

class AdminLoanApprovalView(APIView):
    permission_classes = [IsAdminUser]
    def post(self, request, loan_id):
        action = request.data.get('action')
        try:
            loan = Loan.objects.get(loan_id=loan_id)
        except Loan.DoesNotExist:
            logger.warning(f'Admin {request.user} tried to access non-existent loan {loan_id}')
            return Response({'error': 'Loan not found'}, status=status.HTTP_404_NOT_FOUND)
        if action == 'approve':
            loan.status = 'approved'
            loan.save()
            logger.info(f'Loan {loan_id} approved by admin {request.user}')
            return Response({'message': 'Loan approved'}, status=status.HTTP_200_OK)
        elif action == 'reject':
            loan.status = 'rejected'
            loan.save()
            logger.info(f'Loan {loan_id} rejected by admin {request.user}')
            return Response({'message': 'Loan rejected'}, status=status.HTTP_200_OK)
        else:
            logger.warning(f'Admin {request.user} sent invalid action {action} for loan {loan_id}')
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

class AdminDashboardView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        total_users = User.objects.count()
        total_loans = Loan.objects.count()
        approved_loans = Loan.objects.filter(status='approved').count()
        pending_loans = Loan.objects.filter(status='pending').count()
        rejected_loans = Loan.objects.filter(status='rejected').count()
        logger.info(f'Admin {request.user} viewed dashboard')
        return Response({
            'total_users': total_users,
            'total_loans': total_loans,
            'approved_loans': approved_loans,
            'pending_loans': pending_loans,
            'rejected_loans': rejected_loans,
        })

def home(request):
    return HttpResponse("Welcome to the Credit System Home Page!")

@csrf_exempt
def register_ui(request):
    result = None
    if request.method == 'POST':
        data = {
            'username': request.POST.get('username'),
            'email': request.POST.get('email'),
            'password': request.POST.get('password'),
            'phone_number': request.POST.get('phone_number'),
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
        }
        api_url = 'http://localhost:8000/api/v1/register/'
        try:
            r = requests.post(api_url, json=data)
            result = r.json()
        except Exception as e:
            result = {'error': str(e)}
    return render(request, 'register_ui.html', {'result': result})
