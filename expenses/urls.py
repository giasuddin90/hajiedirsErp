from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    # Expense Categories
    path('categories/', views.ExpenseCategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.ExpenseCategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.ExpenseCategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.ExpenseCategoryDeleteView.as_view(), name='category_delete'),
    
    # Expenses
    path('', views.ExpenseListView.as_view(), name='expense_list'),
    path('create/', views.ExpenseCreateView.as_view(), name='expense_create'),
    path('<int:pk>/', views.ExpenseDetailView.as_view(), name='expense_detail'),
    path('<int:pk>/edit/', views.ExpenseUpdateView.as_view(), name='expense_edit'),
    path('<int:pk>/delete/', views.ExpenseDeleteView.as_view(), name='expense_delete'),
    
    # CSV Downloads
    path('download/expenses-csv/', views.download_expenses_csv, name='download_expenses_csv'),
]
