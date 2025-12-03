from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from customers.models import Customer, CustomerLedger
from suppliers.models import Supplier, SupplierLedger
from stock.models import Product, get_low_stock_products
from sales.models import SalesOrder
from purchases.models import PurchaseOrder
from expenses.models import Expense


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Basic counts
        context['total_customers'] = Customer.objects.filter(is_active=True).count()
        context['total_suppliers'] = Supplier.objects.filter(is_active=True).count()
        context['total_products'] = Product.objects.count()
        
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
        
        # Purchase metrics
        monthly_purchases = PurchaseOrder.objects.filter(
            status='goods-received',
            order_date__gte=this_month_start
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
    return render(request, 'dashboard.html', {
        'total_customers': Customer.objects.count(),
        'total_suppliers': Supplier.objects.count(),
        'total_products': Product.objects.count(),
        'total_sales': SalesOrder.objects.filter(status='delivered').aggregate(total=Sum('total_amount'))['total'] or 0,
        'recent_orders': SalesOrder.objects.select_related('customer').order_by('-created_at')[:5],
        'low_stock_alerts': get_low_stock_products()[:5],
    })
