from django import forms
from .models import Customer, CustomerLedger, CustomerCommitment


class CustomerForm(forms.ModelForm):
    """Form for creating and editing customers"""
    
    class Meta:
        model = Customer
        fields = [
            'name', 'customer_type', 'contact_person', 'phone', 
            'address', 'credit_limit', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter customer name'
            }),
            'customer_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter contact person name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter address'
            }),
            'credit_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'name': 'Customer Name',
            'customer_type': 'Customer Type',
            'contact_person': 'Contact Person',
            'phone': 'Phone Number',
            'address': 'Address',
            'credit_limit': 'Credit Limit',
            'is_active': 'Active'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make name and customer_type required
        self.fields['name'].required = True
        self.fields['customer_type'].required = True


class CustomerLedgerForm(forms.ModelForm):
    """Form for creating customer ledger entries"""
    
    class Meta:
        model = CustomerLedger
        fields = [
            'transaction_type', 'amount', 'description', 
            'reference', 'transaction_date', 'payment_method'
        ]
        widgets = {
            'transaction_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'transaction_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'transaction_type': 'Transaction Type',
            'amount': 'Amount',
            'description': 'Description',
            'reference': 'Reference',
            'transaction_date': 'Transaction Date',
            'payment_method': 'Payment Method'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default transaction date to now
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['transaction_date'].initial = timezone.now()
        
        # Make required fields explicit
        self.fields['transaction_type'].required = True
        self.fields['amount'].required = True
        self.fields['description'].required = True
        self.fields['transaction_date'].required = True
    
    def clean_transaction_date(self):
        """Convert date to datetime"""
        date_value = self.cleaned_data.get('transaction_date')
        if date_value:
            from django.utils import timezone
            # Convert date to datetime with current time
            return timezone.datetime.combine(date_value, timezone.now().time())
        return date_value


class CustomerCommitmentForm(forms.ModelForm):
    """Form for creating customer commitments"""
    
    class Meta:
        model = CustomerCommitment
        fields = ['customer', 'commitment_date', 'amount', 'description']
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-select'
            }),
            'commitment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }
        labels = {
            'customer': 'Customer',
            'commitment_date': 'Commitment Date',
            'amount': 'Amount',
            'description': 'Description'
        }


class SetOpeningBalanceForm(forms.Form):
    """Form for setting opening balance"""
    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        }),
        label='Opening Balance Amount'
    )
    description = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter description (optional)'
        }),
        required=False,
        label='Description'
    )
