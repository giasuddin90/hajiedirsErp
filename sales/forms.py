from django import forms
from django.forms import inlineformset_factory
from decimal import Decimal, ROUND_HALF_UP
from .models import SalesOrder, SalesOrderItem
from customers.models import Customer
from stock.models import Product, ProductCategory, ProductBrand, Warehouse


class RoundedDecimalField(forms.DecimalField):
    """Custom DecimalField that rounds input to 2 decimal places"""
    
    def to_python(self, value):
        if value is None or value == '':
            return None
        
        # Convert to Decimal and round to 2 decimal places
        decimal_value = Decimal(str(value))
        rounded_value = decimal_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return rounded_value


class SalesOrderForm(forms.ModelForm):
    """Form for creating and editing sales orders"""
    
    delivery_charges = RoundedDecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00', 'id': 'id_delivery_charges'}),
        label='Total Delivery Charge',
        required=False,
        min_value=Decimal('0'),  # Explicitly allow 0
        max_value=None  # No maximum limit
    )
    
    def clean_delivery_charges(self):
        """Allow 0 as a valid value for delivery charges"""
        value = self.cleaned_data.get('delivery_charges')
        # If value is None or empty string, return None (will be calculated in view)
        if value is None or value == '':
            return None
        # Convert to Decimal if needed
        if not isinstance(value, Decimal):
            try:
                value = Decimal(str(value))
            except (ValueError, TypeError):
                return None
        # Allow 0 as a valid value - explicitly allow it
        if value < 0:
            raise forms.ValidationError('Delivery charges cannot be negative.')
        # Return the value (including 0 if user set it to 0)
        return value
    
    discount_amount = RoundedDecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00', 'id': 'id_discount_amount'}),
        label='Discount Amount',
        required=False,
        min_value=Decimal('0'),
        max_value=None
    )
    
    customer_deposit = RoundedDecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00', 'id': 'id_customer_deposit'}),
        label='Customer Deposit',
        required=False,
        min_value=Decimal('0'),
        max_value=None
    )
    
    class Meta:
        model = SalesOrder
        fields = ['sales_type', 'customer', 'customer_name', 'order_date', 'delivery_date', 'status', 'delivery_charges', 'transportation_cost', 'discount_amount', 'customer_deposit', 'notes']
        widgets = {
            'sales_type': forms.Select(attrs={'class': 'form-select'}),
            'order_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'delivery_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter customer name for instant sales'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'transportation_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00', 'id': 'id_transportation_cost'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'sales_type': 'Sales Type',
            'customer': 'Customer',
            'customer_name': 'Customer Name',
            'order_date': 'Order Date',
            'delivery_date': 'Delivery Date',
            'status': 'Status',
            'transportation_cost': 'Transportation Cost',
            'notes': 'Notes',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.filter(is_active=True)
        self.fields['status'].choices = [
            ('order', 'Order'),
            ('delivered', 'Delivered'),
            ('cancel', 'Cancel'),
        ]
        
        # Add JavaScript for conditional field display
        self.fields['sales_type'].widget.attrs.update({
            'onchange': 'toggleCustomerFields()'
        })
        
        # Set default status and sales_type
        if not self.instance.pk:
            self.fields['status'].initial = 'order'
            self.fields['sales_type'].initial = 'regular'
            self.fields['delivery_charges'].initial = 0
            self.fields['discount_amount'].initial = 0
            self.fields['customer_deposit'].initial = 0
        else:
            # For existing orders, always show the saved delivery_charges from database
            # Don't recalculate - respect the saved value (even if 0)
            self.fields['delivery_charges'].initial = self.instance.delivery_charges or Decimal('0')
            self.fields['discount_amount'].initial = self.instance.discount_amount or Decimal('0')
            self.fields['customer_deposit'].initial = self.instance.customer_deposit or Decimal('0')
    
    def clean(self):
        cleaned_data = super().clean()
        sales_type = cleaned_data.get('sales_type')
        customer = cleaned_data.get('customer')
        customer_name = cleaned_data.get('customer_name')
        delivery_date = cleaned_data.get('delivery_date')
        
        # For instant sales, customer is optional but customer_name is required
        if sales_type == 'instant':
            if not customer and not customer_name:
                raise forms.ValidationError("For instant sales, either select a customer or enter a customer name.")
            # Delivery date is not required for instant sales
            if delivery_date:
                cleaned_data['delivery_date'] = None
        
        # For regular sales, customer is required
        elif sales_type == 'regular':
            if not customer:
                raise forms.ValidationError("Customer is required for regular sales.")
        
        return cleaned_data


class InstantSalesForm(forms.ModelForm):
    """Form specifically for instant sales"""
    
    class Meta:
        model = SalesOrder
        fields = ['customer_name', 'order_date', 'notes', 'sales_type']
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter customer name (optional)'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'sales_type': forms.HiddenInput(),
        }
        labels = {
            'customer_name': 'Customer Name',
            'order_date': 'Sale Date',
            'notes': 'Notes',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default values for instant sales
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['order_date'].initial = timezone.now().date()
            self.fields['sales_type'].initial = 'instant'
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.sales_type = 'instant'
        instance.status = 'delivered'  # Instant sales are immediately delivered
        if commit:
            instance.save()
        return instance


class SalesOrderItemForm(forms.ModelForm):
    """Form for sales order items"""
    
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
    
    product_note = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control product-note-input', 'placeholder': 'Short note (optional)', 'maxlength': '255'}),
        label='Product Note'
    )
    
    class Meta:
        model = SalesOrderItem
        fields = ['product', 'warehouse', 'quantity', 'unit_price', 'total_price', 'product_note']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select product-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select warehouse-select'}),
        }
        labels = {
            'product': 'Product',
            'warehouse': 'Warehouse',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_active=True).select_related('category', 'brand')
        self.fields['warehouse'].queryset = Warehouse.objects.filter(is_active=True).order_by('name')
        self.fields['warehouse'].required = True
        
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
        
        # If product is not selected, skip validation (empty form)
        product = cleaned_data.get('product')
        if not product:
            # Empty form - don't validate, just return
            # Django formset will ignore empty forms
            return cleaned_data
        
        warehouse = cleaned_data.get('warehouse')
        quantity = cleaned_data.get('quantity', 0)
        unit_price = cleaned_data.get('unit_price', 0)
        
        # Validate warehouse is selected when product is selected
        if product and not warehouse:
            raise forms.ValidationError('Warehouse must be selected when product is selected.')
        
        # Validate quantity and price if product is selected
        if product:
            if not quantity or quantity <= 0:
                raise forms.ValidationError('Quantity must be greater than 0 when product is selected.')
            if not unit_price or unit_price <= 0:
                raise forms.ValidationError('Unit price must be greater than 0 when product is selected.')
            
            # Validate available stock in warehouse
            if warehouse:
                available_qty = product.get_realtime_quantity(warehouse=warehouse)
                if quantity > available_qty:
                    raise forms.ValidationError(
                        f'Insufficient stock in {warehouse.name}. Available: {available_qty}, Requested: {quantity}'
                    )
        
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


# Override formset to handle empty forms
class BaseSalesOrderItemFormSet(forms.BaseInlineFormSet):
    def clean(self):
        """Allow empty forms - they will be ignored"""
        # Don't validate empty forms
        return super().clean()

# Inline formset for sales order items
SalesOrderItemFormSet = inlineformset_factory(
    SalesOrder,
    SalesOrderItem,
    form=SalesOrderItemForm,
    formset=BaseSalesOrderItemFormSet,
    fields=['product', 'warehouse', 'quantity', 'unit_price', 'total_price', 'product_note'],
    extra=0,  # No extra forms by default
    can_delete=True,
    min_num=0,  # Allow zero items initially
    validate_min=False,
)

# Custom formset class to handle creation without instance
class SalesOrderItemFormSetCustom(SalesOrderItemFormSet):
    def __init__(self, *args, **kwargs):
        # If no instance is provided, add one extra form for new orders
        if 'instance' not in kwargs or kwargs['instance'] is None:
            self.extra = 1
        else:
            # No extra forms for existing orders
            self.extra = 0
        super().__init__(*args, **kwargs)


class SalesOrderSearchForm(forms.Form):
    """Form for searching sales orders"""
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by order number, customer, or status...'
        })
    )
