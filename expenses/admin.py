from django.contrib import admin
from .models import ExpenseCategory, Expense


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'amount', 'expense_date', 'status', 'payment_method', 'created_by']
    list_filter = ['status', 'category', 'payment_method', 'expense_date']
    search_fields = ['title', 'description', 'vendor_name', 'receipt_number']
    date_hierarchy = 'expense_date'
    ordering = ['-expense_date', '-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category')
        }),
        ('Financial Information', {
            'fields': ('amount', 'payment_method', 'status')
        }),
        ('Dates', {
            'fields': ('expense_date', 'paid_date')
        }),
        ('Vendor Information', {
            'fields': ('vendor_name',)
        }),
        ('Documentation', {
            'fields': ('receipt_number',)
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_by')
        }),
    )