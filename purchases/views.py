from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from .models import PurchaseOrder, PurchaseOrderItem, GoodsReceipt, GoodsReceiptItem
from .forms import (
    PurchaseOrderForm, PurchaseOrderItemFormSet, PurchaseOrderItemFormSetCustom, PurchaseOrderSearchForm, PurchaseOrderItemForm,
    GoodsReceiptForm, GoodsReceiptItemFormSet, GoodsReceiptItemFormSetEdit, GoodsReceiptItemForm
)
from suppliers.models import Supplier
from stock.models import Product, ProductCategory, ProductBrand
from django.contrib.auth.models import User
import uuid


class PurchaseOrderListView(ListView):
    model = PurchaseOrder
    template_name = 'purchases/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    ordering = ['-order_date', '-created_at']
    
    def get_queryset(self):
        from django.db import models
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        
        if search_query:
            queryset = queryset.filter(
                models.Q(order_number__icontains=search_query) |
                models.Q(supplier__name__icontains=search_query) |
                models.Q(status__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = PurchaseOrderSearchForm(self.request.GET)
        return context


class PurchaseOrderDetailView(DetailView):
    model = PurchaseOrder
    template_name = 'purchases/order_detail.html'
    context_object_name = 'order'


class PurchaseOrderCreateView(CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'purchases/order_form.html'
    success_url = reverse_lazy('purchases:order_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            # Use custom formset that handles creation without instance
            context['formset'] = PurchaseOrderItemFormSetCustom(self.request.POST)
        else:
            # Use custom formset that handles creation without instance
            context['formset'] = PurchaseOrderItemFormSetCustom()
        
        context['categories'] = ProductCategory.objects.filter(is_active=True)
        context['brands'] = ProductBrand.objects.filter(is_active=True)
        context['products'] = Product.objects.filter(is_active=True).select_related('category', 'brand')
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        # Set created_by before validation
        form.instance.created_by = self.request.user
        
        if formset.is_valid():
            with transaction.atomic():
                # Save the order first
                self.object = form.save()
                
                # Re-bind formset to the actual saved instance
                formset.instance = self.object
                # Re-validate with the correct instance
                formset = PurchaseOrderItemFormSet(self.request.POST, instance=self.object)
                
                if formset.is_valid():
                    # Save formset
                    formset.save()
                    
                    # Calculate total amount and round to 2 decimal places
                    total_amount = sum(item.total_price for item in self.object.items.all())
                    self.object.total_amount = round(total_amount, 2)
                    self.object.save()
                    
                    messages.success(self.request, f'✅ Purchase Order {self.object.order_number} created successfully!')
                    return redirect(self.success_url)
                else:
                    # If formset validation fails after binding, show errors
                    messages.error(self.request, '❌ Please correct the errors below.')
                    context['formset'] = formset
                    return self.render_to_response(context)
        else:
            messages.error(self.request, '❌ Please correct the errors below.')
            return self.form_invalid(form)


class PurchaseOrderUpdateView(UpdateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'purchases/order_form.html'
    success_url = reverse_lazy('purchases:order_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = PurchaseOrderItemFormSet(self.request.POST, instance=self.object)
        else:
            # For edit view, don't show extra empty forms
            from .forms import inlineformset_factory
            EditFormSet = inlineformset_factory(
                PurchaseOrder,
                PurchaseOrderItem,
                form=PurchaseOrderItemForm,
                fields=['product', 'quantity', 'unit_price', 'total_price'],
                extra=0,  # No extra forms for edit
                can_delete=True,
                min_num=0,
                validate_min=False,
            )
            context['formset'] = EditFormSet(instance=self.object)
        
        context['categories'] = ProductCategory.objects.filter(is_active=True)
        context['brands'] = ProductBrand.objects.filter(is_active=True)
        context['products'] = Product.objects.filter(is_active=True).select_related('category', 'brand')
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            with transaction.atomic():
                # Store the old status before saving
                old_status = self.object.status
                new_status = form.cleaned_data.get('status')
                
                # Save the order first
                response = super().form_valid(form)
                
                # Save formset
                formset.save()
                
                # Calculate total amount and round to 2 decimal places
                total_amount = sum(item.total_price for item in self.object.items.all())
                self.object.total_amount = round(total_amount, 2)
                self.object.save()
                
                # Update inventory based on status change
                self.object.update_inventory_on_status_change(old_status, new_status, user=self.request.user)
                
                # Show appropriate success message
                if old_status != new_status:
                    if new_status == 'canceled':
                        messages.success(self.request, f'✅ Purchase Order {self.object.order_number} cancelled!')
                    else:
                        messages.success(self.request, f'✅ Purchase Order {self.object.order_number} updated successfully!')
                else:
                    messages.success(self.request, f'✅ Purchase Order {self.object.order_number} updated successfully!')
                
                return response
        else:
            messages.error(self.request, '❌ Please correct the errors below.')
            return self.form_invalid(form)


class PurchaseOrderDeleteView(DeleteView):
    model = PurchaseOrder
    template_name = 'purchases/order_confirm_delete.html'
    success_url = reverse_lazy('purchases:order_list')


# Reports
class PurchaseDailyReportView(ListView):
    model = PurchaseOrder
    template_name = 'purchases/reports/daily_report.html'
    context_object_name = 'orders'
    
    def get_queryset(self):
        date = self.request.GET.get('date', timezone.now().date())
        return PurchaseOrder.objects.filter(order_date=date)


class PurchaseMonthlyReportView(ListView):
    model = PurchaseOrder
    template_name = 'purchases/reports/monthly_report.html'
    context_object_name = 'orders'
    
    def get_queryset(self):
        year = self.request.GET.get('year', timezone.now().year)
        month = self.request.GET.get('month', timezone.now().month)
        return PurchaseOrder.objects.filter(
            order_date__year=year,
            order_date__month=month
        )


class PurchaseSupplierReportView(ListView):
    """
    Supplier-specific report showing all purchase orders and goods receipts.
    """
    model = PurchaseOrder
    template_name = 'purchases/purchase_supplier_report.html'
    context_object_name = 'orders'
    
    def get_queryset(self):
        supplier_id = self.request.GET.get('supplier')
        if not supplier_id:
            return PurchaseOrder.objects.none()
        
        return (
            PurchaseOrder.objects.filter(supplier_id=supplier_id)
            .select_related('supplier', 'created_by')
            .order_by('-order_date', '-created_at')
        )
    
    def get_context_data(self, **kwargs):
        from django.db.models import Sum
        
        context = super().get_context_data(**kwargs)
        supplier_id = self.request.GET.get('supplier')
        
        # Supplier list for the filter dropdown
        context['suppliers'] = Supplier.objects.filter(is_active=True).order_by('name')
        context['selected_supplier_id'] = int(supplier_id) if supplier_id else None
        context['selected_supplier'] = None
        
        if supplier_id:
            context['selected_supplier'] = Supplier.objects.filter(id=supplier_id).first()
            
            # Goods receipts for the selected supplier
            receipts = (
                GoodsReceipt.objects.filter(purchase_order__supplier_id=supplier_id)
                .select_related('purchase_order', 'purchase_order__supplier', 'created_by')
                .order_by('-receipt_date', '-created_at')
            )
            context['receipts'] = receipts
            
            # Order items with received/remaining quantities (ledger-style)
            order_items = (
                PurchaseOrderItem.objects.filter(purchase_order__supplier_id=supplier_id)
                .select_related('purchase_order', 'product')
                .order_by('-purchase_order__order_date', '-purchase_order__created_at')
            )
            context['order_items'] = order_items
            
            # Receipt items with quantities (ledger-style)
            receipt_items = (
                GoodsReceiptItem.objects.filter(goods_receipt__purchase_order__supplier_id=supplier_id)
                .select_related('goods_receipt', 'goods_receipt__purchase_order', 'product', 'warehouse')
                .order_by('-goods_receipt__receipt_date', '-goods_receipt__created_at')
            )
            context['receipt_items'] = receipt_items
            
            # Totals
            context['orders_total'] = self.object_list.aggregate(total=Sum('total_amount'))['total'] or 0
            context['receipts_total'] = receipts.aggregate(total=Sum('total_amount'))['total'] or 0
        else:
            context['receipts'] = GoodsReceipt.objects.none()
            context['order_items'] = PurchaseOrderItem.objects.none()
            context['receipt_items'] = GoodsReceiptItem.objects.none()
            context['orders_total'] = 0
            context['receipts_total'] = 0
        
        return context


# Goods Receipt Views
class GoodsReceiptListView(ListView):
    model = GoodsReceipt
    template_name = 'purchases/receipt_list.html'
    context_object_name = 'receipts'
    paginate_by = 20
    ordering = ['-receipt_date', '-created_at']
    
    def get_queryset(self):
        from django.db import models
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        purchase_order_id = self.request.GET.get('purchase_order')
        
        if search_query:
            queryset = queryset.filter(
                models.Q(receipt_number__icontains=search_query) |
                models.Q(purchase_order__order_number__icontains=search_query) |
                models.Q(purchase_order__supplier__name__icontains=search_query)
            )
        
        if purchase_order_id:
            queryset = queryset.filter(purchase_order_id=purchase_order_id)
        
        return queryset.select_related('purchase_order', 'purchase_order__supplier', 'created_by')


class GoodsReceiptDetailView(DetailView):
    model = GoodsReceipt
    template_name = 'purchases/receipt_detail.html'
    context_object_name = 'receipt'


class GoodsReceiptCreateView(CreateView):
    model = GoodsReceipt
    form_class = GoodsReceiptForm
    template_name = 'purchases/receipt_form.html'
    
    def get_success_url(self):
        return reverse_lazy('purchases:receipt_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        purchase_order = None
        
        # Get purchase_order from GET or POST
        purchase_order_id = self.request.GET.get('purchase_order') or self.request.POST.get('purchase_order')
        
        if purchase_order_id:
            purchase_order = get_object_or_404(PurchaseOrder, pk=purchase_order_id)
            context['purchase_order'] = purchase_order
        
        # Create formset with purchase_order
        if self.request.POST:
            # For POST, we need to get purchase_order from form data if not already set
            if not purchase_order:
                purchase_order_id_from_form = self.request.POST.get('purchase_order')
                if purchase_order_id_from_form:
                    purchase_order = get_object_or_404(PurchaseOrder, pk=purchase_order_id_from_form)
                    context['purchase_order'] = purchase_order
            formset = GoodsReceiptItemFormSet(self.request.POST, purchase_order=purchase_order)
        else:
            formset = GoodsReceiptItemFormSet(purchase_order=purchase_order)
            # Set initial purchase_order if provided
            if purchase_order:
                context['form'].initial['purchase_order'] = purchase_order
        
        context['formset'] = formset
        return context
    
    def form_valid(self, form):
        purchase_order = form.cleaned_data.get('purchase_order')
        
        # Recreate formset with the validated purchase_order
        formset = GoodsReceiptItemFormSet(self.request.POST, purchase_order=purchase_order)
        
        if formset.is_valid():
            with transaction.atomic():
                # Set created_by
                form.instance.created_by = self.request.user
                
                # Save the receipt first
                self.object = form.save()
                
                # Set the instance for the formset
                formset.instance = self.object
                
                # Save formset
                formset.save()
                
                # Calculate total amount
                total_amount = sum(item.total_cost for item in self.object.items.all())
                self.object.total_amount = round(total_amount, 2)
                self.object.save()
                
                messages.success(self.request, f'✅ Goods Receipt {self.object.receipt_number} created successfully!')
                return redirect(self.get_success_url())
        else:
            messages.error(self.request, '❌ Please correct the errors below.')
            return self.form_invalid(form)


class GoodsReceiptUpdateView(UpdateView):
    model = GoodsReceipt
    form_class = GoodsReceiptForm
    template_name = 'purchases/receipt_form.html'
    
    def get_success_url(self):
        return reverse_lazy('purchases:receipt_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        purchase_order = self.object.purchase_order
        
        if self.request.POST:
            formset = GoodsReceiptItemFormSetEdit(self.request.POST, instance=self.object, purchase_order=purchase_order)
        else:
            # For edit view, use edit formset (no extra forms)
            formset = GoodsReceiptItemFormSetEdit(instance=self.object, purchase_order=purchase_order)
        
        context['formset'] = formset
        context['purchase_order'] = purchase_order
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        purchase_order = self.object.purchase_order
        
        if formset.is_valid():
            with transaction.atomic():
                # Save the receipt first
                response = super().form_valid(form)
                
                # Save formset
                formset.save()
                
                # Calculate total amount
                total_amount = sum(item.total_cost for item in self.object.items.all())
                self.object.total_amount = round(total_amount, 2)
                self.object.save()
                
                messages.success(self.request, f'✅ Goods Receipt {self.object.receipt_number} updated successfully!')
                return response
        else:
            messages.error(self.request, '❌ Please correct the errors below.')
            return self.form_invalid(form)


class GoodsReceiptDeleteView(DeleteView):
    model = GoodsReceipt
    template_name = 'purchases/receipt_confirm_delete.html'
    success_url = reverse_lazy('purchases:receipt_list')


def confirm_goods_receipt(request, pk):
    """Confirm goods receipt and update inventory"""
    receipt = get_object_or_404(GoodsReceipt, pk=pk)
    
    if receipt.status == 'draft':
        with transaction.atomic():
            receipt.confirm_receipt()
            messages.success(request, f'✅ Goods Receipt {receipt.receipt_number} confirmed! Inventory updated.')
    else:
        messages.warning(request, f'⚠️ Goods Receipt {receipt.receipt_number} is already {receipt.get_status_display()}.')
    
    return redirect('purchases:receipt_detail', pk=receipt.pk)


def cancel_goods_receipt(request, pk):
    """Cancel goods receipt and reverse inventory"""
    receipt = get_object_or_404(GoodsReceipt, pk=pk)
    
    if receipt.status == 'received':
        with transaction.atomic():
            receipt.cancel_receipt()
            messages.success(request, f'✅ Goods Receipt {receipt.receipt_number} cancelled! Inventory adjusted.')
    else:
        messages.warning(request, f'⚠️ Only received receipts can be cancelled.')
    
    return redirect('purchases:receipt_detail', pk=receipt.pk)


def get_purchase_order_items(request, purchase_order_id):
    """AJAX endpoint to get purchase order items for a given purchase order"""
    try:
        purchase_order = get_object_or_404(PurchaseOrder, pk=purchase_order_id)
        items = purchase_order.items.all().select_related('product')
        
        items_data = []
        for item in items:
            remaining_qty = item.get_remaining_quantity()
            items_data.append({
                'id': item.id,
                'product_name': item.product.name,
                'ordered_quantity': str(item.quantity),
                'received_quantity': str(item.get_received_quantity()),
                'remaining_quantity': str(remaining_qty),
                'unit_price': str(item.unit_price),
                'unit_type': item.product.unit_type.code if item.product.unit_type else '',
            })
        
        return JsonResponse({
            'success': True,
            'items': items_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
