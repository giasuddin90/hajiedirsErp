from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Sum, Count, Q, Case, When, DecimalField
from django.utils import timezone
from datetime import datetime, timedelta
from customers.models import Customer, CustomerLedger
from suppliers.models import Supplier, SupplierLedger
from stock.models import Product, get_low_stock_products
from sales.models import SalesOrder
from purchases.models import PurchaseOrder
from expenses.models import Expense
from bankloan.models import CreditCardLoan
from .mixins import StaffRequiredMixin, AdminRequiredMixin
from .forms import StaffUserForm, StaffUserUpdateForm


class DashboardView(StaffRequiredMixin, TemplateView):
    template_name = 'dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Basic counts
        context['total_customers'] = Customer.objects.filter(is_active=True).count()
        context['total_suppliers'] = Supplier.objects.filter(is_active=True).count()
        context['total_products'] = Product.objects.filter(is_active=True).count()
        
        # Financial metrics
        today = timezone.now().date()
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        
        # Sales metrics
        monthly_sales = SalesOrder.objects.filter(
            status='delivered',
            order_date__gte=this_month_start
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        last_month_sales = SalesOrder.objects.filter(
            status='delivered',
            order_date__gte=last_month_start,
            order_date__lt=this_month_start
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        context['total_sales'] = monthly_sales
        context['sales_growth'] = self._calculate_growth_percentage(monthly_sales, last_month_sales)
        
        # Receivables calculation (positive customer balances)
        total_receivables = Customer.objects.filter(
            current_balance__gt=0
        ).aggregate(total=Sum('current_balance'))['total'] or 0
        context['total_receivables'] = total_receivables
        
        # Payables calculation (positive supplier balances)
        total_payables = Supplier.objects.filter(
            current_balance__gt=0
        ).aggregate(total=Sum('current_balance'))['total'] or 0
        context['total_payables'] = total_payables
        
        # Expenses calculation (current month)
        monthly_expenses = Expense.objects.filter(
            expense_date__gte=this_month_start
        ).aggregate(total=Sum('amount'))['total'] or 0
        context['total_expenses'] = monthly_expenses

        # Credit card loan metrics
        context['active_cc_loans'] = CreditCardLoan.objects.filter(status='active').count()
        closed_loans = CreditCardLoan.objects.filter(status='closed').annotate(
            total_paid=Sum(
                Case(
                    When(ledger_entries__entry_type='payment', then='ledger_entries__payment_amount'),
                    default=0,
                    output_field=DecimalField(),
                )
            ),
            total_disbursed=Sum(
                Case(
                    When(ledger_entries__entry_type='disbursement', then='ledger_entries__payment_amount'),
                    default=0,
                    output_field=DecimalField(),
                )
            ),
        )
        closed_interest_paid = sum(
            max((loan.total_paid or 0) - (loan.total_disbursed or 0), 0) for loan in closed_loans
        )
        context['closed_loan_interest_paid'] = closed_interest_paid
        
        # Purchase metrics - use GoodsReceipt instead of PurchaseOrder status
        from purchases.models import GoodsReceipt
        monthly_purchases = GoodsReceipt.objects.filter(
            status='received',
            receipt_date__gte=this_month_start
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        context['total_purchases'] = monthly_purchases
        
        # Profit margin calculation (simplified)
        gross_profit = monthly_sales - monthly_purchases
        profit_margin = (gross_profit / monthly_sales * 100) if monthly_sales > 0 else 0
        context['profit_margin'] = round(profit_margin, 2)
        
        # Recent activities
        context['recent_orders'] = SalesOrder.objects.select_related('customer').order_by('-created_at')[:5]
        context['recent_purchases'] = PurchaseOrder.objects.select_related('supplier').order_by('-created_at')[:5]
        
        # Low stock alerts (calculated dynamically)
        context['low_stock_alerts'] = get_low_stock_products()[:5]
        
        # Top customers by balance
        context['top_customers'] = Customer.objects.filter(
            current_balance__gt=0
        ).order_by('-current_balance')[:5]
        
        # Top suppliers by balance
        context['top_suppliers'] = Supplier.objects.filter(
            current_balance__gt=0
        ).order_by('-current_balance')[:5]
        
        # Sales trend data for charts
        context['sales_trend_data'] = self._get_sales_trend_data()
        context['monthly_comparison'] = self._get_monthly_comparison()
        
        return context
    
    def _calculate_growth_percentage(self, current, previous):
        """Calculate growth percentage"""
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 1)
    
    def _get_sales_trend_data(self):
        """Get sales data for the last 6 months"""
        today = timezone.now().date()
        months_data = []
        labels = []
        
        for i in range(6):
            month_start = today.replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            sales = SalesOrder.objects.filter(
                status='delivered',
                order_date__gte=month_start,
                order_date__lt=month_end
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            months_data.append(float(sales))
            labels.append(month_start.strftime('%b'))
        
        return {
            'labels': list(reversed(labels)),
            'data': list(reversed(months_data))
        }
    
    def _get_monthly_comparison(self):
        """Get current vs previous month comparison"""
        today = timezone.now().date()
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        
        this_month_sales = SalesOrder.objects.filter(
            status='delivered',
            order_date__gte=this_month_start
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        last_month_sales = SalesOrder.objects.filter(
            status='delivered',
            order_date__gte=last_month_start,
            order_date__lt=this_month_start
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        return {
            'current': float(this_month_sales),
            'previous': float(last_month_sales),
            'growth': self._calculate_growth_percentage(this_month_sales, last_month_sales)
        }


@login_required
def dashboard_redirect(request):
    """Redirect to dashboard after login"""
    closed_loans = CreditCardLoan.objects.filter(status='closed').annotate(
        total_paid=Sum(
            Case(
                When(ledger_entries__entry_type='payment', then='ledger_entries__payment_amount'),
                default=0,
                output_field=DecimalField(),
            )
        ),
        total_disbursed=Sum(
            Case(
                When(ledger_entries__entry_type='disbursement', then='ledger_entries__payment_amount'),
                default=0,
                output_field=DecimalField(),
            )
        ),
    )
    closed_interest_paid = sum(
        max((loan.total_paid or 0) - (loan.total_disbursed or 0), 0) for loan in closed_loans
    )
    return render(request, 'dashboard.html', {
        'total_customers': Customer.objects.filter(is_active=True).count(),
        'total_suppliers': Supplier.objects.filter(is_active=True).count(),
        'total_products': Product.objects.filter(is_active=True).count(),
        'total_sales': SalesOrder.objects.filter(status='delivered').aggregate(total=Sum('total_amount'))['total'] or 0,
        'recent_orders': SalesOrder.objects.select_related('customer').order_by('-created_at')[:5],
        'low_stock_alerts': get_low_stock_products()[:5],
        'active_cc_loans': CreditCardLoan.objects.filter(status='active').count(),
        'closed_loan_interest_paid': closed_interest_paid,
    })


class StaffListView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'core/staff_list.html'
    context_object_name = 'staff_users'

    def get_queryset(self):
        return User.objects.filter(is_superuser=False).order_by('username')


class StaffCreateView(AdminRequiredMixin, CreateView):
    model = User
    form_class = StaffUserForm
    template_name = 'core/staff_form.html'
    success_url = reverse_lazy('staff_list')

    def form_valid(self, form):
        messages.success(self.request, f'Staff user "{form.cleaned_data["username"]}" created successfully.')
        return super().form_valid(form)


class StaffUpdateView(AdminRequiredMixin, UpdateView):
    model = User
    form_class = StaffUserUpdateForm
    template_name = 'core/staff_form.html'
    success_url = reverse_lazy('staff_list')

    def get_queryset(self):
        return User.objects.filter(is_superuser=False)

    def form_valid(self, form):
        messages.success(self.request, f'Staff user "{form.cleaned_data["username"]}" updated successfully.')
        return super().form_valid(form)


class StaffDeleteView(AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'core/staff_confirm_delete.html'
    success_url = reverse_lazy('staff_list')
    context_object_name = 'staff_user'

    def get_queryset(self):
        return User.objects.filter(is_superuser=False)
