from django.conf import settings
from django.db import migrations, models
import django.utils.timezone
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('bank_name', models.CharField(blank=True, max_length=150)),
                ('account_number', models.CharField(blank=True, max_length=100)),
                ('account_type', models.CharField(choices=[('current', 'Current'), ('savings', 'Savings'), ('credit_card', 'Credit Card'), ('loan', 'Loan'), ('other', 'Other')], default='current', max_length=20)),
                ('opening_balance', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('current_balance', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Bank Account',
                'verbose_name_plural': 'Bank Accounts',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='CreditCardLoan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deal_number', models.CharField(max_length=100, unique=True)),
                ('lender_name', models.CharField(blank=True, max_length=150)),
                ('principal_amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('start_date', models.DateField(default=django.utils.timezone.now)),
                ('status', models.CharField(choices=[('active', 'Active'), ('closed', 'Closed')], default='active', max_length=10)),
                ('closed_date', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('bank_account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='credit_card_loans', to='bankloan.bankaccount')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_cc_loans', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Credit Card Loan',
                'verbose_name_plural': 'Credit Card Loans',
                'ordering': ['-start_date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CreditCardLoanLedger',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entry_type', models.CharField(choices=[('disbursement', 'Disbursement'), ('payment', 'Payment')], max_length=20)),
                ('transaction_date', models.DateField(default=django.utils.timezone.now)),
                ('description', models.TextField(blank=True)),
                ('principal_amount', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('principal_paid', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('interest_paid', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('total_paid', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('payment_rate_percent', models.DecimalField(blank=True, decimal_places=3, help_text='Optional dynamic interest rate for this payment', max_digits=7, null=True)),
                ('days_from_last_payment', models.PositiveIntegerField(blank=True, help_text='Days covered by this interest calculation', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('loan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ledger_entries', to='bankloan.creditcardloan')),
            ],
            options={
                'verbose_name': 'Credit Card Loan Ledger',
                'verbose_name_plural': 'Credit Card Loan Ledgers',
                'ordering': ['-transaction_date', '-id'],
            },
        ),
    ]
