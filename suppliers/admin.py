from django.contrib import admin
from .models import Supplier, SupplierLedger


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone', 'current_balance', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'phone', 'email', 'contact_person']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SupplierLedger)
class SupplierLedgerAdmin(admin.ModelAdmin):
    list_display = ['supplier', 'transaction_type', 'amount', 'transaction_date', 'created_by']
    list_filter = ['transaction_type', 'transaction_date', 'created_at']
    search_fields = ['supplier__name', 'description', 'reference']
    readonly_fields = ['created_at']


