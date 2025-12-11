from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.template.loader import get_template
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import os
from .models import (
    SalesOrder, SalesOrderItem
)
from .forms import SalesOrderForm, SalesOrderItemFormSet, SalesOrderItemFormSetCustom, InstantSalesForm
from customers.models import Customer, CustomerLedger
from stock.models import Product, ProductCategory, ProductBrand, Warehouse
from django.contrib.auth.models import User
from core.utils import get_company_info
import uuid


def generate_invoice_description(order):
    """
    Generate full invoice description for customer ledger entry
    Includes all products, quantities, prices, delivery charges, and transportation cost
    """
    description_parts = []
    description_parts.append(f"{order.order_number} | {order.order_date.strftime('%Y-%m-%d')}")
    
    # Add products
    for item in order.items.all():
        product_line = f"{item.product.name} - {item.quantity} {item.product.unit_type} @ ৳{item.unit_price:.2f} = ৳{item.total_price:.2f}"
        
        # Add tile information if applicable
        if item.product.category and item.product.category.name.lower() == 'tiles':
            pcs_per_carton = item.product.pcs_per_carton or 0
            sqft_per_pcs = item.product.sqft_per_pcs or Decimal('0')
            if sqft_per_pcs > 0 and pcs_per_carton > 0:
                unit_code = item.product.unit_type.code.lower() if item.product.unit_type else ''
                if unit_code == 'sqft':
                    total_sqft = item.quantity
                    total_pieces = total_sqft / sqft_per_pcs
                else:
                    total_pieces = item.quantity
                    total_sqft = total_pieces * sqft_per_pcs
                
                cartons = int(total_pieces // pcs_per_carton)
                remaining_pieces = int(total_pieces % pcs_per_carton)
                
                product_line += f" ({int(total_sqft)} sqft, {cartons} carton"
                if remaining_pieces > 0:
                    product_line += f" {remaining_pieces} pcs"
                product_line += ")"
        
        description_parts.append(product_line)
    
    # Calculate subtotal and charges
    subtotal = sum(item.total_price for item in order.items.all())
    # Use stored delivery_charges from order, or calculate if not set
    delivery_charges = order.delivery_charges or Decimal('0')
    if delivery_charges == 0:
        # Calculate if not manually set
        for item in order.items.all():
            delivery_charge_per_unit = item.product.delivery_charge_per_unit or Decimal('0')
            delivery_charges += item.quantity * delivery_charge_per_unit
    
    transportation_cost = order.transportation_cost or Decimal('0')
    total_amount = subtotal + delivery_charges + transportation_cost
    
    # Add cost breakdown
    description_parts.append(f"Subtotal: ৳{subtotal:.2f}")
    if delivery_charges > 0:
        description_parts.append(f"Delivery: ৳{delivery_charges:.2f}")
    if transportation_cost > 0:
        description_parts.append(f"Transport: ৳{transportation_cost:.2f}")
    description_parts.append(f"Total: ৳{total_amount:.2f}")
    
    # Add notes if any
    if order.notes:
        description_parts.append(f"Notes: {order.notes}")
    
    return "\n".join(description_parts)


def create_customer_ledger_entry(order, user=None, update_existing=False):
    """
    Create or update customer ledger entry for sales order with full invoice details
    """
    if not order.customer:
        return None
    
    # Generate full invoice description
    description = generate_invoice_description(order)
    
    # Check if ledger entry already exists for this order
    existing_entry = None
    if update_existing:
        existing_entry = CustomerLedger.objects.filter(
            customer=order.customer,
            reference=order.order_number,
            transaction_type='sale'
        ).first()
    
    if existing_entry:
        # Update existing entry
        old_amount = existing_entry.amount
        existing_entry.amount = order.total_amount
        existing_entry.description = description
        existing_entry.transaction_date = timezone.now()
        existing_entry.save()
        
        # Update customer balance (remove old amount, add new amount)
        order.customer.current_balance = order.customer.current_balance - old_amount + order.total_amount
        order.customer.save()
        
        return existing_entry
    else:
        # Create new ledger entry
        ledger_entry = CustomerLedger.objects.create(
            customer=order.customer,
            transaction_type='sale',
            amount=order.total_amount,
            description=description,
            reference=order.order_number,
            transaction_date=timezone.now(),
            created_by=user or order.created_by
        )
        
        # Update customer balance
        order.customer.current_balance += order.total_amount
        order.customer.save()
        
        return ledger_entry


def create_or_update_deposit_ledger_entry(order, deposit_amount, user=None, update_existing=False):
    """
    Create or update customer ledger entry for customer deposit payment
    """
    if not order.customer or not deposit_amount or deposit_amount <= 0:
        return None
    
    # Check if deposit ledger entry already exists for this order
    existing_entry = None
    if update_existing:
        existing_entry = CustomerLedger.objects.filter(
            customer=order.customer,
            reference=f"{order.order_number}-DEPOSIT",
            transaction_type='payment'
        ).first()
    
    description = f"Deposit/Advance payment for Sales Order {order.order_number}"
    
    if existing_entry:
        # Update existing entry
        old_amount = existing_entry.amount
        existing_entry.amount = deposit_amount
        existing_entry.description = description
        existing_entry.transaction_date = timezone.now()
        existing_entry.save()
        
        # Update customer balance (remove old amount, add new amount)
        # Payment reduces customer balance (credit)
        order.customer.current_balance = order.customer.current_balance + old_amount - deposit_amount
        order.customer.save()
        
        return existing_entry
    else:
        # Create new ledger entry
        ledger_entry = CustomerLedger.objects.create(
            customer=order.customer,
            transaction_type='payment',
            amount=deposit_amount,
            description=description,
            reference=f"{order.order_number}-DEPOSIT",
            transaction_date=timezone.now(),
            created_by=user or order.created_by
        )
        
        # Update customer balance (payment reduces balance - credit)
        order.customer.current_balance -= deposit_amount
        order.customer.save()
        
        return ledger_entry


class SalesOrderListView(ListView):
    model = SalesOrder
    template_name = 'sales/order_list.html'
    context_object_name = 'orders'


class SalesOrderDetailView(DetailView):
    model = SalesOrder
    template_name = 'sales/order_detail.html'


class SalesOrderCreateView(CreateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'sales/order_form.html'
    success_url = reverse_lazy('sales:order_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Create formset for order items
        if self.request.POST:
            context['formset'] = SalesOrderItemFormSetCustom(self.request.POST)
        else:
            context['formset'] = SalesOrderItemFormSetCustom()
        
        # Add data for filtering
        context['products'] = Product.objects.filter(is_active=True).select_related('category', 'brand')
        context['categories'] = ProductCategory.objects.filter(is_active=True)
        context['brands'] = ProductBrand.objects.filter(is_active=True)
        context['warehouses'] = Warehouse.objects.filter(is_active=True).order_by('name')
        
        return context
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Generate unique order number
                order_number = f"SO-{uuid.uuid4().hex[:8].upper()}"
                form.instance.order_number = order_number
                form.instance.created_by = self.request.user
                
                # Save the order first
                response = super().form_valid(form)
                
                # Handle formset - now we have self.object
                formset = SalesOrderItemFormSetCustom(self.request.POST, instance=self.object)
                
                # Validate formset
                if formset.is_valid():
                    formset.save()
                    
                    # Calculate total amount (subtotal + delivery charges + transportation cost)
                    subtotal = sum(item.total_price for item in self.object.items.all())
                    
                    # Get form's delivery_charges value (always use form value if provided, even if 0)
                    form_delivery_charges = form.cleaned_data.get('delivery_charges')
                    
                    # If form value is None or not provided, calculate automatically
                    if form_delivery_charges is None:
                        # Calculate delivery charges automatically
                        delivery_charges = Decimal('0')
                        for item in self.object.items.all():
                            delivery_charge_per_unit = item.product.delivery_charge_per_unit or Decimal('0')
                            delivery_charges += item.quantity * delivery_charge_per_unit
                    else:
                        # Use form value (respects manual input, even if 0)
                        delivery_charges = form_delivery_charges
                    
                    # Save delivery charges value
                    self.object.delivery_charges = delivery_charges
                    
                    # Get transportation cost
                    transportation_cost = self.object.transportation_cost or Decimal('0')
                    
                    # Get customer deposit
                    customer_deposit = form.cleaned_data.get('customer_deposit') or Decimal('0')
                    self.object.customer_deposit = customer_deposit
                    
                    # Total amount
                    total_amount = subtotal + delivery_charges + transportation_cost
                    self.object.total_amount = total_amount
                    self.object.save()
                    
                    # Create customer ledger entry with full invoice details
                    if self.object.customer:
                        create_customer_ledger_entry(self.object, self.request.user)
                        # Create deposit ledger entry if deposit amount > 0
                        if customer_deposit > 0:
                            create_or_update_deposit_ledger_entry(self.object, customer_deposit, self.request.user)
                    
                    items_count = self.object.items.count()
                    if items_count > 0:
                        messages.success(self.request, f"Sales order {order_number} created successfully with {items_count} products! Total: ৳{total_amount}")
                    else:
                        messages.warning(self.request, f"Sales order {order_number} created without items. Please add products to complete the order.")
                else:
                    # Show detailed formset errors
                    error_messages = []
                    for idx, form_item in enumerate(formset.forms):
                        if form_item.errors:
                            for field, errors in form_item.errors.items():
                                for error in errors:
                                    error_messages.append(f"Product {idx + 1} - {field}: {error}")
                    
                    if formset.non_form_errors():
                        for error in formset.non_form_errors():
                            error_messages.append(str(error))
                    
                    if error_messages:
                        messages.error(self.request, "Please fix the following errors:\n" + "\n".join(error_messages))
                    else:
                        messages.error(self.request, "Please add at least one product to the order.")
                    
                    # Return form_invalid to show errors
                    return self.form_invalid(form)
                
                return response
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            error_msg = f"Error creating sales order: {str(e)}"
            messages.error(self.request, error_msg)
            # Log the full error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Sales order creation error: {error_details}")
            print(f"ERROR: {error_details}")  # Also print for immediate debugging
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle invalid form submission with better error display"""
        # Re-create formset with errors
        # For new orders, object might not exist yet
        instance = None
        if hasattr(self, 'object') and self.object:
            instance = self.object
        
        if self.request.POST:
            formset = SalesOrderItemFormSetCustom(self.request.POST, instance=instance)
        else:
            formset = SalesOrderItemFormSetCustom(instance=instance)
        
        # Add formset to context
        context = self.get_context_data(form=form)
        context['formset'] = formset
        
        # Print errors for debugging
        print(f"DEBUG: Form errors: {form.errors}")
        print(f"DEBUG: Formset errors: {formset.errors}")
        if formset.non_form_errors():
            print(f"DEBUG: Formset non-form errors: {formset.non_form_errors()}")
        
        return self.render_to_response(context)


class SalesOrderUpdateView(UpdateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'sales/order_form.html'
    success_url = reverse_lazy('sales:order_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Create formset for order items
        if self.request.POST:
            context['formset'] = SalesOrderItemFormSet(self.request.POST, instance=self.object)
        else:
            # For editing, only show existing items, no extra blank forms
            context['formset'] = SalesOrderItemFormSet(instance=self.object)
        
        # Add data for filtering
        context['products'] = Product.objects.filter(is_active=True).select_related('category', 'brand')
        context['categories'] = ProductCategory.objects.filter(is_active=True)
        context['brands'] = ProductBrand.objects.filter(is_active=True)
        context['warehouses'] = Warehouse.objects.filter(is_active=True).order_by('name')
        
        return context
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Save the order
                response = super().form_valid(form)
                
                # Handle formset
                formset = SalesOrderItemFormSet(self.request.POST, instance=self.object)
                if formset.is_valid():
                    formset.save()
                    
                    # Calculate total amount (subtotal + delivery charges + transportation cost)
                    subtotal = sum(item.total_price for item in self.object.items.all())
                    
                    # Always use form's delivery_charges value (respects manual input, even if 0)
                    delivery_charges = form.cleaned_data.get('delivery_charges', self.object.delivery_charges or Decimal('0'))
                    
                    # Save delivery charges value
                    self.object.delivery_charges = delivery_charges
                    
                    # Get transportation cost
                    transportation_cost = self.object.transportation_cost or Decimal('0')
                    
                    # Get customer deposit (handle both new and existing deposits)
                    old_deposit = self.object.customer_deposit or Decimal('0')
                    new_deposit = form.cleaned_data.get('customer_deposit') or Decimal('0')
                    self.object.customer_deposit = new_deposit
                    
                    # Total amount
                    total_amount = subtotal + delivery_charges + transportation_cost
                    self.object.total_amount = total_amount
                    self.object.save()
                    
                    # Update customer ledger entry with full invoice details
                    if self.object.customer:
                        create_customer_ledger_entry(self.object, self.request.user, update_existing=True)
                        # Handle deposit ledger entry
                        if new_deposit > 0:
                            # Create or update deposit ledger entry
                            create_or_update_deposit_ledger_entry(self.object, new_deposit, self.request.user, update_existing=True)
                        elif old_deposit > 0 and new_deposit == 0:
                            # If deposit was removed, delete the deposit ledger entry and reverse the balance
                            existing_deposit_entry = CustomerLedger.objects.filter(
                                customer=self.object.customer,
                                reference=f"{self.object.order_number}-DEPOSIT",
                                transaction_type='payment'
                            ).first()
                            if existing_deposit_entry:
                                # Reverse the balance change
                                self.object.customer.current_balance += old_deposit
                                self.object.customer.save()
                                existing_deposit_entry.delete()
                    
                    items_count = self.object.items.count()
                    messages.success(self.request, f"Sales order {self.object.order_number} updated successfully with {items_count} products! Total: ৳{total_amount}")
                else:
                    messages.error(self.request, "Please fix the errors in the product selection.")
                    return self.form_invalid(form)
                
                return response
                
        except Exception as e:
            messages.error(self.request, f"Error updating sales order: {str(e)}")
            return self.form_invalid(form)


class SalesOrderDeleteView(DeleteView):
    model = SalesOrder
    template_name = 'sales/order_confirm_delete.html'
    success_url = reverse_lazy('sales:order_list')




class SalesDailyReportView(ListView):
    model = SalesOrder
    template_name = 'sales/sales_daily_report.html'
    context_object_name = 'reports'
    
    def get_queryset(self):
        from django.utils import timezone
        today = timezone.now().date()
        return SalesOrder.objects.filter(order_date=today)


class SalesMonthlyReportView(ListView):
    model = SalesOrder
    template_name = 'sales/sales_monthly_report.html'
    context_object_name = 'reports'
    
    def get_queryset(self):
        from django.utils import timezone
        now = timezone.now()
        return SalesOrder.objects.filter(
            order_date__year=now.year,
            order_date__month=now.month
        )


class SalesCustomerReportView(ListView):
    model = SalesOrder
    template_name = 'sales/sales_customer_report.html'
    context_object_name = 'reports'




def mark_order_delivered(request, order_id):
    """Mark sales order as delivered"""
    try:
        with transaction.atomic():
            order = get_object_or_404(SalesOrder, id=order_id)
            
            if order.status != 'order':
                messages.error(request, f"Order {order.order_number} cannot be marked as delivered. Current status: {order.get_status_display()}")
                return redirect('sales:order_detail', order_id)
            
            order.mark_delivered(user=request.user)
            messages.success(request, f"Order {order.order_number} marked as delivered successfully!")
            
    except Exception as e:
        messages.error(request, f"Error marking order as delivered: {str(e)}")
    
    return redirect('sales:order_detail', order_id)


def cancel_sales_order(request, order_id):
    """Cancel sales order"""
    try:
        with transaction.atomic():
            order = get_object_or_404(SalesOrder, id=order_id)
            
            if order.status == 'cancel':
                messages.warning(request, f"Order {order.order_number} is already cancelled.")
                return redirect('sales:order_detail', order_id)
            
            order.cancel_order(user=request.user)
            messages.success(request, f"Order {order.order_number} cancelled successfully!")
            
    except Exception as e:
        messages.error(request, f"Error cancelling order: {str(e)}")
    
    return redirect('sales:order_detail', order_id)


def sales_order_invoice(request, order_id):
    """Generate PDF invoice for sales order"""
    try:
        order = get_object_or_404(SalesOrder, id=order_id)
        
        # Calculate subtotal (products only)
        subtotal = sum(item.total_price for item in order.items.all())
        
        # Use stored delivery_charges from order (respects manual 0 if set)
        delivery_charges = order.delivery_charges or Decimal('0')
        items_with_delivery = []
        items_with_tile_info = []
        
        # Calculate delivery charges per item for display
        calculated_delivery_charges = Decimal('0')
        for item in order.items.all():
            delivery_charge_per_unit = item.product.delivery_charge_per_unit or Decimal('0')
            item_delivery_charge = item.quantity * delivery_charge_per_unit
            calculated_delivery_charges += item_delivery_charge
            items_with_delivery.append({
                'item': item,
                'delivery_charge_per_unit': delivery_charge_per_unit,
                'delivery_charge_total': item_delivery_charge,
            })
            
            # Calculate tile information if category is "Tiles"
            tile_info = None
            if item.product.category and item.product.category.name.lower() == 'tiles':
                pcs_per_carton = item.product.pcs_per_carton or 0
                sqft_per_pcs = item.product.sqft_per_pcs or Decimal('0')
                
                if sqft_per_pcs > 0 and pcs_per_carton > 0:
                    # Check if quantity is in sqft or pieces based on unit type
                    unit_code = item.product.unit_type.code.lower() if item.product.unit_type else ''
                    
                    if unit_code == 'sqft':
                        # Quantity is in sqft
                        total_sqft = item.quantity
                        total_pieces = total_sqft / sqft_per_pcs
                    else:
                        # Quantity is in pieces, calculate sqft
                        total_pieces = item.quantity
                        total_sqft = total_pieces * sqft_per_pcs
                    
                    # Calculate cartons and remaining pieces
                    cartons = int(total_pieces // pcs_per_carton)
                    remaining_pieces = int(total_pieces % pcs_per_carton)
                    
                    tile_info = {
                        'total_sqft': total_sqft,
                        'cartons': cartons,
                        'pieces': remaining_pieces,
                    }
            
            items_with_tile_info.append({
                'item': item,
                'tile_info': tile_info,
            })
        
        # Use manual delivery charges if set (even if 0), otherwise use calculated
        if delivery_charges == 0 and order.delivery_charges is None:
            delivery_charges = calculated_delivery_charges
        
        # Get transportation cost
        transportation_cost = order.transportation_cost or Decimal('0')
        
        # Get template
        template = get_template('sales/invoice_pdf.html')
        
        # Prepare context
        company_info = get_company_info()
        context = {
            'order': order,
            'items': order.items.all(),
            'items_with_tile_info': items_with_tile_info,
            'items_with_delivery': items_with_delivery,
            'subtotal': subtotal,
            'delivery_charges': delivery_charges,
            'transportation_cost': transportation_cost,
            **company_info,  # Unpack company info into context
        }
        
        # Render HTML
        html = template.render(context)
        
        # For now, return HTML response (can be enhanced with PDF generation later)
        return HttpResponse(html, content_type='text/html')
        
    except Exception as e:
        messages.error(request, f"Error generating invoice: {str(e)}")
        return redirect('sales:order_detail', order_id)


def labour_chalan(request, order_id):
    """Generate labour chalan PDF for sales order (no cost calculations)"""
    try:
        order = get_object_or_404(SalesOrder, id=order_id)
        
        items_with_tile_info = []
        
        # Prepare items with tile information (if applicable)
        for item in order.items.all():
            # Calculate tile information if category is "Tiles"
            tile_info = None
            if item.product.category and item.product.category.name.lower() == 'tiles':
                pcs_per_carton = item.product.pcs_per_carton or 0
                sqft_per_pcs = item.product.sqft_per_pcs or Decimal('0')
                
                if sqft_per_pcs > 0 and pcs_per_carton > 0:
                    # Check if quantity is in sqft or pieces based on unit type
                    unit_code = item.product.unit_type.code.lower() if item.product.unit_type else ''
                    
                    if unit_code == 'sqft':
                        # Quantity is in sqft
                        total_sqft = item.quantity
                        total_pieces = total_sqft / sqft_per_pcs
                    else:
                        # Quantity is in pieces, calculate sqft
                        total_pieces = item.quantity
                        total_sqft = total_pieces * sqft_per_pcs
                    
                    # Calculate cartons and remaining pieces
                    cartons = int(total_pieces // pcs_per_carton)
                    remaining_pieces = int(total_pieces % pcs_per_carton)
                    
                    tile_info = {
                        'total_sqft': total_sqft,
                        'cartons': cartons,
                        'pieces': remaining_pieces,
                    }
            
            items_with_tile_info.append({
                'item': item,
                'tile_info': tile_info,
            })
        
        # Get template
        template = get_template('sales/labour_chalan.html')
        
        # Prepare context (no cost information)
        company_info = get_company_info()
        context = {
            'order': order,
            'items': order.items.all(),
            'items_with_tile_info': items_with_tile_info,
            **company_info,  # Unpack company info into context
        }
        
        # Render HTML
        html = template.render(context)
        
        # For now, return HTML response (can be enhanced with PDF generation later)
        return HttpResponse(html, content_type='text/html')
        
    except Exception as e:
        messages.error(request, f"Error generating labour chalan: {str(e)}")
        return redirect('sales:order_detail', order_id)


class InstantSalesCreateView(CreateView):
    """View for creating instant sales"""
    model = SalesOrder
    form_class = InstantSalesForm
    template_name = 'sales/instant_sales_form.html'
    success_url = reverse_lazy('sales:order_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Create formset for order items
        if self.request.POST:
            context['formset'] = SalesOrderItemFormSetCustom(self.request.POST, instance=self.object)
        else:
            # For GET requests, create formset without instance (new order)
            context['formset'] = SalesOrderItemFormSetCustom()
        
        # Add data for filtering
        context['products'] = Product.objects.filter(is_active=True).select_related('category', 'brand')
        context['categories'] = ProductCategory.objects.filter(is_active=True)
        context['brands'] = ProductBrand.objects.filter(is_active=True)
        
        return context
    
    def form_valid(self, form):
        try:
            print(f"DEBUG: Form is valid, data: {form.cleaned_data}")
            print(f"DEBUG: POST data: {self.request.POST}")
            
            with transaction.atomic():
                # Generate unique order number
                order_number = f"IS-{uuid.uuid4().hex[:8].upper()}"
                form.instance.order_number = order_number
                form.instance.sales_type = 'instant'
                form.instance.status = 'delivered'  # Instant sales are immediately delivered
                form.instance.created_by = self.request.user
                
                # Save the order first
                self.object = form.save()
                print(f"DEBUG: Order saved with ID: {self.object.id}")
                
                # Handle formset - create with the saved instance
                formset = SalesOrderItemFormSetCustom(self.request.POST, instance=self.object)
                print(f"DEBUG: Formset is_valid: {formset.is_valid()}")
                print(f"DEBUG: Formset errors: {formset.errors}")
                
                if formset.is_valid():
                    formset.save()
                    print(f"DEBUG: Formset saved successfully")
                    
                    # Calculate total amount (subtotal + delivery charges + transportation cost)
                    subtotal = sum(item.total_price for item in self.object.items.all())
                    
                    # Use form's delivery_charges value (respects manual input, even if 0)
                    # For instant sales, calculate if not manually set
                    delivery_charges = self.object.delivery_charges or Decimal('0')
                    if delivery_charges == 0:
                        # Calculate delivery charges automatically
                        delivery_charges = Decimal('0')
                        for item in self.object.items.all():
                            delivery_charge_per_unit = item.product.delivery_charge_per_unit or Decimal('0')
                            delivery_charges += item.quantity * delivery_charge_per_unit
                    
                    # Save delivery charges value
                    self.object.delivery_charges = delivery_charges
                    
                    # Get transportation cost
                    transportation_cost = self.object.transportation_cost or Decimal('0')
                    
                    # Total amount
                    total_amount = subtotal + delivery_charges + transportation_cost
                    self.object.total_amount = total_amount
                    self.object.save()
                    print(f"DEBUG: Total amount set to: {total_amount}")
                    
                    # Create customer ledger entry with full invoice details
                    if self.object.customer:
                        create_customer_ledger_entry(self.object, self.request.user)
                    
                    # Inventory is calculated in real-time from sales orders
                    # Instant sales (sales_type='instant') are automatically included
                    # in the real-time inventory calculation, so no manual update needed
                    
                    # Low stock alerts are now calculated dynamically based on min_stock_level
                    # No need to create/store alerts - they're computed in real-time
                    
                    items_count = self.object.items.count()
                    print(f"DEBUG: Final items count: {items_count}")
                    if items_count > 0:
                        messages.success(self.request, f"Instant sale {order_number} completed successfully with {items_count} products! Total: ৳{total_amount}")
                    else:
                        messages.warning(self.request, f"Instant sale {order_number} created without items. Please add products to complete the sale.")
                else:
                    print(f"DEBUG: Formset validation failed: {formset.errors}")
                    messages.error(self.request, f"Please fix the errors in the product selection. Errors: {formset.errors}")
                    return self.form_invalid(form)
                
                # Return redirect response
                return redirect(self.success_url)
                
        except Exception as e:
            print(f"DEBUG: Exception occurred: {str(e)}")
            messages.error(self.request, f"Error creating instant sale: {str(e)}")
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        print(f"DEBUG: Form is invalid, errors: {form.errors}")
        if hasattr(self, 'object') and self.object:
            formset = SalesOrderItemFormSetCustom(self.request.POST, instance=self.object)
            print(f"DEBUG: Formset errors: {formset.errors}")
        return super().form_invalid(form)


class InstantSalesUpdateView(UpdateView):
    """View for editing instant sales"""
    model = SalesOrder
    form_class = InstantSalesForm
    template_name = 'sales/instant_sales_form.html'
    success_url = reverse_lazy('sales:order_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Create formset for order items
        if self.request.POST:
            context['formset'] = SalesOrderItemFormSet(self.request.POST, instance=self.object)
        else:
            # For editing, only show existing items, no extra blank forms
            context['formset'] = SalesOrderItemFormSet(instance=self.object)
        
        # Add data for filtering
        context['products'] = Product.objects.filter(is_active=True).select_related('category', 'brand')
        context['categories'] = ProductCategory.objects.filter(is_active=True)
        context['brands'] = ProductBrand.objects.filter(is_active=True)
        
        return context
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Ensure sales_type remains 'instant'
                form.instance.sales_type = 'instant'
                form.instance.status = 'delivered'  # Instant sales are immediately delivered
                
                # Save the order
                response = super().form_valid(form)
                
                # Handle formset
                formset = SalesOrderItemFormSet(self.request.POST, instance=self.object)
                if formset.is_valid():
                    formset.save()
                    
                    # Calculate total amount (subtotal + delivery charges + transportation cost)
                    subtotal = sum(item.total_price for item in self.object.items.all())
                    
                    # Always use form's delivery_charges value (respects manual input, even if 0)
                    delivery_charges = self.object.delivery_charges or Decimal('0')
                    
                    # Save delivery charges value
                    self.object.delivery_charges = delivery_charges
                    
                    # Get transportation cost
                    transportation_cost = self.object.transportation_cost or Decimal('0')
                    
                    # Total amount
                    total_amount = subtotal + delivery_charges + transportation_cost
                    self.object.total_amount = total_amount
                    self.object.save()
                    
                    # Update customer ledger entry with full invoice details
                    if self.object.customer:
                        create_customer_ledger_entry(self.object, self.request.user, update_existing=True)
                    
                    items_count = self.object.items.count()
                    messages.success(self.request, f"Instant sale {self.object.order_number} updated successfully with {items_count} products! Total: ৳{total_amount}")
                else:
                    messages.error(self.request, "Please fix the errors in the product selection.")
                    return self.form_invalid(form)
                
                return response
                
        except Exception as e:
            messages.error(self.request, f"Error updating instant sale: {str(e)}")
            return self.form_invalid(form)
