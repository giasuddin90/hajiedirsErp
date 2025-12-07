from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'sales'

def sales_redirect(request):
    return redirect('sales:order_list')

urlpatterns = [
    # Default redirect to orders
    path('', sales_redirect, name='sales_home'),
    
    # Sales Orders
    path('orders/', views.SalesOrderListView.as_view(), name='order_list'),
    path('orders/create/', views.SalesOrderCreateView.as_view(), name='order_create'),
    path('orders/<int:pk>/', views.SalesOrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/edit/', views.SalesOrderUpdateView.as_view(), name='order_edit'),
    path('orders/<int:pk>/delete/', views.SalesOrderDeleteView.as_view(), name='order_delete'),
    
    # Instant Sales
    path('instant-sales/', views.InstantSalesCreateView.as_view(), name='instant_sales'),
    path('instant-sales/<int:pk>/edit/', views.InstantSalesUpdateView.as_view(), name='instant_sales_edit'),
    
    # Order Flow Actions
    path('orders/<int:order_id>/mark-delivered/', views.mark_order_delivered, name='mark_order_delivered'),
    path('orders/<int:order_id>/cancel/', views.cancel_sales_order, name='cancel_sales_order'),
    path('orders/<int:order_id>/invoice/', views.sales_order_invoice, name='order_invoice'),
    path('orders/<int:order_id>/labour-chalan/', views.labour_chalan, name='labour_chalan'),
    
    # Reports
    path('reports/daily/', views.SalesDailyReportView.as_view(), name='sales_daily_report'),
    path('reports/monthly/', views.SalesMonthlyReportView.as_view(), name='sales_monthly_report'),
    path('reports/customer/', views.SalesCustomerReportView.as_view(), name='sales_customer_report'),
]
