from django.contrib import admin

from .models import BankAccount, BankAccountLedger, CreditCardLoan, CreditCardLoanLedger


class BankAccountLedgerInline(admin.TabularInline):
    model = BankAccountLedger
    extra = 0
    readonly_fields = ('created_by', 'created_at')


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'bank_name', 'account_number', 'account_type', 'current_balance', 'is_active')
    list_filter = ('account_type', 'is_active')
    search_fields = ('name', 'bank_name', 'account_number')
    inlines = [BankAccountLedgerInline]


@admin.register(BankAccountLedger)
class BankAccountLedgerAdmin(admin.ModelAdmin):
    list_display = ('bank_account', 'entry_type', 'transaction_date', 'amount', 'description')
    list_filter = ('entry_type', 'transaction_date', 'bank_account')
    search_fields = ('bank_account__name', 'description')


class CreditCardLoanLedgerInline(admin.TabularInline):
    model = CreditCardLoanLedger
    extra = 0


@admin.register(CreditCardLoan)
class CreditCardLoanAdmin(admin.ModelAdmin):
    list_display = ('deal_number', 'bank_account', 'principal_amount', 'status', 'start_date', 'closed_date')
    list_filter = ('status', 'start_date')
    search_fields = ('deal_number', 'lender_name')
    inlines = [CreditCardLoanLedgerInline]


@admin.register(CreditCardLoanLedger)
class CreditCardLoanLedgerAdmin(admin.ModelAdmin):
    list_display = ('loan', 'entry_type', 'transaction_date', 'payment_amount')
    list_filter = ('entry_type', 'transaction_date')
    search_fields = ('loan__deal_number',)
