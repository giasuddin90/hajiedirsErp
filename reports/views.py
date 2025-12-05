from django.shortcuts import render
from django.views.generic import ListView
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone
from django.db.models import Sum, Count
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import DatabaseError
import logging
from decimal import Decimal
from datetime import timedelta
import csv
from django.utils.dateparse import parse_date

from .models import ReportLog
from sales.models import SalesOrder
from purchases.models import PurchaseOrder, GoodsReceipt
from stock.models import Product
from customers.models import Customer, CustomerLedger
from suppliers.models import SupplierLedger
from expenses.models import Expense
from core.utils import get_company_info


# ==================== ENHANCED REPORTS WITH TIME RANGE FILTERING ====================

class SalesReportEnhancedView(LoginRequiredMixin, ListView):
    """Enhanced Sales Report with time range filtering and CSV download"""
    model = SalesOrder
    template_name = 'reports/sales_report_enhanced.html'
    context_object_name = 'sales_data'
    
    def get_queryset(self):
        """Get sales orders based on date range"""
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        # Default to last 30 days if no dates provided
        if start_date_str:
            start_date = parse_date(start_date_str)
        else:
            start_date = (timezone.now() - timedelta(days=30)).date()
            
        if end_date_str:
            end_date = parse_date(end_date_str)
        else:
            end_date = timezone.now().date()
        
        return SalesOrder.objects.filter(
            order_date__range=[start_date, end_date]
        ).select_related('customer').prefetch_related('items__product')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range from request
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        # Default to last 30 days if no dates provided
        if start_date_str:
            start_date = parse_date(start_date_str)
        else:
            start_date = (timezone.now() - timedelta(days=30)).date()
            
        if end_date_str:
            end_date = parse_date(end_date_str)
        else:
            end_date = timezone.now().date()
        
        # Get all orders in date range
        all_orders = SalesOrder.objects.filter(order_date__range=[start_date, end_date])
        delivered_orders = all_orders.filter(status='delivered')
        
        # Calculate metrics
        total_orders = all_orders.count()
        delivered_count = delivered_orders.count()
        total_sales = delivered_orders.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        average_order_value = total_sales / delivered_count if delivered_count > 0 else Decimal('0')
        
        # Get top customers
        top_customers = delivered_orders.values('customer__name').annotate(
            total_sales=Sum('total_amount'),
            order_count=Count('id')
        ).order_by('-total_sales')[:10]
        
        # Get sales by product
        sales_by_product = []
        for order in delivered_orders:
            for item in order.items.all():
                product_name = item.product.name
                existing = next((p for p in sales_by_product if p['product_name'] == product_name), None)
                if existing:
                    existing['total_quantity'] += float(item.quantity)
                    existing['total_value'] += float(item.total_price)
                    existing['order_count'] += 1
                else:
                    sales_by_product.append({
                        'product_name': product_name,
                        'total_quantity': float(item.quantity),
                        'total_value': float(item.total_price),
                        'order_count': 1,
                    })
        
        sales_by_product.sort(key=lambda x: x['total_value'], reverse=True)
        
        context.update({
            'start_date': start_date,
            'end_date': end_date,
            'total_orders': total_orders,
            'delivered_count': delivered_count,
            'total_sales': total_sales,
            'average_order_value': average_order_value,
            'top_customers': top_customers,
            'sales_by_product': sales_by_product[:10],  # Top 10 products
            'sales_orders': delivered_orders[:50],  # Recent orders for table
        })
        return context


class TopSellingProductsReportView(LoginRequiredMixin, ListView):
    """Top Selling Products Report with time range filtering and CSV download"""
    model = Product
    template_name = 'reports/top_selling_products.html'
    context_object_name = 'top_products'
    
    def get_queryset(self):
        """Return empty queryset since we calculate products in get_context_data"""
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range from request
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        # Default to last 30 days if no dates provided
        if start_date_str:
            start_date = parse_date(start_date_str)
        else:
            start_date = (timezone.now() - timedelta(days=30)).date()
            
        if end_date_str:
            end_date = parse_date(end_date_str)
        else:
            end_date = timezone.now().date()
        
        # Get sales orders in date range
        sales_orders = SalesOrder.objects.filter(
            order_date__range=[start_date, end_date],
            status='delivered'
        ).prefetch_related('items__product')
        
        # Calculate top selling products
        top_products = []
        for order in sales_orders:
            for item in order.items.all():
                product_name = item.product.name
                product_brand = item.product.brand.name if item.product.brand else "No Brand"
                product_category = item.product.category.name if item.product.category else "No Category"
                existing = next((p for p in top_products if p['product_name'] == product_name), None)
                if existing:
                    existing['total_quantity'] += float(item.quantity)
                    existing['total_value'] += float(item.total_price)
                    existing['order_count'] += 1
                else:
                    top_products.append({
                        'product_name': product_name,
                        'product_brand': product_brand,
                        'product_category': product_category,
                        'total_quantity': float(item.quantity),
                        'total_value': float(item.total_price),
                        'order_count': 1,
                        'average_price': float(item.unit_price),
                    })
        
        # Sort by total value
        top_products.sort(key=lambda x: x['total_value'], reverse=True)
        
        # Calculate summary metrics
        total_products_sold = len(top_products)
        total_quantity_sold = sum(p['total_quantity'] for p in top_products)
        total_value_sold = sum(p['total_value'] for p in top_products)
        average_price = total_value_sold / total_quantity_sold if total_quantity_sold > 0 else 0
        
        context.update({
            'start_date': start_date,
            'end_date': end_date,
            'top_products': top_products[:20],  # Top 20 products
            'total_products_sold': total_products_sold,
            'total_quantity_sold': total_quantity_sold,
            'total_value_sold': total_value_sold,
            'average_price': average_price,
        })
        return context


class TopSellingCustomersReportView(LoginRequiredMixin, ListView):
    """Top Selling Customers Report with time range filtering and CSV download"""
    model = Customer
    template_name = 'reports/top_selling_customers.html'
    context_object_name = 'top_customers'
    
    def get_queryset(self):
        """Return empty queryset since we calculate customers in get_context_data"""
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range from request
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        # Default to last 30 days if no dates provided
        if start_date_str:
            start_date = parse_date(start_date_str)
        else:
            start_date = (timezone.now() - timedelta(days=30)).date()
            
        if end_date_str:
            end_date = parse_date(end_date_str)
        else:
            end_date = timezone.now().date()
        
        # Get sales orders in date range
        sales_orders = SalesOrder.objects.filter(
            order_date__range=[start_date, end_date],
            status='delivered'
        ).select_related('customer')
        
        # Calculate top customers
        top_customers = []
        for order in sales_orders:
            if order.customer:
                customer_name = order.customer.name
                existing = next((c for c in top_customers if c['customer_name'] == customer_name), None)
                if existing:
                    existing['total_orders'] += 1
                    existing['total_value'] += float(order.total_amount)
                else:
                    top_customers.append({
                        'customer_name': customer_name,
                        'total_orders': 1,
                        'total_value': float(order.total_amount),
                    })
        
        # Sort by total value
        top_customers.sort(key=lambda x: x['total_value'], reverse=True)
        
        # Calculate summary metrics
        total_customers = len(top_customers)
        total_orders = sum(c['total_orders'] for c in top_customers)
        total_value = sum(c['total_value'] for c in top_customers)
        average_customer_value = total_value / total_customers if total_customers > 0 else 0
        
        context.update({
            'start_date': start_date,
            'end_date': end_date,
            'top_customers': top_customers[:20],  # Top 20 customers
            'total_customers': total_customers,
            'total_orders': total_orders,
            'total_value': total_value,
            'average_customer_value': average_customer_value,
        })
        return context


class AccountsReceivableReportView(LoginRequiredMixin, ListView):
    """Accounts Receivable Report with time range filtering and CSV download"""
    model = Customer
    template_name = 'reports/accounts_receivable.html'
    context_object_name = 'receivables_data'
    
    def get_queryset(self):
        """Return customers with positive balances"""
        return Customer.objects.filter(
            is_active=True,
            current_balance__gt=0
        ).order_by('-current_balance')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range from request
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        # Default to last 30 days if no dates provided
        if start_date_str:
            start_date = parse_date(start_date_str)
        else:
            start_date = (timezone.now() - timedelta(days=30)).date()
            
        if end_date_str:
            end_date = parse_date(end_date_str)
        else:
            end_date = timezone.now().date()
        
        # Get customers with receivables
        customers = self.get_queryset()
        
        # Calculate aging analysis
        aging_data = []
        for customer in customers:
            # Calculate days since last transaction (simplified)
            days_outstanding = 30  # Default for now
            
            if customer.current_balance > 0:
                aging_data.append({
                    'customer': customer,
                    'amount': customer.current_balance,
                    'days_outstanding': days_outstanding,
                    'aging_category': 'Current' if days_outstanding <= 30 else 'Overdue'
                })
        
        # Calculate summary metrics
        total_receivables = sum(c['amount'] for c in aging_data)
        current_receivables = sum(c['amount'] for c in aging_data if c['aging_category'] == 'Current')
        overdue_receivables = sum(c['amount'] for c in aging_data if c['aging_category'] == 'Overdue')
        
        context.update({
            'start_date': start_date,
            'end_date': end_date,
            'aging_data': aging_data,
            'total_receivables': total_receivables,
            'current_receivables': current_receivables,
            'overdue_receivables': overdue_receivables,
            'total_customers': len(aging_data),
        })
        return context


# ==================== PROFIT & LOSS REPORT ====================

class ProfitLossReportView(LoginRequiredMixin, ListView):
    """Profit & Loss Report with expense tracking, COGS, and sales revenue"""
    template_name = 'reports/profit_loss_report.html'
    context_object_name = 'profit_loss_data'
    
    def get_queryset(self):
        """Return empty queryset since we don't need a list of objects"""
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Get date range from request
            start_date_str = self.request.GET.get('start_date')
            end_date_str = self.request.GET.get('end_date')
            
            # Default to current month if no dates provided
            if start_date_str:
                start_date = parse_date(start_date_str)
                if not start_date:
                    raise ValidationError("Invalid start date format")
            else:
                start_date = timezone.now().date().replace(day=1)
                
            if end_date_str:
                end_date = parse_date(end_date_str)
                if not end_date:
                    raise ValidationError("Invalid end date format")
            else:
                end_date = timezone.now().date()
            
            # Validate date range
            if start_date > end_date:
                raise ValidationError("Start date cannot be after end date")
            
            # Sales Revenue
            sales_revenue = SalesOrder.objects.filter(
                status='delivered',
                order_date__range=[start_date, end_date]
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
            
            # Cost of Goods Sold (COGS) - Goods receipts that are received
            from purchases.models import GoodsReceipt
            cost_of_goods_sold = GoodsReceipt.objects.filter(
                status='received',
                receipt_date__range=[start_date, end_date]
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
            
            # Operating Expenses
            operating_expenses = Expense.objects.filter(
                expense_date__range=[start_date, end_date]
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Expenses by Category with percentages
            expenses_by_category = []
            raw_expenses = Expense.objects.filter(
                expense_date__range=[start_date, end_date]
            ).values('category__name').annotate(
                total=Sum('amount')
            ).order_by('-total')
            
            for expense in raw_expenses:
                expense_dict = dict(expense)
                expense_dict['percentage'] = (expense['total'] / sales_revenue * 100) if sales_revenue > 0 else 0
                expenses_by_category.append(expense_dict)
            
            # Calculate Gross Profit
            gross_profit = sales_revenue - cost_of_goods_sold
            
            # Calculate Net Profit
            net_profit = gross_profit - operating_expenses
            
            # Calculate percentages
            gross_profit_margin = (gross_profit / sales_revenue * 100) if sales_revenue > 0 else 0
            net_profit_margin = (net_profit / sales_revenue * 100) if sales_revenue > 0 else 0
            cogs_percentage = (cost_of_goods_sold / sales_revenue * 100) if sales_revenue > 0 else 0
            operating_expenses_percentage = (operating_expenses / sales_revenue * 100) if sales_revenue > 0 else 0
            
            # Monthly comparison data
            previous_month_start = (start_date - timedelta(days=1)).replace(day=1)
            previous_month_end = start_date - timedelta(days=1)
            
            previous_sales = SalesOrder.objects.filter(
                status='delivered',
                order_date__range=[previous_month_start, previous_month_end]
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
            
            previous_cogs = GoodsReceipt.objects.filter(
                status='received',
                receipt_date__range=[previous_month_start, previous_month_end]
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
            
            previous_expenses = Expense.objects.filter(
                expense_date__range=[previous_month_start, previous_month_end]
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            previous_gross_profit = previous_sales - previous_cogs
            previous_net_profit = previous_gross_profit - previous_expenses
            
            # Growth calculations
            sales_growth = ((sales_revenue - previous_sales) / previous_sales * 100) if previous_sales > 0 else 0
            gross_profit_growth = ((gross_profit - previous_gross_profit) / previous_gross_profit * 100) if previous_gross_profit > 0 else 0
            net_profit_growth = ((net_profit - previous_net_profit) / previous_net_profit * 100) if previous_net_profit > 0 else 0
            
            context.update({
                'start_date': start_date,
                'end_date': end_date,
                'sales_revenue': sales_revenue,
                'cost_of_goods_sold': cost_of_goods_sold,
                'gross_profit': gross_profit,
                'operating_expenses': operating_expenses,
                'net_profit': net_profit,
                'gross_profit_margin': gross_profit_margin,
                'net_profit_margin': net_profit_margin,
                'cogs_percentage': cogs_percentage,
                'operating_expenses_percentage': operating_expenses_percentage,
                'expenses_by_category': expenses_by_category,
                'previous_sales': previous_sales,
                'previous_cogs': previous_cogs,
                'previous_expenses': previous_expenses,
                'previous_gross_profit': previous_gross_profit,
                'previous_net_profit': previous_net_profit,
                'sales_growth': sales_growth,
                'gross_profit_growth': gross_profit_growth,
                'net_profit_growth': net_profit_growth,
            })
            
        except (ValidationError, DatabaseError) as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in ProfitLossReportView: {e}")
            # Set default values for error case
            context.update({
                'start_date': timezone.now().date().replace(day=1),
                'end_date': timezone.now().date(),
                'sales_revenue': Decimal('0'),
                'cost_of_goods_sold': Decimal('0'),
                'gross_profit': Decimal('0'),
                'operating_expenses': Decimal('0'),
                'net_profit': Decimal('0'),
                'gross_profit_margin': 0,
                'net_profit_margin': 0,
                'cogs_percentage': 0,
                'operating_expenses_percentage': 0,
                'expenses_by_category': [],
                'previous_sales': Decimal('0'),
                'previous_cogs': Decimal('0'),
                'previous_expenses': Decimal('0'),
                'previous_gross_profit': Decimal('0'),
                'previous_net_profit': Decimal('0'),
                'sales_growth': 0,
                'gross_profit_growth': 0,
                'net_profit_growth': 0,
                'error_message': 'An error occurred while generating the report. Please try again.',
            })
        
        return context


# ==================== CASH FLOW (INFLOW/OUTFLOW) REPORT ====================

class FinancialFlowReportView(LoginRequiredMixin, ListView):
    """Inflow/Outflow by customer, supplier and expense title with PDF download."""
    template_name = 'reports/financial_flow.html'
    context_object_name = 'flows'

    def get_queryset(self):
        return []

    def _get_date_range(self):
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        # Default to last 30 days
        start_date = parse_date(start_date_str) if start_date_str else (timezone.now() - timedelta(days=30)).date()
        end_date = parse_date(end_date_str) if end_date_str else timezone.now().date()
        return start_date, end_date

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start_date, end_date = self._get_date_range()

        # Inflow: Cash/Bank received from customers (CustomerLedger with transaction_type='payment')
        from datetime import datetime as dt
        start_datetime = timezone.make_aware(dt.combine(start_date, dt.min.time()))
        end_datetime = timezone.make_aware(dt.combine(end_date, dt.max.time()))
        
        customer_payments_qs = CustomerLedger.objects.filter(
            transaction_type='payment',
            transaction_date__range=[start_datetime, end_datetime]
        ).select_related('customer')

        # Calculate total inflow from customer payments
        total_inflow = customer_payments_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        inflow_by_customer = customer_payments_qs.values('customer__name').annotate(
            total=Sum('amount'),
            payments=Count('id')
        ).order_by('-total')

        # Outflow: Cash/Bank paid to suppliers (SupplierLedger with transaction_type='payment')
        supplier_payments_qs = SupplierLedger.objects.filter(
            transaction_type='payment',
            transaction_date__range=[start_datetime, end_datetime]
        ).select_related('supplier')

        # Calculate total outflow to suppliers from original queryset
        total_outflow_suppliers = supplier_payments_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        outflow_by_supplier = supplier_payments_qs.values('supplier__name').annotate(
            total=Sum('amount'),
            payments=Count('id')
        ).order_by('-total')

        # Expenses by title (only paid expenses)
        expenses_qs = Expense.objects.filter(
            status='paid',
            expense_date__range=[start_date, end_date]
        )
        
        # Calculate total expenses from original queryset
        total_expenses = expenses_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        expenses_by_title = expenses_qs.values('title').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')

        net_flow = total_inflow - (total_outflow_suppliers + total_expenses)

        context.update({
            'start_date': start_date,
            'end_date': end_date,
            'inflow_by_customer': inflow_by_customer,
            'outflow_by_supplier': outflow_by_supplier,
            'expenses_by_title': expenses_by_title,
            'total_inflow': total_inflow,
            'total_outflow_suppliers': total_outflow_suppliers,
            'total_expenses': total_expenses,
            'net_flow': net_flow,
            **get_company_info(),
        })
        return context


@login_required
def download_financial_flow_pdf(request):
    """
    Download the financial inflow/outflow report as a PDF file.
    """
    from django.template.loader import get_template
    from core.utils import get_company_info
    
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    # Parse dates with better error handling
    try:
        start_date = parse_date(start_date_str) if start_date_str else (timezone.now() - timedelta(days=30)).date()
        end_date = parse_date(end_date_str) if end_date_str else timezone.now().date()
        
        # Validate dates
        if start_date is None:
            start_date = (timezone.now() - timedelta(days=30)).date()
        if end_date is None:
            end_date = timezone.now().date()
    except (ValueError, TypeError):
        # Fallback to default dates if parsing fails
        start_date = (timezone.now() - timedelta(days=30)).date()
        end_date = timezone.now().date()

    # Convert dates to datetime for ledger queries
    from datetime import datetime as dt
    try:
        start_datetime = timezone.make_aware(dt.combine(start_date, dt.min.time()))
        end_datetime = timezone.make_aware(dt.combine(end_date, dt.max.time()))
    except (ValueError, TypeError) as e:
        # If date conversion fails, redirect back with error
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, f"Invalid date format. Please try again.")
        return redirect('reports:financial_flow')

    # Inflow: Cash/Bank received from customers
    customer_payments_qs = CustomerLedger.objects.filter(
        transaction_type='payment',
        transaction_date__range=[start_datetime, end_datetime]
    ).select_related('customer')

    total_inflow = customer_payments_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    inflow_by_customer = customer_payments_qs.values('customer__name').annotate(
        total=Sum('amount'),
        payments=Count('id')
    ).order_by('-total')

    # Outflow: Cash/Bank paid to suppliers
    supplier_payments_qs = SupplierLedger.objects.filter(
        transaction_type='payment',
        transaction_date__range=[start_datetime, end_datetime]
    ).select_related('supplier')

    total_outflow_suppliers = supplier_payments_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    outflow_by_supplier = supplier_payments_qs.values('supplier__name').annotate(
        total=Sum('amount'),
        payments=Count('id')
    ).order_by('-total')

    # Expenses by title (only paid expenses)
    expenses_qs = Expense.objects.filter(
        status='paid',
        expense_date__range=[start_date, end_date]
    )
    
    total_expenses = expenses_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    expenses_by_title = expenses_qs.values('title').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')

    net_flow = total_inflow - (total_outflow_suppliers + total_expenses)

    template = get_template('reports/financial_flow_pdf.html')
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'inflow_by_customer': inflow_by_customer,
        'outflow_by_supplier': outflow_by_supplier,
        'expenses_by_title': expenses_by_title,
        'total_inflow': total_inflow,
        'total_outflow_suppliers': total_outflow_suppliers,
        'total_expenses': total_expenses,
        'net_flow': net_flow,
        **get_company_info(),
    }
    html = template.render(context)

    # Try to generate PDF using weasyprint, fallback to HTML if not available
    try:
        from weasyprint import HTML
        from io import BytesIO
        
        pdf_file = BytesIO()
        HTML(string=html).write_pdf(pdf_file)
        pdf_file.seek(0)
        
        response = HttpResponse(pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="financial_flow_report_{start_date}_to_{end_date}.pdf"'
        return response
    except ImportError:
        # If weasyprint is not installed, return HTML with instructions
        from django.contrib import messages
        messages.warning(request, "PDF generation requires weasyprint. Install it with: pip install weasyprint")
        response = HttpResponse(html, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="financial_flow_report_{start_date}_to_{end_date}.html"'
        return response
    except Exception as e:
        # If PDF generation fails, return HTML
        from django.contrib import messages
        messages.warning(request, f"PDF generation failed: {str(e)}. Returning HTML instead.")
        response = HttpResponse(html, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="financial_flow_report_{start_date}_to_{end_date}.html"'
        return response


# ==================== CSV DOWNLOAD VIEWS ====================

@login_required
def download_sales_report_csv(request):
    """Download Sales Report as CSV"""
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if start_date_str:
        start_date = parse_date(start_date_str)
    else:
        start_date = (timezone.now() - timedelta(days=30)).date()
        
    if end_date_str:
        end_date = parse_date(end_date_str)
    else:
        end_date = timezone.now().date()
    
    # Get sales orders
    orders = SalesOrder.objects.filter(
        order_date__range=[start_date, end_date],
        status='delivered'
    ).select_related('customer')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    
    # Header
    writer.writerow(['SALES REPORT'])
    writer.writerow([f'Period: {start_date} to {end_date}'])
    writer.writerow([])
    
    # Summary
    total_sales = orders.aggregate(total=Sum('total_amount'))['total'] or 0
    writer.writerow(['Total Sales', total_sales])
    writer.writerow(['Total Orders', orders.count()])
    writer.writerow([])
    
    # Orders
    writer.writerow(['Order Number', 'Customer', 'Date', 'Amount'])
    for order in orders:
        customer_name = order.customer.name if order.customer else 'Anonymous'
        writer.writerow([
            order.order_number,
            customer_name,
            order.order_date,
            order.total_amount
        ])
    
    return response


@login_required
def download_top_products_csv(request):
    """Download Top Selling Products Report as CSV"""
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if start_date_str:
        start_date = parse_date(start_date_str)
    else:
        start_date = (timezone.now() - timedelta(days=30)).date()
        
    if end_date_str:
        end_date = parse_date(end_date_str)
    else:
        end_date = timezone.now().date()
    
    # Get sales orders
    orders = SalesOrder.objects.filter(
        order_date__range=[start_date, end_date],
        status='delivered'
    ).prefetch_related('items__product')
    
    # Calculate product sales
    product_sales = {}
    for order in orders:
        for item in order.items.all():
            product_name = item.product.name
            if product_name in product_sales:
                product_sales[product_name]['quantity'] += float(item.quantity)
                product_sales[product_name]['value'] += float(item.total_price)
                product_sales[product_name]['orders'] += 1
            else:
                product_sales[product_name] = {
                    'quantity': float(item.quantity),
                    'value': float(item.total_price),
                    'orders': 1
                }
    
    # Sort by value
    sorted_products = sorted(product_sales.items(), key=lambda x: x[1]['value'], reverse=True)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="top_products_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    
    # Header
    writer.writerow(['TOP SELLING PRODUCTS REPORT'])
    writer.writerow([f'Period: {start_date} to {end_date}'])
    writer.writerow([])
    
    # Products
    writer.writerow(['Product Name', 'Total Quantity', 'Total Value', 'Orders'])
    for product_name, data in sorted_products:
        writer.writerow([
            product_name,
            data['quantity'],
            data['value'],
            data['orders']
        ])
    
    return response


@login_required
def download_top_customers_csv(request):
    """Download Top Selling Customers Report as CSV"""
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if start_date_str:
        start_date = parse_date(start_date_str)
    else:
        start_date = (timezone.now() - timedelta(days=30)).date()
        
    if end_date_str:
        end_date = parse_date(end_date_str)
    else:
        end_date = timezone.now().date()
    
    # Get sales orders
    orders = SalesOrder.objects.filter(
        order_date__range=[start_date, end_date],
        status='delivered'
    ).select_related('customer')
    
    # Calculate customer sales
    customer_sales = {}
    for order in orders:
        if order.customer:
            customer_name = order.customer.name
            if customer_name in customer_sales:
                customer_sales[customer_name]['orders'] += 1
                customer_sales[customer_name]['value'] += float(order.total_amount)
            else:
                customer_sales[customer_name] = {
                    'orders': 1,
                    'value': float(order.total_amount)
                }
    
    # Sort by value
    sorted_customers = sorted(customer_sales.items(), key=lambda x: x[1]['value'], reverse=True)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="top_customers_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    
    # Header
    writer.writerow(['TOP SELLING CUSTOMERS REPORT'])
    writer.writerow([f'Period: {start_date} to {end_date}'])
    writer.writerow([])
    
    # Customers
    writer.writerow(['Customer Name', 'Total Orders', 'Total Value'])
    for customer_name, data in sorted_customers:
        writer.writerow([
            customer_name,
            data['orders'],
            data['value']
        ])
    
    return response


@login_required
def download_receivables_csv(request):
    """Download Accounts Receivable Report as CSV"""
    customers = Customer.objects.filter(is_active=True)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="accounts_receivable.csv"'
    
    writer = csv.writer(response)
    
    # Header
    writer.writerow(['ACCOUNTS RECEIVABLE REPORT'])
    writer.writerow([])
    
    # Customers
    writer.writerow(['Customer Name', 'Current Balance', 'Credit Limit'])
    for customer in customers:
        if customer.current_balance > 0:
            writer.writerow([
                customer.name,
                customer.current_balance,
                customer.credit_limit
            ])
    
    return response


@login_required
def download_profit_loss_csv(request):
    """Download Profit & Loss report as CSV"""
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if start_date_str:
        start_date = parse_date(start_date_str)
    else:
        start_date = timezone.now().date().replace(day=1)
        
    if end_date_str:
        end_date = parse_date(end_date_str)
    else:
        end_date = timezone.now().date()
    
    # Calculate P&L data
    sales_revenue = SalesOrder.objects.filter(
        status='delivered',
        order_date__range=[start_date, end_date]
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    from purchases.models import GoodsReceipt
    cost_of_goods_sold = GoodsReceipt.objects.filter(
        status='received',
        receipt_date__range=[start_date, end_date]
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    operating_expenses = Expense.objects.filter(
        expense_date__range=[start_date, end_date]
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    gross_profit = sales_revenue - cost_of_goods_sold
    net_profit = gross_profit - operating_expenses
    
    # Expenses by category
    expenses_by_category = Expense.objects.filter(
        expense_date__range=[start_date, end_date]
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="profit_loss_report_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    
    # Header
    writer.writerow(['PROFIT & LOSS STATEMENT'])
    writer.writerow([f'Period: {start_date} to {end_date}'])
    writer.writerow([])
    
    # Revenue section
    writer.writerow(['REVENUE'])
    writer.writerow(['Sales Revenue', sales_revenue])
    writer.writerow([])
    
    # Cost of Goods Sold
    writer.writerow(['COST OF GOODS SOLD'])
    writer.writerow(['Cost of Goods Sold', cost_of_goods_sold])
    writer.writerow(['Gross Profit', gross_profit])
    writer.writerow([])
    
    # Operating Expenses
    writer.writerow(['OPERATING EXPENSES'])
    for expense in expenses_by_category:
        category_name = expense['category__name'] if expense['category__name'] else 'Uncategorized'
        writer.writerow([category_name, expense['total']])
    writer.writerow(['Total Operating Expenses', operating_expenses])
    writer.writerow([])
    
    # Net Profit
    writer.writerow(['NET PROFIT', net_profit])
    
    return response