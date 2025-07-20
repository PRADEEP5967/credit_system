from rest_framework import serializers
from .models import Customer, CreditApplication, Transaction, Loan
from django.contrib.auth.models import User
import re

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class CreditApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditApplication
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = '__all__'

class CustomerRegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    age = serializers.IntegerField()
    monthly_income = serializers.IntegerField()
    phone_number = serializers.CharField(max_length=15)

    def create(self, validated_data):
        # Calculate approved_limit: 36 * monthly_salary, rounded to nearest lakh
        salary = validated_data['monthly_income']
        approved_limit = round(36 * salary / 100000) * 100000
        customer = Customer.objects.create(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            age=validated_data['age'],
            phone_number=validated_data['phone_number'],
            monthly_salary=salary,
            approved_limit=approved_limit,
            current_debt=0
        )
        return customer

    def save(self, **kwargs):
        return self.create(self.validated_data)

class LoanEligibilitySerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.FloatField()
    interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()

class CreateLoanSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.FloatField()
    interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=True)
    phone_number = serializers.CharField(required=True, max_length=15)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'phone_number', 'first_name', 'last_name')

    def validate_phone_number(self, value):
        if not re.match(r'^\+?\d{10,15}$', value):
            raise serializers.ValidationError('Enter a valid phone number.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser') 