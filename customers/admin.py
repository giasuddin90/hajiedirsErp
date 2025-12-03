from django.contrib import admin
from .models import Customer, CustomerLedger, CustomerCommitment


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'customer_type', 'phone', 'current_balance', 'is_active']
    list_filter = ['customer_type', 'is_active', 'created_at']
    search_fields = ['name', 'phone', 'email', 'contact_person']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CustomerLedger)
class CustomerLedgerAdmin(admin.ModelAdmin):
    list_display = ['customer', 'transaction_type', 'amount', 'transaction_date', 'created_by']
    list_filter = ['transaction_type', 'transaction_date', 'created_at']
    search_fields = ['customer__name', 'description', 'reference']
    readonly_fields = ['created_at']




@admin.register(CustomerCommitment)
class CustomerCommitmentAdmin(admin.ModelAdmin):
    list_display = ['customer', 'commitment_date', 'amount', 'is_reminded', 'is_fulfilled']
    list_filter = ['commitment_date', 'is_reminded', 'is_fulfilled', 'created_at']
    search_fields = ['customer__name', 'description']
    readonly_fields = ['created_at']
