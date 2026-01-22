from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .forms import BankAccountForm, CreditCardLoanForm, CreditCardLoanLedgerForm
from .models import BankAccount, CreditCardLoan, CreditCardLoanLedger
from core.utils import get_company_info


class BankAccountListView(ListView):
    model = BankAccount
    template_name = 'bankloan/bank_account_list.html'
    context_object_name = 'accounts'


class BankAccountCreateView(CreateView):
    model = BankAccount
    form_class = BankAccountForm
    template_name = 'bankloan/bank_account_form.html'
    success_url = reverse_lazy('bankloan:account_list')


class BankAccountUpdateView(UpdateView):
    model = BankAccount
    form_class = BankAccountForm
    template_name = 'bankloan/bank_account_form.html'
    success_url = reverse_lazy('bankloan:account_list')


class BankAccountDeleteView(DeleteView):
    model = BankAccount
    template_name = 'bankloan/bank_account_confirm_delete.html'
    success_url = reverse_lazy('bankloan:account_list')


class CreditCardLoanListView(ListView):
    model = CreditCardLoan
    template_name = 'bankloan/loan_list.html'
    context_object_name = 'loans'

    def get_queryset(self):
        return CreditCardLoan.objects.select_related('bank_account').order_by('-start_date', '-created_at')


class CreditCardLoanDetailView(DetailView):
    model = CreditCardLoan
    template_name = 'bankloan/loan_detail.html'
    context_object_name = 'loan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        loan = self.get_object()
        ledger_entries = loan.ledger_entries.order_by('-transaction_date', '-id')

        total_disbursed = loan.get_total_disbursed()
        total_principal_paid = loan.get_total_principal_paid()
        total_interest_paid = loan.get_total_interest_paid()
        outstanding_principal = loan.get_outstanding_principal()

        context.update({
            'ledger_entries': ledger_entries,
            'total_disbursed': total_disbursed,
            'total_principal_paid': total_principal_paid,
            'total_interest_paid': total_interest_paid,
            'outstanding_principal': outstanding_principal,
        })
        return context


class CreditCardLoanCreateView(CreateView):
    model = CreditCardLoan
    form_class = CreditCardLoanForm
    template_name = 'bankloan/loan_form.html'

    def get_success_url(self):
        return reverse_lazy('bankloan:loan_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)

        CreditCardLoanLedger.objects.create(
            loan=self.object,
            entry_type='disbursement',
            transaction_date=self.object.start_date,
            description='Initial loan disbursement',
            payment_amount=self.object.principal_amount,
            created_by=self.request.user,
        )

        messages.success(self.request, f'Loan {self.object.deal_number} created with disbursement entry.')
        return response


class CreditCardLoanUpdateView(UpdateView):
    model = CreditCardLoan
    form_class = CreditCardLoanForm
    template_name = 'bankloan/loan_form.html'

    def get_success_url(self):
        return reverse_lazy('bankloan:loan_detail', kwargs={'pk': self.object.pk})


class CreditCardLoanDeleteView(DeleteView):
    model = CreditCardLoan
    template_name = 'bankloan/loan_confirm_delete.html'
    success_url = reverse_lazy('bankloan:loan_list')


class CreditCardLoanLedgerCreateView(CreateView):
    model = CreditCardLoanLedger
    form_class = CreditCardLoanLedgerForm
    template_name = 'bankloan/loan_ledger_form.html'

    def get_success_url(self):
        return reverse_lazy('bankloan:loan_detail', kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['loan'] = get_object_or_404(CreditCardLoan, pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        loan = get_object_or_404(CreditCardLoan, pk=self.kwargs['pk'])
        form.instance.loan = loan
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        loan.refresh_status()

        messages.success(self.request, 'Ledger entry added successfully.')
        return response


def credit_card_loan_ledger_pdf(request, pk):
    loan = get_object_or_404(CreditCardLoan, pk=pk)
    ledger_entries = loan.ledger_entries.order_by('-transaction_date', '-id')

    context = {
        'loan': loan,
        'ledger_entries': ledger_entries,
        'total_disbursed': loan.get_total_disbursed(),
        'total_paid': loan.get_total_paid(),
        'extra_paid': loan.get_total_interest_paid(),
        'outstanding_principal': loan.get_outstanding_principal(),
        **get_company_info(),
    }

    template = get_template('bankloan/loan_ledger_pdf.html')
    html = template.render(context)
    return HttpResponse(html, content_type='text/html')
