from decimal import Decimal

from django import forms

from .models import BankAccount, CreditCardLoan, CreditCardLoanLedger


class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = [
            'name',
            'bank_name',
            'account_number',
            'account_type',
            'opening_balance',
            'current_balance',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'opening_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'current_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CreditCardLoanForm(forms.ModelForm):
    class Meta:
        model = CreditCardLoan
        fields = [
            'bank_account',
            'deal_number',
            'lender_name',
            'principal_amount',
            'start_date',
            'status',
            'closed_date',
            'notes',
        ]
        widgets = {
            'bank_account': forms.Select(attrs={'class': 'form-select'}),
            'deal_number': forms.TextInput(attrs={'class': 'form-control'}),
            'lender_name': forms.TextInput(attrs={'class': 'form-control'}),
            'principal_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'closed_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CreditCardLoanLedgerForm(forms.ModelForm):
    class Meta:
        model = CreditCardLoanLedger
        fields = [
            'entry_type',
            'transaction_date',
            'description',
            'payment_amount',
        ]
        widgets = {
            'entry_type': forms.Select(attrs={'class': 'form-select'}),
            'transaction_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        entry_type = cleaned_data.get('entry_type')
        payment_amount = cleaned_data.get('payment_amount') or Decimal('0.00')
        if entry_type == 'disbursement':
            if payment_amount <= 0:
                self.add_error('payment_amount', 'Disbursement amount must be greater than 0.')
        elif entry_type == 'payment':
            if payment_amount <= 0:
                self.add_error('payment_amount', 'Payment amount must be greater than 0.')
        return cleaned_data
