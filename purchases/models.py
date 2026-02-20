from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from suppliers.models import Supplier
from stock.models import Product, Warehouse
import uuid
from datetime import datetime


class PurchaseOrder(models.Model):
    ORDER_STATUS = [
        ('purchase-order', 'Purchase Order'),
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
        Inventory is now calculated in real-time from GoodsReceipt items.
        No need to update pre-calculated stock - inventory increases automatically
        when goods receipts are confirmed.
        """
        # Real-time inventory calculation is handled by Product.get_realtime_quantity()
        # which sums GoodsReceiptItem with status='received' and subtracts sales.
        # No action needed here - inventory updates automatically based on goods receipts.
        pass
    
    def cancel_order(self, user=None):
        """Cancel the purchase order"""
        old_status = self.status
        self.status = 'canceled'
        self.save()
        self.update_inventory_on_status_change(old_status, 'canceled', user)

    class Meta:
        verbose_name = "Purchase Order"
        verbose_name_plural = "Purchase Orders"
        ordering = ['-order_date', '-created_at']


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    total_price = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"{self.purchase_order.order_number} - {self.product.name}"
    
    def get_received_quantity(self):
        """Calculate total quantity received for this order item"""
        total_received = GoodsReceiptItem.objects.filter(
            purchase_order_item=self,
            goods_receipt__status='received'
        ).aggregate(total=models.Sum('quantity'))['total'] or Decimal('0')
        return total_received
    
    def get_remaining_quantity(self):
        """Calculate remaining quantity to be received"""
        received = self.get_received_quantity()
        return max(Decimal('0'), self.quantity - received)
    
    def is_fully_received(self):
        """Check if all quantities have been received"""
        return self.get_received_quantity() >= self.quantity

    class Meta:
        verbose_name = "Purchase Order Item"
        verbose_name_plural = "Purchase Order Items"
        ordering = ['id']


class GoodsReceipt(models.Model):
    RECEIPT_STATUS = [
        ('draft', 'Draft'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]

    receipt_number = models.CharField(max_length=50, unique=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='goods_receipts')
    receipt_date = models.DateField()
    status = models.CharField(max_length=20, choices=RECEIPT_STATUS, default='draft')
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"GR-{self.receipt_number} - {self.purchase_order.supplier.name}"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            # Generate unique receipt number
            while True:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                random_part = str(uuid.uuid4().hex[:6].upper())
                self.receipt_number = f"GR-{timestamp}-{random_part}"
                
                if not GoodsReceipt.objects.filter(receipt_number=self.receipt_number).exists():
                    break
        
        super().save(*args, **kwargs)
        
        # Calculate total amount from items after saving
        if self.pk:
            self.total_amount = sum(item.total_cost for item in self.items.all())
            # Update without triggering save again to avoid recursion
            GoodsReceipt.objects.filter(pk=self.pk).update(total_amount=self.total_amount)
    
    def confirm_receipt(self):
        """Confirm receipt and update inventory"""
        if self.status == 'draft':
            self.status = 'received'
            self.save()
            return True
        return False
    
    def cancel_receipt(self):
        """Cancel receipt and reverse inventory"""
        if self.status == 'received':
            self.status = 'cancelled'
            self.save()
            return True
        return False

    class Meta:
        verbose_name = "Goods Receipt"
        verbose_name_plural = "Goods Receipts"
        ordering = ['-receipt_date', '-created_at']


class GoodsReceiptItem(models.Model):
    goods_receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name='items')
    purchase_order_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.CASCADE, related_name='receipt_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"{self.goods_receipt.receipt_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Calculate total cost
        if self.quantity and self.unit_cost:
            self.total_cost = round(self.quantity * self.unit_cost, 2)
        
        # Ensure product matches purchase order item
        if not self.product_id:
            self.product = self.purchase_order_item.product
        
        super().save(*args, **kwargs)
        
        # Update goods receipt total amount
        if self.goods_receipt:
            self.goods_receipt.save()

    class Meta:
        verbose_name = "Goods Receipt Item"
        verbose_name_plural = "Goods Receipt Items"
        ordering = ['id']


