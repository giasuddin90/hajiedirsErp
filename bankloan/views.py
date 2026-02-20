from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Case, When, DecimalField, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .forms import BankAccountForm, BankAccountLedgerForm, CreditCardLoanForm, CreditCardLoanLedgerForm
from .models import BankAccount, BankAccountLedger, CreditCardLoan, CreditCardLoanLedger
from core.utils import get_company_info, html_to_pdf_response
from core.mixins import StaffRequiredMixin, AdminRequiredMixin


class BankAccountListView(StaffRequiredMixin, ListView):
    model = BankAccount
    template_name = 'bankloan/bank_account_list.html'
    context_object_name = 'accounts'

    def get_queryset(self):
        return BankAccount.objects.filter(is_active=True)


class BankAccountLedgerListView(StaffRequiredMixin, ListView):
    model = BankAccount
    template_name = 'bankloan/bank_account_ledger_list.html'
    context_object_name = 'accounts'

    def get_queryset(self):
        return BankAccount.objects.filter(is_active=True).annotate(
            total_deposits=Coalesce(
                Sum(
                    Case(
                        When(ledger_entries__entry_type='deposit', then='ledger_entries__amount'),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2),
                    )
                ),
                Value(Decimal('0.00'), output_field=DecimalField(max_digits=15, decimal_places=2)),
            ),
            total_withdrawals=Coalesce(
                Sum(
                    Case(
                        When(ledger_entries__entry_type='withdrawal', then='ledger_entries__amount'),
                        default=Value(0),
                        output_field=DecimalField(max_digits=15, decimal_places=2),
                    )
                ),
                Value(Decimal('0.00'), output_field=DecimalField(max_digits=15, decimal_places=2)),
            ),
        ).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        accounts = context['accounts']

        grand_opening = Decimal('0.00')
        grand_deposits = Decimal('0.00')
        grand_withdrawals = Decimal('0.00')
        grand_balance = Decimal('0.00')

        for acc in accounts:
            acc.balance = acc.opening_balance + acc.total_deposits - acc.total_withdrawals
            grand_opening += acc.opening_balance
            grand_deposits += acc.total_deposits
            grand_withdrawals += acc.total_withdrawals
            grand_balance += acc.balance

        context.update({
            'grand_opening': grand_opening,
            'grand_deposits': grand_deposits,
            'grand_withdrawals': grand_withdrawals,
            'grand_balance': grand_balance,
        })
        return context


class BankAccountLedgerView(StaffRequiredMixin, DetailView):
    model = BankAccount
    template_name = 'bankloan/bank_account_ledger.html'
    context_object_name = 'account'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.object
        loans = account.credit_card_loans.all().order_by('-start_date', '-created_at')

        total_received = Decimal('0.00')
        total_paid = Decimal('0.00')

        for loan in loans:
            loan.received_amount = loan.get_total_disbursed()
            loan.paid_amount = loan.get_total_paid()
            loan.left_amount = loan.get_outstanding_principal()
            loan.interest_paid = loan.get_total_interest_paid()
            total_received += loan.received_amount
            total_paid += loan.paid_amount

        context.update({
            'loans': loans,
            'total_received': total_received,
            'total_paid': total_paid,
            'total_left': total_received - total_paid if total_received > total_paid else Decimal('0.00'),
        })
        return context


@login_required
def bank_account_ledger_pdf(request, pk):
    account = get_object_or_404(BankAccount, pk=pk)
    loans = account.credit_card_loans.all().order_by('-start_date', '-created_at')

    total_received = Decimal('0.00')
    total_paid = Decimal('0.00')

    for loan in loans:
        loan.received_amount = loan.get_total_disbursed()
        loan.paid_amount = loan.get_total_paid()
        loan.left_amount = loan.get_outstanding_principal()
        loan.interest_paid = loan.get_total_interest_paid()
        total_received += loan.received_amount
        total_paid += loan.paid_amount

    context = {
        'account': account,
        'loans': loans,
        'total_received': total_received,
        'total_paid': total_paid,
        'total_left': total_received - total_paid if total_received > total_paid else Decimal('0.00'),
    }

    template = get_template('bankloan/bank_account_ledger_pdf.html')
    html = template.render(context)
    return HttpResponse(html, content_type='text/html')


class BankAccountCreateView(StaffRequiredMixin, CreateView):
    model = BankAccount
    form_class = BankAccountForm
    template_name = 'bankloan/bank_account_form.html'
    success_url = reverse_lazy('bankloan:account_list')


class BankAccountUpdateView(StaffRequiredMixin, UpdateView):
    model = BankAccount
    form_class = BankAccountForm
    template_name = 'bankloan/bank_account_form.html'
    success_url = reverse_lazy('bankloan:account_list')


class BankAccountDeleteView(AdminRequiredMixin, DeleteView):
    model = BankAccount
    template_name = 'bankloan/bank_account_confirm_delete.html'
    success_url = reverse_lazy('bankloan:account_list')


class BankAccountTransactionLedgerView(StaffRequiredMixin, DetailView):
    model = BankAccount
    template_name = 'bankloan/bank_account_transaction_ledger.html'
    context_object_name = 'account'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.object
        entries = account.ledger_entries.all().order_by('transaction_date', 'id')

        running_balance = account.opening_balance
        ledger_rows = []
        for entry in entries:
            if entry.entry_type == 'deposit':
                running_balance += entry.amount
            else:
                running_balance -= entry.amount
            ledger_rows.append({
                'entry': entry,
                'balance': running_balance,
            })

        context.update({
            'ledger_rows': ledger_rows,
            'total_deposits': account.get_total_deposits(),
            'total_withdrawals': account.get_total_withdrawals(),
            'current_balance': account.get_calculated_balance(),
        })
        return context


class BankAccountLedgerEntryCreateView(StaffRequiredMixin, CreateView):
    model = BankAccountLedger
    form_class = BankAccountLedgerForm
    template_name = 'bankloan/bank_account_ledger_entry_form.html'

    def get_success_url(self):
        return reverse_lazy('bankloan:account_transaction_ledger', kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account'] = get_object_or_404(BankAccount, pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        account = get_object_or_404(BankAccount, pk=self.kwargs['pk'])
        form.instance.bank_account = account
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'{form.instance.get_entry_type_display()} of ৳{form.instance.amount} recorded.')
        return response


class BankAccountLedgerEntryDeleteView(AdminRequiredMixin, DeleteView):
    model = BankAccountLedger
    template_name = 'bankloan/bank_account_ledger_entry_confirm_delete.html'
    context_object_name = 'entry'

    def get_success_url(self):
        return reverse_lazy('bankloan:account_transaction_ledger', kwargs={'pk': self.object.bank_account.pk})

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Ledger entry deleted successfully.')
        return response


@login_required
def bank_account_transaction_ledger_pdf(request, pk):
    account = get_object_or_404(BankAccount, pk=pk)
    entries = account.ledger_entries.all().order_by('transaction_date', 'id')

    running_balance = account.opening_balance
    ledger_rows = []
    for entry in entries:
        if entry.entry_type == 'deposit':
            running_balance += entry.amount
        else:
            running_balance -= entry.amount
        ledger_rows.append({
            'entry': entry,
            'balance': running_balance,
        })

    context = {
        'account': account,
        'ledger_rows': ledger_rows,
        'total_deposits': account.get_total_deposits(),
        'total_withdrawals': account.get_total_withdrawals(),
        'current_balance': account.get_calculated_balance(),
    }

    template = get_template('bankloan/bank_account_transaction_ledger_pdf.html')
    html = template.render(context)
    return HttpResponse(html, content_type='text/html')


class CreditCardLoanListView(StaffRequiredMixin, ListView):
    model = CreditCardLoan
    template_name = 'bankloan/loan_list.html'
    context_object_name = 'loans'

    def get_queryset(self):
        queryset = (
            CreditCardLoan.objects.select_related('bank_account')
            .annotate(
                total_paid=Coalesce(
                    Sum(
                        Case(
                            When(ledger_entries__entry_type='payment', then='ledger_entries__payment_amount'),
                            default=Value(0),
                            output_field=DecimalField(max_digits=15, decimal_places=2),
                        )
                    ),
                    Value(Decimal('0.00'), output_field=DecimalField(max_digits=15, decimal_places=2)),
                ),
                total_disbursed=Coalesce(
                    Sum(
                        Case(
                            When(ledger_entries__entry_type='disbursement', then='ledger_entries__payment_amount'),
                            default=Value(0),
                            output_field=DecimalField(max_digits=15, decimal_places=2),
                        )
                    ),
                    Value(Decimal('0.00'), output_field=DecimalField(max_digits=15, decimal_places=2)),
                ),
            )
            .order_by('-start_date', '-created_at')
        )
        deal_number = self.request.GET.get('deal_number')
        if deal_number:
            queryset = queryset.filter(deal_number__icontains=deal_number.strip())
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        loans = context.get('loans', [])
        active_count = 0
        total_active_amount = Decimal('0.00')
        total_active_left = Decimal('0.00')

        for loan in loans:
            disbursed = loan.total_disbursed or loan.principal_amount
            paid = loan.total_paid or Decimal('0.00')
            left = disbursed - paid
            loan.paid_amount = paid
            loan.left_amount = left if left > 0 else Decimal('0.00')
            loan.interest_paid = loan.get_total_interest_paid()
            if loan.status == 'active':
                active_count += 1
                total_active_amount += disbursed
                total_active_left += loan.left_amount

        context['loans'] = loans
        context['deal_number_filter'] = self.request.GET.get('deal_number', '').strip()
        context['active_loan_count'] = active_count
        context['total_active_amount'] = total_active_amount
        context['total_active_left'] = total_active_left
        return context


class CreditCardLoanDetailView(StaffRequiredMixin, DetailView):
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


class CreditCardLoanCreateView(StaffRequiredMixin, CreateView):
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


class CreditCardLoanUpdateView(StaffRequiredMixin, UpdateView):
    model = CreditCardLoan
    form_class = CreditCardLoanForm
    template_name = 'bankloan/loan_form.html'

    def get_success_url(self):
        return reverse_lazy('bankloan:loan_detail', kwargs={'pk': self.object.pk})


class CreditCardLoanDeleteView(AdminRequiredMixin, DeleteView):
    model = CreditCardLoan
    template_name = 'bankloan/loan_confirm_delete.html'
    success_url = reverse_lazy('bankloan:loan_list')


class CreditCardLoanLedgerCreateView(StaffRequiredMixin, CreateView):
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


@login_required
def credit_card_loan_ledger_pdf(request, pk):
    loan = get_object_or_404(CreditCardLoan, pk=pk)
    ledger_entries = loan.ledger_entries.order_by('-transaction_date', '-id')

    company_info = get_company_info()
    context = {
        'loan': loan,
        'ledger_entries': ledger_entries,
        'total_disbursed': loan.get_total_disbursed(),
        'total_paid': loan.get_total_paid(),
        'extra_paid': loan.get_total_interest_paid(),
        'outstanding_principal': loan.get_outstanding_principal(),
        **company_info,
    }

    template = get_template('bankloan/loan_ledger_pdf.html')
    html = template.render(context)

    filename = f"cc_loan_ledger_{loan.deal_number}.pdf"
    return html_to_pdf_response(html, filename)
