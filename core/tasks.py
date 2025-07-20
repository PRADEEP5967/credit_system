from celery import shared_task
import pandas as pd
from .models import Customer, Loan
from django.db import transaction
from datetime import datetime

@shared_task
def ingest_customer_and_loan_data(customer_file_path, loan_file_path):
    # Ingest customers
    customer_df = pd.read_excel(customer_file_path)
    for _, row in customer_df.iterrows():
        Customer.objects.update_or_create(
            customer_id=row['Customer ID'],
            defaults={
                'first_name': row.get('First Name', ''),
                'last_name': row.get('Last Name', ''),
                'age': row.get('Age'),
                'phone_number': str(row.get('Phone Number', '')),
                'monthly_salary': row.get('Monthly Salary', 0),
                'approved_limit': row.get('Approved Limit', 0),
                'current_debt': row.get('Current Debt', 0),
            }
        )
    # Ingest loans
    loan_df = pd.read_excel(loan_file_path)
    for _, row in loan_df.iterrows():
        customer = Customer.objects.filter(customer_id=row['Customer ID']).first()
        if customer:
            Loan.objects.update_or_create(
                loan_id=row['Loan ID'],
                defaults={
                    'customer': customer,
                    'loan_amount': row.get('Loan Amount', 0),
                    'tenure': row.get('Tenure', 0),
                    'interest_rate': row.get('Interest Rate', 0),
                    'monthly_payment': row.get('Monthly payment', 0),
                    'emis_paid_on_time': row.get('EMIs paid on Time', 0),
                    'start_date': pd.to_datetime(row.get('Start date', datetime.now())).date() if 'Start date' in row else None,
                    'end_date': pd.to_datetime(row.get('End date', datetime.now())).date() if 'End date' in row else None,
                }
            ) 