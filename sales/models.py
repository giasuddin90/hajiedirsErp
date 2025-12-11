from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from customers.models import Customer
from stock.models import Product, Warehouse


class SalesOrder(models.Model):
    ORDER_STATUS = [
        ('order', 'Order'),
        ('delivered', 'Delivered'),
        ('cancel', 'Cancel'),
    ]
    
    SALES_TYPE = [
        ('regular', 'Regular Sale'),
        ('instant', 'Instant Sale'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True)
    sales_type = models.CharField(max_length=20, choices=SALES_TYPE, default='regular')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    customer_name = models.CharField(max_length=100, blank=True, help_text="For instant sales when no customer is selected")
    order_date = models.DateField()
    delivery_date = models.DateField(null=True, blank=True, help_text="Not required for instant sales")
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='order')
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    delivery_charges = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Total delivery charges (auto-calculated, can be manually adjusted)")
    transportation_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Transportation cost for this order")
    customer_deposit = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Customer deposit/advance payment for this order")
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        customer_name = self.customer.name if self.customer else self.customer_name or "Anonymous"
        return f"SO-{self.order_number} - {customer_name}"

    def mark_delivered(self, user=None):
        """
        Mark order as delivered.
        Inventory is calculated in real-time - no need to update pre-calculated stock.
        Inventory decreases automatically when status changes to 'delivered'.
        """
        if self.status == 'order':
            self.status = 'delivered'
            self.save()
            
            # Low stock alerts are now calculated dynamically based on min_stock_level
            # No need to create/store alerts - they're computed in real-time
    
    def cancel_order(self, user=None):
        """
        Cancel the order.
        Inventory is calculated in real-time - cancelling a delivered order
        automatically restores inventory because it's no longer counted in the calculation.
        """
        if self.status in ['order', 'delivered']:
            self.status = 'cancel'
            self.save()
            
            # No need to manually update stock - real-time calculation handles it automatically

    class Meta:
        verbose_name = "Sales Order"
        verbose_name_plural = "Sales Orders"
        ordering = ['-order_date', '-created_at']
        indexes = [
            models.Index(fields=['order_date']),
            models.Index(fields=['status']),
            models.Index(fields=['customer']),
            models.Index(fields=['sales_type']),
            models.Index(fields=['created_at']),
        ]


class SalesOrderItem(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, help_text="Warehouse from which this item will be sold")
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    total_price = models.DecimalField(max_digits=15, decimal_places=2)
    product_note = models.CharField(max_length=255, blank=True, help_text="Short note for this product item")

    def __str__(self):
        return f"{self.sales_order.order_number} - {self.product.name}"

    class Meta:
        verbose_name = "Sales Order Item"
        verbose_name_plural = "Sales Order Items"
        indexes = [
            models.Index(fields=['sales_order']),
            models.Index(fields=['product']),
            models.Index(fields=['warehouse']),
        ]


