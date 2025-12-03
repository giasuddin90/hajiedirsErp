from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    # Supplier Management
    path('', views.SupplierListView.as_view(), name='supplier_list'),
    path('create/', views.SupplierCreateView.as_view(), name='supplier_create'),
    path('<int:pk>/', views.SupplierDetailView.as_view(), name='supplier_detail'),
    path('<int:pk>/edit/', views.SupplierUpdateView.as_view(), name='supplier_edit'),
    path('<int:pk>/delete/', views.SupplierDeleteView.as_view(), name='supplier_delete'),
    
    # Supplier Ledger
    path('<int:pk>/ledger/', views.SupplierLedgerDetailView.as_view(), name='supplier_ledger_detail'),
    path('<int:supplier_id>/ledger/', views.SupplierLedgerListView.as_view(), name='supplier_ledger_list'),
    path('<int:supplier_id>/ledger/create/', views.SupplierLedgerCreateView.as_view(), name='supplier_ledger_create'),
    path('<int:pk>/opening-balance/', views.set_opening_balance, name='supplier_opening_balance'),
    
    
    # General views (without supplier_id)
    path('ledger/', views.SupplierLedgerListView.as_view(), name='ledger_list'),
    path('ledger/create/', views.SupplierLedgerCreateView.as_view(), name='ledger_create'),
]
