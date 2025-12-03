from django import forms
from django.forms import inlineformset_factory
from decimal import Decimal, ROUND_HALF_UP
from .models import PurchaseOrder, PurchaseOrderItem
from suppliers.models import Supplier
from stock.models import Product, ProductCategory, ProductBrand


class RoundedDecimalField(forms.DecimalField):
    """Custom DecimalField that rounds input to 2 decimal places"""
    
    def to_python(self, value):
        if value is None or value == '':
            return None
        
        # Convert to Decimal and round to 2 decimal places
        decimal_value = Decimal(str(value))
        rounded_value = decimal_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return rounded_value


class PurchaseOrderForm(forms.ModelForm):
    """Form for creating and editing purchase orders"""
    
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'order_date', 'expected_date', 'status', 'invoice_id', 'notes']
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expected_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'invoice_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter invoice ID from supplier'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'supplier': 'Supplier',
            'order_date': 'Order Date',
            'expected_date': 'Expected Date',
            'status': 'Status',
            'invoice_id': 'Invoice ID',
            'notes': 'Notes',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True)
        self.fields['status'].choices = [
            ('purchase-order', 'Purchase Order'),
            ('goods-received', 'Goods Received'),
            ('canceled', 'Canceled'),
        ]
        
        # Set default status
        if not self.instance.pk:
            self.fields['status'].initial = 'purchase-order'


class PurchaseOrderItemForm(forms.ModelForm):
    """Form for purchase order items"""
    
    # Override fields to handle decimal places properly
    quantity = RoundedDecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control quantity-input', 'step': '0.01', 'min': '0'}),
        label='Quantity'
    )
    
    unit_price = RoundedDecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control price-input', 'step': '0.01', 'min': '0'}),
        label='Unit Price'
    )
    
    total_price = RoundedDecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control total-input', 'step': '0.01', 'readonly': True}),
        label='Total Price',
        required=False
    )
    
    class Meta:
        model = PurchaseOrderItem
        fields = ['product', 'quantity', 'unit_price', 'total_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select product-select'}),
        }
        labels = {
            'product': 'Product',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_active=True).select_related('category', 'brand')
        
        # Add data attributes for JavaScript filtering
        if 'product' in self.fields:
            self.fields['product'].widget.attrs.update({
                'class': 'form-select product-select',
            })

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None:
            if quantity <= 0:
                raise forms.ValidationError('Quantity must be greater than 0.')
            # Round to 2 decimal places
            quantity = round(quantity, 2)
        return quantity

    def clean_unit_price(self):
        unit_price = self.cleaned_data.get('unit_price')
        if unit_price is not None:
            if unit_price <= 0:
                raise forms.ValidationError('Unit price must be greater than 0.')
            # Round to 2 decimal places
            unit_price = round(unit_price, 2)
        return unit_price

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity', 0)
        unit_price = cleaned_data.get('unit_price', 0)
        
        # Calculate total price and round to 2 decimal places
        if quantity and unit_price:
            total = quantity * unit_price
            cleaned_data['total_price'] = round(total, 2)
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Calculate total price and round to 2 decimal places
        quantity = self.cleaned_data.get('quantity', 0)
        unit_price = self.cleaned_data.get('unit_price', 0)
        instance.total_price = round(quantity * unit_price, 2)
        
        if commit:
            instance.save()
        return instance


# Inline formset for purchase order items
PurchaseOrderItemFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    form=PurchaseOrderItemForm,
    fields=['product', 'quantity', 'unit_price', 'total_price'],
    extra=1,
    can_delete=True,
    min_num=0,  # Allow zero items initially
    validate_min=False,
)

# Custom formset class to handle creation without instance
class PurchaseOrderItemFormSetCustom(PurchaseOrderItemFormSet):
    def __init__(self, *args, **kwargs):
        # If no instance is provided, create a temporary one
        if 'instance' not in kwargs or kwargs['instance'] is None:
            kwargs['instance'] = PurchaseOrder()
        super().__init__(*args, **kwargs)


class PurchaseOrderSearchForm(forms.Form):
    """Form for searching purchase orders"""
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by order number, supplier, or status...'
        })
    )
