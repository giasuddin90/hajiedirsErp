from django import forms
from django.forms import inlineformset_factory
from decimal import Decimal, ROUND_HALF_UP
from .models import PurchaseOrder, PurchaseOrderItem, GoodsReceipt, GoodsReceiptItem
from suppliers.models import Supplier
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


class GoodsReceiptForm(forms.ModelForm):
    """Form for creating and editing goods receipts"""
    
    class Meta:
        model = GoodsReceipt
        fields = ['purchase_order', 'receipt_date', 'notes']
        widgets = {
            'purchase_order': forms.Select(attrs={'class': 'form-select'}),
            'receipt_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'purchase_order': 'Purchase Order',
            'receipt_date': 'Receipt Date',
            'notes': 'Notes',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show purchase orders that are not canceled
        self.fields['purchase_order'].queryset = PurchaseOrder.objects.filter(
            status__in=['purchase-order', 'goods-received']
        ).order_by('-order_date')
        # Add data attribute for JavaScript
        self.fields['purchase_order'].widget.attrs['id'] = 'id_purchase_order'


class GoodsReceiptItemForm(forms.ModelForm):
    """Form for goods receipt items"""
    
    quantity = RoundedDecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control quantity-input', 'step': '0.01', 'min': '0'}),
        label='Quantity'
    )
    
    unit_cost = RoundedDecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control cost-input', 'step': '0.01', 'min': '0'}),
        label='Unit Cost'
    )
    
    total_cost = RoundedDecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control total-input', 'step': '0.01', 'readonly': True}),
        label='Total Cost',
        required=False
    )
    
    class Meta:
        model = GoodsReceiptItem
        fields = ['purchase_order_item', 'warehouse', 'quantity', 'unit_cost', 'total_cost']
        widgets = {
            'purchase_order_item': forms.Select(attrs={'class': 'form-select purchase-order-item-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'purchase_order_item': 'Order Item',
            'warehouse': 'Warehouse',
        }
    
    def __init__(self, *args, **kwargs):
        self.purchase_order = kwargs.pop('purchase_order', None)
        super().__init__(*args, **kwargs)
        
        # Filter purchase order items based on the purchase order
        if self.purchase_order:
            self.fields['purchase_order_item'].queryset = PurchaseOrderItem.objects.filter(
                purchase_order=self.purchase_order
            ).select_related('product')
        else:
            # If no purchase_order provided initially, show all items
            # The queryset will be validated in clean() method
            self.fields['purchase_order_item'].queryset = PurchaseOrderItem.objects.all().select_related('product')
        
        # Filter warehouses
        self.fields['warehouse'].queryset = Warehouse.objects.filter(is_active=True)
        self.fields['warehouse'].required = False
    
    def set_purchase_order(self, purchase_order):
        """Update the purchase_order and refresh the queryset"""
        self.purchase_order = purchase_order
        if purchase_order:
            self.fields['purchase_order_item'].queryset = PurchaseOrderItem.objects.filter(
                purchase_order=purchase_order
            ).select_related('product')
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None:
            if quantity <= 0:
                raise forms.ValidationError('Quantity must be greater than 0.')
            quantity = round(quantity, 2)
        return quantity
    
    def clean_unit_cost(self):
        unit_cost = self.cleaned_data.get('unit_cost')
        if unit_cost is not None:
            if unit_cost <= 0:
                raise forms.ValidationError('Unit cost must be greater than 0.')
            unit_cost = round(unit_cost, 2)
        return unit_cost
    
    def clean(self):
        cleaned_data = super().clean()
        purchase_order_item = cleaned_data.get('purchase_order_item')
        quantity = cleaned_data.get('quantity', 0)
        unit_cost = cleaned_data.get('unit_cost', 0)
        
        # If purchase_order_item is selected but purchase_order is not set yet,
        # get it from the purchase_order_item itself
        if purchase_order_item and not self.purchase_order:
            self.purchase_order = purchase_order_item.purchase_order
            # Update queryset to match
            self.fields['purchase_order_item'].queryset = PurchaseOrderItem.objects.filter(
                purchase_order=self.purchase_order
            ).select_related('product')
        
        # Validate purchase_order_item belongs to the correct purchase_order
        if purchase_order_item and self.purchase_order:
            if purchase_order_item.purchase_order != self.purchase_order:
                raise forms.ValidationError(
                    'Selected order item does not belong to the selected purchase order.'
                )
        
        if purchase_order_item and quantity:
            # Check if quantity exceeds remaining quantity
            remaining = purchase_order_item.get_remaining_quantity()
            if quantity > remaining:
                raise forms.ValidationError(
                    f'Quantity cannot exceed remaining quantity ({remaining}) for this order item.'
                )
        
        # Calculate total cost
        if quantity and unit_cost:
            total = quantity * unit_cost
            cleaned_data['total_cost'] = round(total, 2)
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Set product from purchase order item
        if instance.purchase_order_item:
            instance.product = instance.purchase_order_item.product
        
        # Calculate total cost
        quantity = self.cleaned_data.get('quantity', 0)
        unit_cost = self.cleaned_data.get('unit_cost', 0)
        instance.total_cost = round(quantity * unit_cost, 2)
        
        if commit:
            instance.save()
        return instance


# Base inline formset for goods receipt items (create mode - with extra forms)
BaseGoodsReceiptItemFormSet = inlineformset_factory(
    GoodsReceipt,
    GoodsReceiptItem,
    form=GoodsReceiptItemForm,
    fields=['purchase_order_item', 'warehouse', 'quantity', 'unit_cost', 'total_cost'],
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)

# Base inline formset for goods receipt items (edit mode - no extra forms)
BaseGoodsReceiptItemFormSetEdit = inlineformset_factory(
    GoodsReceipt,
    GoodsReceiptItem,
    form=GoodsReceiptItemForm,
    fields=['purchase_order_item', 'warehouse', 'quantity', 'unit_cost', 'total_cost'],
    extra=0,
    can_delete=True,
    min_num=0,
    validate_min=False,
)


# Custom formset class to pass purchase_order to forms (create mode)
class GoodsReceiptItemFormSet(BaseGoodsReceiptItemFormSet):
    def __init__(self, *args, **kwargs):
        self.purchase_order = kwargs.pop('purchase_order', None)
        super().__init__(*args, **kwargs)
        
        # Pass purchase_order to each form and update queryset
        for form in self.forms:
            if self.purchase_order:
                form.set_purchase_order(self.purchase_order)
            else:
                form.purchase_order = self.purchase_order
    
    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)
        if self.purchase_order:
            form.set_purchase_order(self.purchase_order)
        else:
            form.purchase_order = self.purchase_order
        return form


# Custom formset class to pass purchase_order to forms (edit mode)
class GoodsReceiptItemFormSetEdit(BaseGoodsReceiptItemFormSetEdit):
    def __init__(self, *args, **kwargs):
        self.purchase_order = kwargs.pop('purchase_order', None)
        super().__init__(*args, **kwargs)
        
        # Pass purchase_order to each form
        for form in self.forms:
            form.purchase_order = self.purchase_order
    
    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)
        form.purchase_order = self.purchase_order
        return form
