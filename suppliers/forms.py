from django import forms
from django.utils import timezone
from .models import Supplier, SupplierLedger


class SupplierForm(forms.ModelForm):
    """Form for creating and editing suppliers"""
    
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'address', 'city', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter supplier name'
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
                'placeholder': 'Enter full address'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter city'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make name field required
        self.fields['name'].required = True


class SupplierLedgerForm(forms.ModelForm):
    """Form for creating supplier ledger entries"""
    
    class Meta:
        model = SupplierLedger
        fields = ['transaction_type', 'amount', 'description', 'reference', 'transaction_date', 'payment_method']
        widgets = {
            'transaction_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter transaction description'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter reference number'
            }),
            'transaction_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default transaction date to now
        if not self.instance.pk:
            self.fields['transaction_date'].initial = timezone.now()
        
        # Make amount field required
        self.fields['amount'].required = True
        self.fields['description'].required = True
        self.fields['transaction_type'].required = True


class SetOpeningBalanceForm(forms.Form):
    """Form for setting supplier opening balance"""
    
    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Enter opening balance amount'
        }),
        help_text='Enter the opening balance amount (positive for amount owed to supplier, negative for amount owed by supplier)'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount'].required = True
