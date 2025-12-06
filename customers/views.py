from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Sum
from decimal import Decimal
from django.http import HttpResponse
from django.template.loader import get_template
from .models import Customer, CustomerLedger, CustomerCommitment
from .forms import CustomerForm, CustomerLedgerForm, CustomerCommitmentForm, SetOpeningBalanceForm
from sales.models import SalesOrder
from core.utils import get_company_info


class CustomerListView(ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    
    def get_queryset(self):
        qs = Customer.objects.all()
        # Status filter
        status = self.request.GET.get('status')
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        
        # Search by name / phone
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(contact_person__icontains=search)
            )
        return qs.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customers = self.get_queryset()
        
        total_receivable = sum(customer.current_balance for customer in customers if customer.current_balance > 0)
        total_payable = sum(abs(customer.current_balance) for customer in customers if customer.current_balance < 0)
        active_customers = customers.filter(is_active=True).count()
        
        context.update({
            'total_receivable': total_receivable,
            'total_payable': total_payable,
            'active_customers': active_customers,
            'current_status': self.request.GET.get('status', ''),
            'current_search': self.request.GET.get('search', ''),
        })
        return context


class CustomerDetailView(DetailView):
    model = Customer
    template_name = 'customers/customer_detail.html'


class CustomerCreateView(CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customers:customer_list')


class CustomerUpdateView(UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customers:customer_list')


class CustomerDeleteView(DeleteView):
    model = Customer
    template_name = 'customers/customer_confirm_delete.html'
    success_url = reverse_lazy('customers:customer_list')


class CustomerLedgerListView(ListView):
    model = CustomerLedger
    template_name = 'customers/ledger_list.html'
    context_object_name = 'items'
    paginate_by = 20
    
    def get_queryset(self):
        """Return ordered queryset to avoid pagination warning"""
        return CustomerLedger.objects.select_related('customer', 'created_by').order_by('-transaction_date', '-id')


class CustomerLedgerDetailView(DetailView):
    model = Customer
    template_name = 'customers/customer_ledger_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.get_object()
        transactions = []
        
        # Note: Sales orders are tracked via CustomerLedger entries (created automatically)
        # when sales orders are created, so we don't need to add them separately here
        
        # Ledger Entries (includes sales orders, payments, opening balances, etc.)
        ledger_entries = CustomerLedger.objects.filter(customer=customer).order_by('-transaction_date')
        for entry in ledger_entries:
            if entry.transaction_type == 'sale':
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
        running_balance = Decimal('0.00')
        for transaction in reversed(transactions):
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
        
        context.update({
            'transactions': transactions,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'opening_balance': actual_opening_balance,
            'current_balance': current_balance,
        })
        
        return context


class CustomerLedgerCreateView(CreateView):
    model = CustomerLedger
    form_class = CustomerLedgerForm
    template_name = 'customers/ledger_form.html'
    
    def get_success_url(self):
        return reverse_lazy('customers:customer_ledger_detail', kwargs={'pk': self.kwargs['pk']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer_id'] = self.kwargs['pk']
        return context
    
    def form_valid(self, form):
        form.instance.customer_id = self.kwargs['pk']
        form.instance.created_by = self.request.user
        
        # Save the ledger entry first
        response = super().form_valid(form)
        
        # Update customer balance
        customer = form.instance.customer
        self.update_customer_balance(customer)
        
        # Add success message
        messages.success(
            self.request, 
            f'Ledger entry created successfully for {customer.name}. '
            f'New balance: ৳{customer.current_balance}'
        )
        
        return response
    
    def update_customer_balance(self, customer):
        """Update customer current balance based on all ledger entries"""
        from decimal import Decimal
        
        # Get all ledger entries for this customer
        ledger_entries = CustomerLedger.objects.filter(customer=customer)
        
        total_balance = Decimal('0.00')
        for entry in ledger_entries:
            if entry.transaction_type in ['sale', 'opening_balance']:
                # These increase the balance (debit)
                total_balance += entry.amount
            elif entry.transaction_type in ['payment', 'return']:
                # These decrease the balance (credit)
                total_balance -= entry.amount
            elif entry.transaction_type == 'adjustment':
                # Adjustments can be positive or negative
                total_balance += entry.amount
        
        # Update customer balance
        customer.current_balance = total_balance
        customer.save()




class CustomerCommitmentListView(ListView):
    model = CustomerCommitment
    template_name = 'customers/commitment_list.html'
    context_object_name = 'items'


class CustomerCommitmentCreateView(CreateView):
    model = CustomerCommitment
    form_class = CustomerCommitmentForm
    template_name = 'customers/commitment_form.html'
    success_url = reverse_lazy('customers:commitment_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customers'] = Customer.objects.all()
        return context


class CustomerCommitmentUpdateView(UpdateView):
    model = CustomerCommitment
    form_class = CustomerCommitmentForm
    template_name = 'customers/commitment_form.html'
    success_url = reverse_lazy('customers:commitment_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customers'] = Customer.objects.all()
        return context


class CustomerCommitmentDeleteView(DeleteView):
    model = CustomerCommitment
    template_name = 'customers/commitment_confirm_delete.html'
    success_url = reverse_lazy('customers:commitment_list')


def set_opening_balance(request, pk):
    """Set opening balance for a customer"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        form = SetOpeningBalanceForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            customer.set_opening_balance(amount, user=request.user)
            messages.success(request, f'Opening balance set to ৳{amount} for {customer.name}')
            return redirect('customers:customer_ledger_detail', pk=customer.pk)
    else:
        form = SetOpeningBalanceForm()
    
    return render(request, 'customers/set_opening_balance.html', {
        'customer': customer,
        'form': form
    })


def customer_ledger_pdf(request, pk):
    """Generate PDF report for customer ledger"""
    try:
        customer = get_object_or_404(Customer, pk=pk)
        transactions = []
        
        # Note: Sales orders are tracked via CustomerLedger entries (created automatically)
        # when sales orders are created, so we don't need to add them separately here
        
        # Ledger Entries (includes sales orders, payments, opening balances, etc.)
        ledger_entries = CustomerLedger.objects.filter(customer=customer).order_by('-transaction_date')
        for entry in ledger_entries:
            if entry.transaction_type == 'sale':
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
        running_balance = Decimal('0.00')
        for transaction in reversed(transactions):
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
        
        # Get template
        template = get_template('customers/ledger_pdf.html')
        
        # Prepare context
        company_info = get_company_info()
        context = {
            'customer': customer,
            'transactions': transactions,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'opening_balance': actual_opening_balance,
            'current_balance': current_balance,
            **company_info,  # Unpack company info into context
        }
        
        # Render HTML
        html = template.render(context)
        
        # Return HTML response (can be printed as PDF)
        return HttpResponse(html, content_type='text/html')
        
    except Exception as e:
        messages.error(request, f"Error generating ledger report: {str(e)}")
        return redirect('customers:customer_ledger_detail', pk=pk)
