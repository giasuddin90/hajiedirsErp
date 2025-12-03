from django.contrib import admin
from .models import ProductCategory, ProductBrand, UnitType, Product


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ProductBrand)
class ProductBrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UnitType)
class UnitTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('name')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'brand', 'unit_type', 'cost_price', 'selling_price', 'is_active']
    list_filter = ['category', 'brand', 'unit_type', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'category__name', 'brand__name']
    readonly_fields = ['created_at', 'updated_at']


# Stock model removed - inventory is now calculated in real-time
# StockAlert model removed - alerts are now calculated dynamically based on min_stock_level
