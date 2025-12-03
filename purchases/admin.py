from django.contrib import admin
from .models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'supplier', 'order_date', 'expected_date', 'status', 'invoice_id', 'total_amount']
    list_filter = ['status', 'order_date', 'expected_date', 'created_at']
    search_fields = ['order_number', 'supplier__name', 'invoice_id', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PurchaseOrderItemInline]
