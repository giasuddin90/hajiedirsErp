from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Sum
from django.utils import timezone
from django.contrib import messages
from decimal import Decimal
from .models import Supplier, SupplierLedger
from .forms import SupplierForm, SupplierLedgerForm, SetOpeningBalanceForm
from purchases.models import PurchaseOrder


class SupplierListView(ListView):
    model = Supplier
    template_name = 'suppliers/supplier_list.html'
    context_object_name = 'suppliers'
    
    def get_queryset(self):
        """Filter suppliers based on search query and status"""
        queryset = Supplier.objects.all()
        
        # Get filter parameters from request
        search = self.request.GET.get('search', '').strip()
        status = self.request.GET.get('status', '')
        
        # Apply search filter
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(contact_person__icontains=search)
            )
        
        # Apply status filter
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Order by name
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        suppliers = self.get_queryset()
        
        # Calculate total payable amount (positive balances = you owe money)
        total_payable = sum(supplier.current_balance for supplier in suppliers if supplier.current_balance > 0)
        
        # Calculate total receivable amount (negative balances = they owe you money)
        total_receivable = sum(abs(supplier.current_balance) for supplier in suppliers if supplier.current_balance < 0)
        
        # Count active suppliers
        active_suppliers = suppliers.filter(is_active=True).count()
        
        # Get current filter values for form
        context.update({
            'total_payable': total_payable,
            'total_receivable': total_receivable,
            'active_suppliers': active_suppliers,
            'current_search': self.request.GET.get('search', ''),
            'current_status': self.request.GET.get('status', ''),
        })
        
        return context


class SupplierDetailView(DetailView):
    model = Supplier
    template_name = 'suppliers/supplier_detail.html'


class SupplierCreateView(CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'suppliers/supplier_form.html'
    success_url = reverse_lazy('suppliers:supplier_list')


class SupplierUpdateView(UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'suppliers/supplier_form.html'
    success_url = reverse_lazy('suppliers:supplier_list')


class SupplierDeleteView(DeleteView):
    model = Supplier
    template_name = 'suppliers/supplier_confirm_delete.html'
    success_url = reverse_lazy('suppliers:supplier_list')


class SupplierLedgerListView(ListView):
    model = SupplierLedger
    template_name = 'suppliers/ledger_list.html'
    context_object_name = 'items'


class SupplierLedgerCreateView(CreateView):
    model = SupplierLedger
    form_class = SupplierLedgerForm
    template_name = 'suppliers/ledger_form.html'
    
    def get_success_url(self):
        return reverse_lazy('suppliers:supplier_ledger_detail', kwargs={'pk': self.kwargs['supplier_id']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['supplier_id'] = self.kwargs['supplier_id']
        return context
    
    def form_valid(self, form):
        form.instance.supplier_id = self.kwargs['supplier_id']
        form.instance.created_by = self.request.user
        return super().form_valid(form)




class SupplierLedgerDetailView(DetailView):
    model = Supplier
    template_name = 'suppliers/supplier_ledger_detail.html'
    context_object_name = 'supplier'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        supplier = self.get_object()
        
        # Get all transactions for this supplier
        transactions = []
        
        # Purchase Orders
        purchase_orders = PurchaseOrder.objects.filter(supplier=supplier).exclude(status="canceled").order_by('-order_date')
        for po in purchase_orders:
            transactions.append({
                'date': po.order_date,
                'type': 'Purchase Order',
                'reference': f"PO-{po.order_number}",
                'description': f"Purchase Order - {po.supplier.name}",
                'debit': po.total_amount,
                'credit': Decimal('0.00'),
                'status': po.status,
                'created_at': po.created_at,
            })
        
        # No purchase invoices, payments, or returns in simplified model
        
        # Manual Ledger Entries
        ledger_entries = SupplierLedger.objects.filter(supplier=supplier).order_by('-transaction_date')
        for entry in ledger_entries:
            if entry.transaction_type == 'purchase':
                debit = entry.amount
                credit = Decimal('0.00')
            elif entry.transaction_type == 'payment':
                debit = Decimal('0.00')
                credit = entry.amount
            elif entry.transaction_type == 'opening_balance':
                debit = entry.amount if entry.amount > 0 else Decimal('0.00')
                credit = abs(entry.amount) if entry.amount < 0 else Decimal('0.00')
            else:
                debit = entry.amount if entry.amount > 0 else Decimal('0.00')
                credit = abs(entry.amount) if entry.amount < 0 else Decimal('0.00')
            
            transactions.append({
                'date': entry.transaction_date.date(),
                'type': entry.get_transaction_type_display(),
                'reference': entry.reference or f"LED-{entry.id}",
                'description': entry.description,
                'debit': debit,
                'credit': credit,
                'status': 'manual',
                'created_at': entry.created_at,
                'payment_method': entry.payment_method,
            })
        
        # Sort all transactions by date (newest first)
        transactions.sort(key=lambda x: x['date'], reverse=True)
        
        # Calculate running balance
        running_balance = Decimal('0.00')  # Start from zero
        for transaction in reversed(transactions):  # Process oldest first for balance calculation
            running_balance += transaction['debit'] - transaction['credit']
            transaction['balance'] = running_balance
        
        # Reverse to show newest first
        transactions.reverse()
        
        # Calculate totals
        total_debit = sum(t['debit'] for t in transactions)
        total_credit = sum(t['credit'] for t in transactions)
        current_balance = total_debit - total_credit
        
        # Calculate actual opening balance from ledger entries
        opening_balance_entry = next((t for t in transactions if t['type'] == 'Opening Balance'), None)
        if opening_balance_entry:
            actual_opening_balance = opening_balance_entry['debit'] - opening_balance_entry['credit']
        else:
            actual_opening_balance = Decimal('0.00')
        
        # Debug information
        debug_info = {
            'supplier_opening_balance': supplier.opening_balance,
            'total_transactions': len(transactions),
            'purchase_orders_count': len([t for t in transactions if t['type'] == 'Purchase Order']),
            'opening_balance_entries': len([t for t in transactions if t['type'] == 'Opening Balance']),
        }
        
        context.update({
            'transactions': transactions,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'opening_balance': actual_opening_balance,
            'current_balance': current_balance,
            'debug_info': debug_info,
        })
        
        return context


def set_opening_balance(request, pk):
    """Set opening balance for a supplier"""
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        form = SetOpeningBalanceForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            supplier.set_opening_balance(amount, user=request.user)
            messages.success(request, f'Opening balance set to ৳{amount} for {supplier.name}')
            return redirect('suppliers:supplier_ledger_detail', pk=supplier.pk)
    else:
        form = SetOpeningBalanceForm()
    
    return render(request, 'suppliers/set_opening_balance.html', {
        'supplier': supplier,
        'form': form
    })
