from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

def get_low_stock_products():
    """Helper function to get products with low stock based on min_stock_level"""
    products = Product.objects.filter(is_active=True)
    low_stock = []
    for product in products:
        qty = product.get_realtime_quantity()
        if qty <= product.min_stock_level and product.min_stock_level > 0:
            low_stock.append({
                'product': product,
                'current_quantity': qty,
                'min_quantity': product.min_stock_level
            })
    return low_stock


class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Warehouse"
        verbose_name_plural = "Warehouses"


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Product Category"
        verbose_name_plural = "Product Categories"
        ordering = ['name']


class ProductBrand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Product Brand"
        verbose_name_plural = "Product Brands"
        ordering = ['name']


class UnitType(models.Model):
    """Model to store unit types for products"""
    code = models.CharField(max_length=20, unique=True, help_text="Short code for the unit (e.g., 'kg', 'pcs')")
    name = models.CharField(max_length=100, help_text="Full name of the unit (e.g., 'Kilogram', 'Pieces')")
    description = models.TextField(blank=True, help_text="Optional description of the unit")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        verbose_name = "Unit Type"
        verbose_name_plural = "Unit Types"
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]


class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    brand = models.ForeignKey(ProductBrand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    unit_type = models.ForeignKey(UnitType, on_delete=models.PROTECT, related_name='products', help_text="Unit of measurement for this product")
    delivery_charge_per_unit = models.DecimalField(max_digits=10, decimal_places=5, default=0)
    pcs_per_carton = models.IntegerField(default=0)
    sqft_per_pcs = models.DecimalField(max_digits=20, decimal_places=10, default=0)
    description = models.TextField(blank=True)
    cost_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    min_stock_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.brand})"
    
    def get_realtime_quantity(self, warehouse=None):
        """
        Calculate inventory quantity in real-time from transactions.
        Formula: Total Goods Receipt Items (received) - Total Sales Delivered
        If warehouse is specified, returns quantity for that warehouse only.
        """
        try:
            from purchases.models import GoodsReceiptItem
            from sales.models import SalesOrderItem
            
            # Sum quantities from goods receipt items that are received
            receipt_filter = {
                'product': self,
                'goods_receipt__status': 'received'
            }
            if warehouse:
                receipt_filter['warehouse'] = warehouse
            
            total_purchase_received = GoodsReceiptItem.objects.filter(
                **receipt_filter
            ).aggregate(total=models.Sum('quantity'))['total'] or Decimal('0')
            
            # Sum quantities from sales orders that are delivered
            sales_filter = {
                'product': self,
                'sales_order__status': 'delivered'
            }
            if warehouse:
                # When warehouse is specified, only count sales from that warehouse
                sales_filter['warehouse'] = warehouse
            
            total_sales_delivered = SalesOrderItem.objects.filter(
                **sales_filter
            ).aggregate(total=models.Sum('quantity'))['total'] or Decimal('0')
            
            # Simple calculation: purchase received - sales delivered
            stock = total_purchase_received - total_sales_delivered
            return max(Decimal('0'), stock)  # Ensure non-negative
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error calculating realtime quantity for product {self.id}: {e}")
            return Decimal('0')
    
    def get_total_quantity(self):
        """Alias for get_realtime_quantity for backward compatibility"""
        return self.get_realtime_quantity()
    
    def get_total_stock_value(self):
        """Calculate total stock value using real-time quantity"""
        try:
            quantity = self.get_realtime_quantity()
            # Use average unit cost from recent goods receipts if available
            from purchases.models import GoodsReceiptItem
            recent_receipts = GoodsReceiptItem.objects.filter(
                product=self,
                goods_receipt__status='received'
            ).order_by('-goods_receipt__receipt_date')[:1]
            
            if recent_receipts.exists():
                unit_cost = recent_receipts.first().unit_cost
            else:
                unit_cost = self.cost_price
            
            return quantity * unit_cost
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error calculating total stock value for product {self.id}: {e}")
            return Decimal('0')

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['brand']),
            models.Index(fields=['is_active']),
            models.Index(fields=['selling_price']),
        ]


# Stock model removed - inventory is now calculated in real-time from transactions only
# No pre-calculated stock values or manual adjustments


# StockAlert model removed - alerts are now calculated dynamically based on min_stock_level
