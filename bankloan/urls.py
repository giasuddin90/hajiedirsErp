from django.urls import path

from . import views

app_name = 'bankloan'

urlpatterns = [
    path('accounts/', views.BankAccountListView.as_view(), name='account_list'),
    path('accounts/new/', views.BankAccountCreateView.as_view(), name='account_create'),
    path('accounts/<int:pk>/edit/', views.BankAccountUpdateView.as_view(), name='account_edit'),
    path('accounts/<int:pk>/delete/', views.BankAccountDeleteView.as_view(), name='account_delete'),
    path('loans/', views.CreditCardLoanListView.as_view(), name='loan_list'),
    path('loans/new/', views.CreditCardLoanCreateView.as_view(), name='loan_create'),
    path('loans/<int:pk>/', views.CreditCardLoanDetailView.as_view(), name='loan_detail'),
    path('loans/<int:pk>/edit/', views.CreditCardLoanUpdateView.as_view(), name='loan_edit'),
    path('loans/<int:pk>/delete/', views.CreditCardLoanDeleteView.as_view(), name='loan_delete'),
    path('loans/<int:pk>/ledger/new/', views.CreditCardLoanLedgerCreateView.as_view(), name='loan_ledger_create'),
    path('loans/<int:pk>/ledger/pdf/', views.credit_card_loan_ledger_pdf, name='loan_ledger_pdf'),
]
