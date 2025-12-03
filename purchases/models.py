from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from suppliers.models import Supplier
from stock.models import Product
import uuid
from datetime import datetime


class PurchaseOrder(models.Model):
    ORDER_STATUS = [
        ('purchase-order', 'Purchase Order'),
        ('goods-received', 'Goods Received'),
        ('canceled', 'Canceled'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    order_date = models.DateField()
    expected_date = models.DateField()
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='purchase-order')
    invoice_id = models.CharField(max_length=100, blank=True, help_text="Invoice ID from supplier when goods are received")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PO-{self.order_number} - {self.supplier.name}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number
            while True:
                # Create order number with timestamp and random component
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                random_part = str(uuid.uuid4().hex[:6].upper())
                self.order_number = f"PO-{timestamp}-{random_part}"
                
                # Check if this order number already exists
                if not PurchaseOrder.objects.filter(order_number=self.order_number).exists():
                    break
        
        super().save(*args, **kwargs)

    def update_inventory_on_status_change(self, old_status, new_status, user=None):
        """
        Inventory is now calculated in real-time from transaction status.
        No need to update pre-calculated stock - inventory increases automatically
        when status changes to 'goods-received' and decreases when cancelled.
        """
        # Real-time inventory calculation is handled by Product.get_realtime_quantity()
        # which sums purchase orders with status='goods-received' and subtracts sales.
        # No action needed here - inventory updates automatically based on status.
        pass
    
    def receive_goods(self, user=None):
        """Receive goods and update inventory (legacy method for compatibility)"""
        old_status = self.status
        self.status = 'goods-received'
        self.save()
        self.update_inventory_on_status_change(old_status, 'goods-received', user)
    
    def cancel_order(self, user=None):
        """Cancel the purchase order"""
        old_status = self.status
        self.status = 'canceled'
        self.save()
        self.update_inventory_on_status_change(old_status, 'canceled', user)

    class Meta:
        verbose_name = "Purchase Order"
        verbose_name_plural = "Purchase Orders"


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    total_price = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"{self.purchase_order.order_number} - {self.product.name}"

    class Meta:
        verbose_name = "Purchase Order Item"
        verbose_name_plural = "Purchase Order Items"


# GoodsReceipt model removed - simplified to use only PurchaseOrder
