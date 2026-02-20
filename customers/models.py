from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class Customer(models.Model):
    CUSTOMER_TYPES = [
        ('retail', 'Retail'),
        ('wholesale', 'Wholesale'),
    ]
    
    name = models.CharField(max_length=200)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.customer_type})"
    
    def set_opening_balance(self, amount, user=None):
        """Set opening balance and create ledger entry"""
        self.opening_balance = amount
        self.current_balance = amount
        self.save()
        
        # Create opening balance ledger entry
        CustomerLedger.objects.create(
            customer=self,
            transaction_type='opening_balance',
            amount=amount,
            description=f"Opening balance set to ৳{amount}",
            reference="OPENING",
            transaction_date=timezone.now(),
            created_by=user
        )

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['customer_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['current_balance']),
        ]


class CustomerLedger(models.Model):
    TRANSACTION_TYPES = [
        ('opening_balance', 'Opening Balance'),
        ('sale', 'Sale'),
        ('return', 'Return'),
        ('payment', 'Payment'),
        ('adjustment', 'Adjustment'),
        ('commission', 'Commission'),
    ]
    
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('other', 'Other'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()
    reference = models.CharField(max_length=100, blank=True)
    transaction_date = models.DateTimeField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.name} - {self.transaction_type} - {self.amount}"

    class Meta:
        verbose_name = "Customer Ledger"
        verbose_name_plural = "Customer Ledgers"
        ordering = ['-transaction_date', '-id']




class CustomerCommitment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    commitment_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()
    is_reminded = models.BooleanField(default=False)
    is_fulfilled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.name} - {self.commitment_date} - {self.amount}"

    class Meta:
        verbose_name = "Customer Commitment"
        verbose_name_plural = "Customer Commitments"
        ordering = ['-commitment_date', '-id']
