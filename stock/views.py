from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db import models
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from django.contrib import messages
from datetime import datetime, timedelta
from decimal import Decimal
from .models import ProductCategory, ProductBrand, UnitType, Product, Warehouse, get_low_stock_products
from .forms import (
    ProductForm, ProductCategoryForm, ProductBrandForm, UnitTypeForm, WarehouseForm,
    ProductSearchForm, StockReportForm
)
from sales.models import SalesOrderItem
from purchases.models import PurchaseOrderItem, GoodsReceiptItem






class ProductListView(ListView):
    model = Product
    template_name = 'stock/product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Product.objects.select_related('category', 'brand').all()
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Filter by brand
        brand = self.request.GET.get('brand')
        if brand:
            queryset = queryset.filter(brand_id=brand)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Search by name
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ProductCategory.objects.filter(is_active=True).order_by('name')
        context['brands'] = ProductBrand.objects.filter(is_active=True).order_by('name')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_brand'] = self.request.GET.get('brand', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_search'] = self.request.GET.get('search', '')
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'stock/product_detail.html'


class ProductCreateView(CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'stock/product_form.html'
    success_url = reverse_lazy('stock:product_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ProductCategory.objects.filter(is_active=True)
        context['brands'] = ProductBrand.objects.filter(is_active=True)
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f'Product "{form.instance.name}" created successfully.')
        return super().form_valid(form)


class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'stock/product_form.html'
    success_url = reverse_lazy('stock:product_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ProductCategory.objects.filter(is_active=True)
        context['brands'] = ProductBrand.objects.filter(is_active=True)
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f'Product "{form.instance.name}" updated successfully.')
        return super().form_valid(form)


class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'stock/product_confirm_delete.html'
    success_url = reverse_lazy('stock:product_list')


class StockListView(ListView):
    """List view for products with real-time inventory"""
    model = Product
    template_name = 'stock/stock_list.html'
    context_object_name = 'products'
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category', 'brand', 'unit_type')
        
        # Filter by product name
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = self.get_queryset()
        
        # Get selected warehouse filter
        warehouse_id = self.request.GET.get('warehouse')
        selected_warehouse = None
        if warehouse_id:
            try:
                selected_warehouse = Warehouse.objects.get(pk=warehouse_id, is_active=True)
            except Warehouse.DoesNotExist:
                pass
        
        # Get all active warehouses for filter dropdown
        warehouses = Warehouse.objects.filter(is_active=True).order_by('name')
        
        # Calculate warehouse summary (how many products in each warehouse)
        warehouse_summary = []
        
        for warehouse in warehouses:
            # Count products that have stock in this warehouse
            products_in_warehouse = GoodsReceiptItem.objects.filter(
                warehouse=warehouse,
                goods_receipt__status='received'
            ).values('product').distinct().count()
            
            # Calculate total quantity and value in this warehouse using aggregation
            warehouse_aggregates = GoodsReceiptItem.objects.filter(
                warehouse=warehouse,
                goods_receipt__status='received'
            ).aggregate(
                total_qty=Sum('quantity'),
                total_value=Sum('total_cost')
            )
            
            warehouse_summary.append({
                'warehouse': warehouse,
                'product_count': products_in_warehouse,
                'total_quantity': warehouse_aggregates['total_qty'] or Decimal('0'),
                'total_value': warehouse_aggregates['total_value'] or Decimal('0'),
            })
        
        # Calculate summary statistics using real-time inventory
        stock_data = []
        total_products = 0
        in_stock = 0
        low_stock = 0
        out_of_stock = 0
        total_stock_value = Decimal('0')
        
        for product in products:
            # Get quantity for selected warehouse or total
            if selected_warehouse:
                qty = product.get_realtime_quantity(warehouse=selected_warehouse)
            else:
                qty = product.get_realtime_quantity()
            
            # Skip products with zero quantity if warehouse is selected
            if selected_warehouse and qty <= 0:
                continue
            
            total_products += 1
            
            # Calculate total stock value
            if selected_warehouse:
                # Calculate value for this warehouse only
                warehouse_items = GoodsReceiptItem.objects.filter(
                    product=product,
                    warehouse=selected_warehouse,
                    goods_receipt__status='received'
                )
                product_value = sum(item.total_cost for item in warehouse_items)
            else:
                product_value = product.get_total_stock_value()
            
            total_stock_value += product_value
            
            if qty <= 0:
                out_of_stock += 1
                status = 'out_of_stock'
            elif qty <= product.min_stock_level and product.min_stock_level > 0:
                low_stock += 1
                status = 'low_stock'
            else:
                in_stock += 1
                status = 'in_stock'
            
            # Get warehouse breakdown for this product
            warehouse_breakdown = []
            if not selected_warehouse:
                # Show breakdown by warehouse
                for warehouse in warehouses:
                    warehouse_qty = product.get_realtime_quantity(warehouse=warehouse)
                    if warehouse_qty > 0:
                        warehouse_breakdown.append({
                            'warehouse': warehouse,
                            'quantity': warehouse_qty
                        })
            
            stock_data.append({
                'product': product,
                'quantity': qty,
                'status': status,
                'value': product_value,
                'warehouse_breakdown': warehouse_breakdown,
                'selected_warehouse': selected_warehouse,
            })
        
        context.update({
            'stock_data': stock_data,
            'total_products': total_products,
            'in_stock': in_stock,
            'low_stock': low_stock,
            'out_of_stock': out_of_stock,
            'total_stock_value': total_stock_value,
            'warehouses': warehouses,
            'warehouse_summary': warehouse_summary,
            'selected_warehouse': selected_warehouse,
            'current_search': self.request.GET.get('search', ''),
            'current_warehouse': warehouse_id or '',
        })
        
        return context


class StockDetailView(DetailView):
    """Show product details with real-time inventory"""
    model = Product
    template_name = 'stock/stock_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['current_qty'] = product.get_realtime_quantity()
        context['total_value'] = product.get_total_stock_value()
        return context


# StockUpdateView removed - inventory is now real-time only




# Category Management Views
class ProductCategoryListView(ListView):
    model = ProductCategory
    template_name = 'stock/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ProductCategory.objects.all()
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Search by name
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', '')
        context['current_search'] = self.request.GET.get('search', '')
        return context


class ProductCategoryCreateView(CreateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = 'stock/category_form.html'
    success_url = reverse_lazy('stock:category_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" created successfully.')
        return super().form_valid(form)


class ProductCategoryUpdateView(UpdateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = 'stock/category_form.html'
    success_url = reverse_lazy('stock:category_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" updated successfully.')
        return super().form_valid(form)


class ProductCategoryDeleteView(DeleteView):
    model = ProductCategory
    template_name = 'stock/category_confirm_delete.html'
    success_url = reverse_lazy('stock:category_list')


# Brand Management Views
class ProductBrandListView(ListView):
    model = ProductBrand
    template_name = 'stock/brand_list.html'
    context_object_name = 'brands'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ProductBrand.objects.all()
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Search by name
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', '')
        context['current_search'] = self.request.GET.get('search', '')
        return context


class ProductBrandCreateView(CreateView):
    model = ProductBrand
    form_class = ProductBrandForm
    template_name = 'stock/brand_form.html'
    success_url = reverse_lazy('stock:brand_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Brand "{form.instance.name}" created successfully.')
        return super().form_valid(form)


class ProductBrandUpdateView(UpdateView):
    model = ProductBrand
    form_class = ProductBrandForm
    template_name = 'stock/brand_form.html'
    success_url = reverse_lazy('stock:brand_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Brand "{form.instance.name}" updated successfully.')
        return super().form_valid(form)


class ProductBrandDeleteView(DeleteView):
    model = ProductBrand
    template_name = 'stock/brand_confirm_delete.html'
    success_url = reverse_lazy('stock:brand_list')


# Stock adjustment removed - inventory is calculated in real-time from transactions only
# To adjust inventory, create purchase orders (to increase) or cancel sales (to decrease)


class StockReportView(ListView):
    """Stock report using real-time inventory"""
    model = Product
    template_name = 'stock/stock_report.html'
    context_object_name = 'products'
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category', 'brand')
        
        # Apply filters from form if provided
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        brand = self.request.GET.get('brand')
        if brand:
            queryset = queryset.filter(brand_id=brand)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = self.get_queryset()
        
        report_data = []
        for product in products:
            qty = product.get_realtime_quantity()
            value = product.get_total_stock_value()
            status = 'out_of_stock' if qty <= 0 else 'low_stock' if qty <= product.min_stock_level else 'in_stock'
            
            report_data.append({
                'product': product,
                'quantity': qty,
                'value': value,
                'status': status
            })
        
        context['report_data'] = report_data
        return context


class StockValuationReportView(ListView):
    """Stock valuation report using real-time inventory"""
    model = Product
    template_name = 'stock/stock_valuation_report.html'
    context_object_name = 'products'
    
    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category', 'brand')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = self.get_queryset()
        
        total_value = 0
        valuation_data = []
        for product in products:
            qty = product.get_realtime_quantity()
            value = product.get_total_stock_value()
            total_value += value
            
            if qty > 0:
                valuation_data.append({
                    'product': product,
                    'quantity': qty,
                    'unit_cost': product.cost_price,
                    'total_value': value
                })
        
        context['valuation_data'] = valuation_data
        context['total_value'] = total_value
        return context



# UnitType Management Views
class UnitTypeListView(ListView):
    model = UnitType
    template_name = 'stock/unittype_list.html'
    context_object_name = 'unit_types'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = UnitType.objects.all()
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Search by name or code
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(code__icontains=search)
            )
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', '')
        context['current_search'] = self.request.GET.get('search', '')
        return context


class UnitTypeCreateView(CreateView):
    model = UnitType
    form_class = UnitTypeForm
    template_name = 'stock/unittype_form.html'
    success_url = reverse_lazy('stock:unittype_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Unit Type "{form.instance.name}" created successfully.')
        return super().form_valid(form)


class UnitTypeUpdateView(UpdateView):
    model = UnitType
    form_class = UnitTypeForm
    template_name = 'stock/unittype_form.html'
    success_url = reverse_lazy('stock:unittype_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Unit Type "{form.instance.name}" updated successfully.')
        return super().form_valid(form)


class UnitTypeDeleteView(DeleteView):
    model = UnitType
    template_name = 'stock/unittype_confirm_delete.html'
    success_url = reverse_lazy('stock:unittype_list')
    
    def delete(self, request, *args, **kwargs):
        unit_type = self.get_object()
        messages.success(request, f'Unit Type "{unit_type.name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Warehouse Management Views
class WarehouseListView(ListView):
    model = Warehouse
    template_name = 'stock/warehouse_list.html'
    context_object_name = 'warehouses'
    paginate_by = 20
    ordering = ['name']
    
    def get_queryset(self):
        queryset = Warehouse.objects.all()
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Search by name
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset


class WarehouseDetailView(DetailView):
    model = Warehouse
    template_name = 'stock/warehouse_detail.html'
    context_object_name = 'warehouse'


class WarehouseCreateView(CreateView):
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'stock/warehouse_form.html'
    success_url = reverse_lazy('stock:warehouse_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'✅ Warehouse "{form.instance.name}" created successfully!')
        return super().form_valid(form)


class WarehouseUpdateView(UpdateView):
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'stock/warehouse_form.html'
    success_url = reverse_lazy('stock:warehouse_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'✅ Warehouse "{form.instance.name}" updated successfully!')
        return super().form_valid(form)


class WarehouseDeleteView(DeleteView):
    model = Warehouse
    template_name = 'stock/warehouse_confirm_delete.html'
    success_url = reverse_lazy('stock:warehouse_list')
    
    def delete(self, request, *args, **kwargs):
        warehouse = self.get_object()
        messages.success(request, f'✅ Warehouse "{warehouse.name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)
