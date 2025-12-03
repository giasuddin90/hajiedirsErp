from django.contrib import admin
from .models import (
    SalesOrder, SalesOrderItem
)


class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 1


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'order_date', 'delivery_date', 'status', 'total_amount']
    list_filter = ['status', 'order_date', 'delivery_date', 'created_at']
    search_fields = ['order_number', 'customer__name', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [SalesOrderItemInline]
