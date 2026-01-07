from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Reports
    path('top-products/', views.TopSellingProductsReportView.as_view(), name='top_selling_products'),
    path('top-customers/', views.TopSellingCustomersReportView.as_view(), name='top_selling_customers'),
    path('accounts-receivable/', views.AccountsReceivableReportView.as_view(), name='accounts_receivable'),
    path('profit-loss/', views.ProfitLossReportView.as_view(), name='profit_loss'),
    path('financial-flow/', views.FinancialFlowReportView.as_view(), name='financial_flow'),
    path('labour-cost/', views.LabourCostReportView.as_view(), name='labour_cost'),
    path('transportation-cost/', views.TransportationCostReportView.as_view(), name='transportation_cost'),
    
    # CSV Download URLs
    path('download/sales-csv/', views.download_sales_report_csv, name='download_sales_csv'),
    path('download/top-products-csv/', views.download_top_products_csv, name='download_top_products_csv'),
    path('download/top-customers-csv/', views.download_top_customers_csv, name='download_top_customers_csv'),
    path('download/receivables-csv/', views.download_receivables_csv, name='download_receivables_csv'),
    path('download/profit-loss-csv/', views.download_profit_loss_csv, name='download_profit_loss_csv'),
    
    # PDF / printable downloads
    path('download/financial-flow/', views.download_financial_flow_pdf, name='download_financial_flow_pdf'),
]
