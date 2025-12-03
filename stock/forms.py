from django import forms
from django.utils import timezone
from .models import Product, ProductCategory, ProductBrand, UnitType


class ProductCategoryForm(forms.ModelForm):
    """Form for creating and editing product categories"""
    
    class Meta:
        model = ProductCategory
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter category description'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'name': 'Category Name',
            'description': 'Description',
            'is_active': 'Active'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True


class ProductBrandForm(forms.ModelForm):
    """Form for creating and editing product brands"""
    
    class Meta:
        model = ProductBrand
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter brand name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter brand description'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'name': 'Brand Name',
            'description': 'Description',
            'is_active': 'Active'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True


class UnitTypeForm(forms.ModelForm):
    """Form for creating and editing unit types"""
    
    class Meta:
        model = UnitType
        fields = ['code', 'name', 'description', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter unit code (e.g., kg, pcs)'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter unit name (e.g., Kilogram, Pieces)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter unit description'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'code': 'Unit Code',
            'name': 'Unit Name',
            'description': 'Description',
            'is_active': 'Active'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['code'].required = True
        self.fields['name'].required = True
    
    def clean_code(self):
        """Validate unit code"""
        code = self.cleaned_data.get('code')
        if code:
            code = code.lower().strip()
            # Check if code already exists (excluding current instance)
            queryset = UnitType.objects.filter(code=code)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError("A unit type with this code already exists.")
        return code


class ProductForm(forms.ModelForm):
    """Form for creating and editing products"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'brand', 'unit_type', 'description',
            'cost_price', 'selling_price', 'min_stock_level', 
            'delivery_charge_per_unit', 'pcs_per_carton', 'sqft_per_pcs',
            'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter product name'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_category'
            }),
            'brand': forms.Select(attrs={
                'class': 'form-select'
            }),
            'unit_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter product description'
            }),
            'cost_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'selling_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'min_stock_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'delivery_charge_per_unit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'pcs_per_carton': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1',
                'min': '0',
                'placeholder': '0',
                'id': 'id_pcs_per_carton'
            }),
            'sqft_per_pcs': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'id_sqft_per_pcs'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'name': 'Product Name',
            'category': 'Category',
            'brand': 'Brand',
            'unit_type': 'Unit Type',
            'description': 'Description',
            'cost_price': 'Cost Price',
            'selling_price': 'Selling Price',
            'min_stock_level': 'Minimum Stock Level',
            'delivery_charge_per_unit': 'Delivery Charge per Unit',
            'pcs_per_carton': 'Pieces per Carton',
            'sqft_per_pcs': 'Square Feet per Piece',
            'is_active': 'Active'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make name field required
        self.fields['name'].required = True
        
        # Filter active categories, brands, and unit types
        self.fields['category'].queryset = ProductCategory.objects.filter(is_active=True).order_by('name')
        self.fields['brand'].queryset = ProductBrand.objects.filter(is_active=True).order_by('name')
        self.fields['unit_type'].queryset = UnitType.objects.filter(is_active=True).order_by('name')
        
        # Add empty option for category and brand
        self.fields['category'].empty_label = "Select Category (Optional)"
        self.fields['brand'].empty_label = "Select Brand (Optional)"
        self.fields['unit_type'].empty_label = "Select Unit Type"
        
        # Set default values for new fields
        if not self.instance.pk:
            self.fields['delivery_charge_per_unit'].initial = 0
            self.fields['pcs_per_carton'].initial = 0
            self.fields['sqft_per_pcs'].initial = 0
    
    def clean_selling_price(self):
        """Validate selling price"""
        selling_price = self.cleaned_data.get('selling_price')
        cost_price = self.cleaned_data.get('cost_price')
        
        if selling_price and cost_price and selling_price < cost_price:
            raise forms.ValidationError("Selling price cannot be less than cost price.")
        
        return selling_price
    
    def clean_min_stock_level(self):
        """Validate minimum stock level"""
        min_stock_level = self.cleaned_data.get('min_stock_level')
        
        if min_stock_level is not None and min_stock_level < 0:
            raise forms.ValidationError("Minimum stock level cannot be negative.")
        
        return min_stock_level


# StockForm and StockAdjustmentForm removed - inventory is now real-time only
# No manual stock adjustments or pre-calculated stock values


# StockAlertForm removed - alerts are now calculated dynamically based on min_stock_level


class ProductSearchForm(forms.Form):
    """Form for product search and filtering"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search products...'
        }),
        label='Search'
    )
    
    category = forms.ModelChoiceField(
        queryset=ProductCategory.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Category'
    )
    
    brand = forms.ModelChoiceField(
        queryset=ProductBrand.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label="All Brands",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Brand'
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'All Status'),
            ('active', 'Active'),
            ('inactive', 'Inactive'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Status'
    )
    
    unit_type = forms.ModelChoiceField(
        queryset=UnitType.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label="All Units",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Unit Type'
    )


class StockReportForm(forms.Form):
    """Form for stock report filtering"""
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='From Date'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='To Date'
    )
    
    category = forms.ModelChoiceField(
        queryset=ProductCategory.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Category'
    )
    
    brand = forms.ModelChoiceField(
        queryset=ProductBrand.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label="All Brands",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Brand'
    )
    
    stock_status = forms.ChoiceField(
        choices=[
            ('', 'All Stock Status'),
            ('in_stock', 'In Stock'),
            ('low_stock', 'Low Stock'),
            ('out_of_stock', 'Out of Stock'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Stock Status'
    )
    
    def clean(self):
        """Validate date range"""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("From date cannot be after to date.")
        
        return cleaned_data
