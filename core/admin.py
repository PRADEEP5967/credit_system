
from django.contrib import admin
from .models import Customer, CreditApplication, Transaction, Loan

admin.site.register(Customer)
admin.site.register(CreditApplication)
admin.site.register(Transaction)
admin.site.register(Loan)
