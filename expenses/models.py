from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class ExpenseCategory(models.Model):
    """Categories for business expenses"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Expense Category"
        verbose_name_plural = "Expense Categories"
        ordering = ['name']


class Expense(models.Model):
    """Simple business expense records"""
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('credit_card', 'Credit Card'),
        ('mobile_banking', 'Mobile Banking'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=200, help_text="Brief description of the expense")
    description = models.TextField(blank=True, help_text="Detailed description")
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    
    # Financial Information
    amount = models.DecimalField(max_digits=15, decimal_places=2, help_text="Expense amount")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unpaid')
    
    # Dates
    expense_date = models.DateField(help_text="Date when expense occurred")
    paid_date = models.DateField(null=True, blank=True, help_text="Date when expense was paid")
    
    # Vendor Information
    vendor_name = models.CharField(max_length=200, blank=True, help_text="Vendor or supplier name")
    
    # Receipt and Documentation
    receipt_number = models.CharField(max_length=100, blank=True, help_text="Receipt or invoice number")
    
    # User and Timestamps
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_expenses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional Notes
    notes = models.TextField(blank=True, help_text="Additional notes or comments")
    
    def __str__(self):
        return f"{self.title} - ৳{self.amount} ({self.expense_date})"
    
    @property
    def is_paid(self):
        """Check if expense is paid"""
        return self.status == 'paid'
    
    class Meta:
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"
        ordering = ['-expense_date', '-created_at']