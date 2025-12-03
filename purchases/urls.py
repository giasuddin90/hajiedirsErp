from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'purchases'

def purchases_redirect(request):
    return redirect('purchases:order_list')

urlpatterns = [
    # Default redirect to orders
    path('', purchases_redirect, name='purchases_home'),
    
    # Purchase Orders
    path('orders/', views.PurchaseOrderListView.as_view(), name='order_list'),
    path('orders/create/', views.PurchaseOrderCreateView.as_view(), name='order_create'),
    path('orders/<int:pk>/', views.PurchaseOrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/edit/', views.PurchaseOrderUpdateView.as_view(), name='order_edit'),
    path('orders/<int:pk>/delete/', views.PurchaseOrderDeleteView.as_view(), name='order_delete'),
    
    # Simplified flow - no separate goods receipts needed
    
    # Removed unnecessary URLs for simplified purchase flow
    
    # Reports
    path('reports/daily/', views.PurchaseDailyReportView.as_view(), name='purchase_daily_report'),
    path('reports/monthly/', views.PurchaseMonthlyReportView.as_view(), name='purchase_monthly_report'),
    path('reports/supplier/', views.PurchaseSupplierReportView.as_view(), name='purchase_supplier_report'),
]
