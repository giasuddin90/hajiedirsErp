from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class BankAccount(models.Model):
    ACCOUNT_TYPES = [
        ('current', 'Current'),
        ('savings', 'Savings'),
        ('credit_card', 'Credit Card'),
        ('loan', 'Loan'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=150)
    bank_name = models.CharField(max_length=150, blank=True)
    account_number = models.CharField(max_length=100, blank=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='current')
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.bank_name}" if self.bank_name else self.name

    class Meta:
        verbose_name = "Bank Account"
        verbose_name_plural = "Bank Accounts"
        ordering = ['name']


class CreditCardLoan(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]

    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credit_card_loans',
    )
    deal_number = models.CharField(max_length=100, unique=True)
    lender_name = models.CharField(max_length=150, blank=True)
    principal_amount = models.DecimalField(max_digits=15, decimal_places=2)
    start_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    closed_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_cc_loans')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Loan {self.deal_number}"

    def get_total_disbursed(self):
        total = self.ledger_entries.filter(entry_type='disbursement').aggregate(
            total=Sum('payment_amount')
        )['total'] or Decimal('0.00')
        return total if total > 0 else self.principal_amount

    def get_total_principal_paid(self):
        total_paid = self.get_total_paid()
        total_disbursed = self.get_total_disbursed()
        return min(total_paid, total_disbursed)

    def get_total_interest_paid(self):
        total_paid = self.get_total_paid()
        total_disbursed = self.get_total_disbursed()
        extra_paid = total_paid - total_disbursed
        return extra_paid if extra_paid > 0 else Decimal('0.00')

    def get_total_paid(self):
        return self.ledger_entries.filter(entry_type='payment').aggregate(
            total=Sum('payment_amount')
        )['total'] or Decimal('0.00')

    def get_outstanding_principal(self):
        outstanding = self.get_total_disbursed() - self.get_total_paid()
        return outstanding if outstanding > 0 else Decimal('0.00')

    def refresh_status(self):
        outstanding = self.get_outstanding_principal()
        if outstanding <= 0 and self.status != 'closed':
            self.status = 'closed'
            if not self.closed_date:
                self.closed_date = timezone.now().date()
            self.save(update_fields=['status', 'closed_date'])
        elif outstanding > 0 and self.status == 'closed':
            self.status = 'active'
            self.closed_date = None
            self.save(update_fields=['status', 'closed_date'])

    class Meta:
        verbose_name = "Credit Card Loan"
        verbose_name_plural = "Credit Card Loans"
        ordering = ['-start_date', '-created_at']


class CreditCardLoanLedger(models.Model):
    ENTRY_TYPES = [
        ('disbursement', 'Disbursement'),
        ('payment', 'Payment'),
    ]

    loan = models.ForeignKey(
        CreditCardLoan,
        on_delete=models.CASCADE,
        related_name='ledger_entries',
    )
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES)
    transaction_date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True)

    payment_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.loan.deal_number} - {self.get_entry_type_display()} - {self.transaction_date}"

    class Meta:
        verbose_name = "Credit Card Loan Ledger"
        verbose_name_plural = "Credit Card Loan Ledgers"
        ordering = ['-transaction_date', '-id']
