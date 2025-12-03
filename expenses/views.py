from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
import csv

from .models import ExpenseCategory, Expense
from .forms import ExpenseCategoryForm, ExpenseForm, ExpenseFilterForm


class ExpenseDashboardView(LoginRequiredMixin, TemplateView):
    """Simple expense dashboard with overview statistics"""
    template_name = 'expenses/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current month data
        current_month = timezone.now().replace(day=1)
        next_month = (current_month + timedelta(days=32)).replace(day=1)
        
        # Get last month data
        last_month = (current_month - timedelta(days=1)).replace(day=1)
        
        # Current month expenses
        current_month_expenses = Expense.objects.filter(
            expense_date__gte=current_month,
            expense_date__lt=next_month
        )
        
        # Last month expenses
        last_month_expenses = Expense.objects.filter(
            expense_date__gte=last_month,
            expense_date__lt=current_month
        )
        
        # Calculate statistics
        total_expenses_current = current_month_expenses.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        total_expenses_last = last_month_expenses.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        # Calculate growth percentage
        if total_expenses_last > 0:
            growth_percentage = ((total_expenses_current - total_expenses_last) / total_expenses_last) * 100
        else:
            growth_percentage = 0
        
        # Unpaid expenses
        unpaid_expenses = Expense.objects.filter(status='unpaid').count()
        paid_expenses = Expense.objects.filter(status='paid').count()
        
        # Expenses by category
        expenses_by_category = current_month_expenses.values('category__name').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        # Recent expenses
        recent_expenses = Expense.objects.all().order_by('-created_at')[:10]
        
        context.update({
            'total_expenses_current': total_expenses_current,
            'total_expenses_last': total_expenses_last,
            'growth_percentage': growth_percentage,
            'unpaid_expenses': unpaid_expenses,
            'paid_expenses': paid_expenses,
            'expenses_by_category': expenses_by_category,
            'recent_expenses': recent_expenses,
            'current_month': current_month.strftime('%B %Y'),
            'last_month': last_month.strftime('%B %Y'),
        })
        return context


class ExpenseCategoryListView(LoginRequiredMixin, ListView):
    """List all expense categories"""
    model = ExpenseCategory
    template_name = 'expenses/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20


class ExpenseCategoryCreateView(LoginRequiredMixin, CreateView):
    """Create new expense category"""
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'expenses/category_form.html'
    success_url = reverse_lazy('expenses:category_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Expense category created successfully!')
        return super().form_valid(form)


class ExpenseCategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Update expense category"""
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'expenses/category_form.html'
    success_url = reverse_lazy('expenses:category_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Expense category updated successfully!')
        return super().form_valid(form)


class ExpenseCategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Delete expense category"""
    model = ExpenseCategory
    template_name = 'expenses/category_confirm_delete.html'
    success_url = reverse_lazy('expenses:category_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Expense category deleted successfully!')
        return super().delete(request, *args, **kwargs)


class ExpenseListView(LoginRequiredMixin, ListView):
    """List all expenses with filtering"""
    model = Expense
    template_name = 'expenses/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Expense.objects.all().order_by('-expense_date', '-created_at')

        # Apply filters
        q = self.request.GET.get('q')
        date_preset = self.request.GET.get('date_preset')
        category = self.request.GET.get('category')
        status = self.request.GET.get('status')
        payment_method = self.request.GET.get('payment_method')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        min_amount = self.request.GET.get('min_amount')
        max_amount = self.request.GET.get('max_amount')

        # Full-text like search across key fields
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q)
                | Q(description__icontains=q)
                | Q(vendor_name__icontains=q)
                | Q(receipt_number__icontains=q)
            )

        # Date presets
        if date_preset:
            today = timezone.localdate()
            if date_preset == 'today':
                queryset = queryset.filter(expense_date=today)
            elif date_preset == 'yesterday':
                queryset = queryset.filter(expense_date=today - timedelta(days=1))
            elif date_preset == 'this_week':
                start_of_week = today - timedelta(days=today.weekday())
                queryset = queryset.filter(expense_date__gte=start_of_week, expense_date__lte=today)
            elif date_preset == 'last_7':
                queryset = queryset.filter(expense_date__gte=today - timedelta(days=6), expense_date__lte=today)
            elif date_preset == 'this_month':
                start_of_month = today.replace(day=1)
                queryset = queryset.filter(expense_date__gte=start_of_month, expense_date__lte=today)
            elif date_preset == 'last_month':
                first_of_this_month = today.replace(day=1)
                last_month_end = first_of_this_month - timedelta(days=1)
                last_month_start = last_month_end.replace(day=1)
                queryset = queryset.filter(expense_date__gte=last_month_start, expense_date__lte=last_month_end)
            elif date_preset == 'this_year':
                start_of_year = today.replace(month=1, day=1)
                queryset = queryset.filter(expense_date__gte=start_of_year, expense_date__lte=today)

        if category:
            queryset = queryset.filter(category_id=category)
        if status:
            queryset = queryset.filter(status=status)
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        if start_date:
            queryset = queryset.filter(expense_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(expense_date__lte=end_date)
        if min_amount:
            queryset = queryset.filter(amount__gte=min_amount)
        if max_amount:
            queryset = queryset.filter(amount__lte=max_amount)

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ExpenseFilterForm(self.request.GET)
        return context


class ExpenseDetailView(LoginRequiredMixin, DetailView):
    """View expense details"""
    model = Expense
    template_name = 'expenses/expense_detail.html'
    context_object_name = 'expense'


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    """Create new expense"""
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expenses:expense_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Expense created successfully!')
        return super().form_valid(form)


class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    """Update expense"""
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expenses:expense_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Expense updated successfully!')
        return super().form_valid(form)


class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    """Delete expense"""
    model = Expense
    template_name = 'expenses/expense_confirm_delete.html'
    success_url = reverse_lazy('expenses:expense_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Expense deleted successfully!')
        return super().delete(request, *args, **kwargs)


# CSV Download Views
def download_expenses_csv(request):
    """Download expenses as CSV"""
    expenses = Expense.objects.all().order_by('-expense_date')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Title', 'Category', 'Amount', 'Expense Date', 'Status',
        'Payment Method', 'Vendor', 'Receipt Number', 'Created By'
    ])
    
    for expense in expenses:
        writer.writerow([
            expense.title,
            expense.category.name if expense.category else '',
            expense.amount,
            expense.expense_date,
            expense.status,
            expense.payment_method,
            expense.vendor_name,
            expense.receipt_number,
            expense.created_by.username if expense.created_by else '',
        ])
    
    return response