from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.utils import timezone
from decimal import Decimal
from datetime import date, datetime
from .models import Customer, CustomerLedger, CustomerCommitment
from .forms import CustomerForm, CustomerLedgerForm, CustomerCommitmentForm, SetOpeningBalanceForm
from .views import *


class CustomerModelTest(TestCase):
    """Test cases for Customer model"""
    
    def setUp(self):
        """Set up test data"""
        self.customer = Customer.objects.create(
            name="Test Customer",
            customer_type="retail",
            contact_person="John Doe",
            phone="1234567890",
            address="123 Test Street",
            credit_limit=Decimal('1000.00'),
            opening_balance=Decimal('0.00'),
            current_balance=Decimal('0.00'),
            is_active=True
        )
    
    def test_customer_creation(self):
        """Test customer creation"""
        self.assertEqual(self.customer.name, "Test Customer")
        self.assertEqual(self.customer.customer_type, "retail")
        self.assertEqual(self.customer.contact_person, "John Doe")
        self.assertEqual(self.customer.phone, "1234567890")
        self.assertEqual(self.customer.address, "123 Test Street")
        self.assertEqual(self.customer.credit_limit, Decimal('1000.00'))
        self.assertEqual(self.customer.opening_balance, Decimal('0.00'))
        self.assertEqual(self.customer.current_balance, Decimal('0.00'))
        self.assertTrue(self.customer.is_active)
        self.assertIsNotNone(self.customer.created_at)
        self.assertIsNotNone(self.customer.updated_at)
    
    def test_customer_str_representation(self):
        """Test string representation of customer"""
        expected = "Test Customer (retail)"
        self.assertEqual(str(self.customer), expected)
    
    def test_customer_meta(self):
        """Test customer meta options"""
        self.assertEqual(Customer._meta.verbose_name, "Customer")
        self.assertEqual(Customer._meta.verbose_name_plural, "Customers")
    
    def test_customer_choices(self):
        """Test customer type choices"""
        choices = [choice[0] for choice in Customer.CUSTOMER_TYPES]
        self.assertIn('retail', choices)
        self.assertIn('wholesale', choices)
    
    def test_set_opening_balance(self):
        """Test setting opening balance"""
        user = User.objects.create_user(username='testuser', password='testpass')
        amount = Decimal('500.00')
        
        self.customer.set_opening_balance(amount, user=user)
        
        # Check customer balance is updated
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.opening_balance, amount)
        self.assertEqual(self.customer.current_balance, amount)
        
        # Check ledger entry is created
        ledger_entry = CustomerLedger.objects.get(customer=self.customer)
        self.assertEqual(ledger_entry.transaction_type, 'opening_balance')
        self.assertEqual(ledger_entry.amount, amount)
        self.assertEqual(ledger_entry.created_by, user)
        self.assertEqual(ledger_entry.reference, "OPENING")


class CustomerLedgerModelTest(TestCase):
    """Test cases for CustomerLedger model"""
    
    def setUp(self):
        """Set up test data"""
        self.customer = Customer.objects.create(
            name="Test Customer",
            customer_type="retail"
        )
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        self.ledger_entry = CustomerLedger.objects.create(
            customer=self.customer,
            transaction_type='sale',
            amount=Decimal('100.00'),
            description="Test sale transaction",
            reference="TEST-001",
            transaction_date=timezone.now(),
            payment_method='cash',
            created_by=self.user
        )
    
    def test_ledger_entry_creation(self):
        """Test ledger entry creation"""
        self.assertEqual(self.ledger_entry.customer, self.customer)
        self.assertEqual(self.ledger_entry.transaction_type, 'sale')
        self.assertEqual(self.ledger_entry.amount, Decimal('100.00'))
        self.assertEqual(self.ledger_entry.description, "Test sale transaction")
        self.assertEqual(self.ledger_entry.reference, "TEST-001")
        self.assertEqual(self.ledger_entry.payment_method, 'cash')
        self.assertEqual(self.ledger_entry.created_by, self.user)
        self.assertIsNotNone(self.ledger_entry.created_at)
    
    def test_ledger_entry_str_representation(self):
        """Test string representation of ledger entry"""
        expected = "Test Customer - sale - 100.00"
        self.assertEqual(str(self.ledger_entry), expected)
    
    def test_ledger_entry_meta(self):
        """Test ledger entry meta options"""
        self.assertEqual(CustomerLedger._meta.verbose_name, "Customer Ledger")
        self.assertEqual(CustomerLedger._meta.verbose_name_plural, "Customer Ledgers")
    
    def test_transaction_type_choices(self):
        """Test transaction type choices"""
        choices = [choice[0] for choice in CustomerLedger.TRANSACTION_TYPES]
        expected_types = ['opening_balance', 'sale', 'return', 'payment', 'adjustment', 'commission']
        for transaction_type in expected_types:
            self.assertIn(transaction_type, choices)
    
    def test_payment_method_choices(self):
        """Test payment method choices"""
        choices = [choice[0] for choice in CustomerLedger.PAYMENT_METHODS]
        expected_methods = ['cash', 'bank_transfer', 'cheque', 'other']
        for payment_method in expected_methods:
            self.assertIn(payment_method, choices)


class CustomerCommitmentModelTest(TestCase):
    """Test cases for CustomerCommitment model"""
    
    def setUp(self):
        """Set up test data"""
        self.customer = Customer.objects.create(
            name="Test Customer",
            customer_type="retail"
        )
        
        self.commitment = CustomerCommitment.objects.create(
            customer=self.customer,
            commitment_date=date.today(),
            amount=Decimal('500.00'),
            description="Test commitment",
            is_reminded=False,
            is_fulfilled=False
        )
    
    def test_commitment_creation(self):
        """Test commitment creation"""
        self.assertEqual(self.commitment.customer, self.customer)
        self.assertEqual(self.commitment.commitment_date, date.today())
        self.assertEqual(self.commitment.amount, Decimal('500.00'))
        self.assertEqual(self.commitment.description, "Test commitment")
        self.assertFalse(self.commitment.is_reminded)
        self.assertFalse(self.commitment.is_fulfilled)
        self.assertIsNotNone(self.commitment.created_at)
    
    def test_commitment_str_representation(self):
        """Test string representation of commitment"""
        expected = f"Test Customer - {date.today()} - 500.00"
        self.assertEqual(str(self.commitment), expected)
    
    def test_commitment_meta(self):
        """Test commitment meta options"""
        self.assertEqual(CustomerCommitment._meta.verbose_name, "Customer Commitment")
        self.assertEqual(CustomerCommitment._meta.verbose_name_plural, "Customer Commitments")


class CustomerFormTest(TestCase):
    """Test cases for CustomerForm"""
    
    def test_customer_form_valid_data(self):
        """Test customer form with valid data"""
        form_data = {
            'name': 'Test Customer',
            'customer_type': 'retail',
            'contact_person': 'John Doe',
            'phone': '1234567890',
            'address': '123 Test Street',
            'credit_limit': '1000.00',
            'is_active': True
        }
        form = CustomerForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_customer_form_required_fields(self):
        """Test customer form required fields"""
        form = CustomerForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('customer_type', form.errors)
    
    def test_customer_form_save(self):
        """Test customer form save"""
        form_data = {
            'name': 'Test Customer',
            'customer_type': 'retail',
            'contact_person': 'John Doe',
            'phone': '1234567890',
            'address': '123 Test Street',
            'credit_limit': '1000.00',
            'is_active': True
        }
        form = CustomerForm(data=form_data)
        self.assertTrue(form.is_valid())
        customer = form.save()
        self.assertEqual(customer.name, 'Test Customer')
        self.assertEqual(customer.customer_type, 'retail')


class CustomerLedgerFormTest(TestCase):
    """Test cases for CustomerLedgerForm"""
    
    def test_ledger_form_valid_data(self):
        """Test ledger form with valid data"""
        form_data = {
            'transaction_type': 'sale',
            'amount': '100.00',
            'description': 'Test transaction',
            'reference': 'TEST-001',
            'transaction_date': date.today(),
            'payment_method': 'cash'
        }
        form = CustomerLedgerForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_ledger_form_required_fields(self):
        """Test ledger form required fields"""
        form = CustomerLedgerForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('transaction_type', form.errors)
        self.assertIn('amount', form.errors)
        self.assertIn('description', form.errors)
        self.assertIn('transaction_date', form.errors)
    
    def test_ledger_form_clean_transaction_date(self):
        """Test ledger form transaction date cleaning"""
        form_data = {
            'transaction_type': 'sale',
            'amount': '100.00',
            'description': 'Test transaction',
            'transaction_date': date.today()
        }
        form = CustomerLedgerForm(data=form_data)
        self.assertTrue(form.is_valid())
        cleaned_date = form.clean_transaction_date()
        self.assertIsInstance(cleaned_date, datetime)


class CustomerCommitmentFormTest(TestCase):
    """Test cases for CustomerCommitmentForm"""
    
    def setUp(self):
        """Set up test data"""
        self.customer = Customer.objects.create(
            name="Test Customer",
            customer_type="retail"
        )
    
    def test_commitment_form_valid_data(self):
        """Test commitment form with valid data"""
        form_data = {
            'customer': self.customer.id,
            'commitment_date': date.today(),
            'amount': '500.00',
            'description': 'Test commitment'
        }
        form = CustomerCommitmentForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_commitment_form_save(self):
        """Test commitment form save"""
        form_data = {
            'customer': self.customer.id,
            'commitment_date': date.today(),
            'amount': '500.00',
            'description': 'Test commitment'
        }
        form = CustomerCommitmentForm(data=form_data)
        self.assertTrue(form.is_valid())
        commitment = form.save()
        self.assertEqual(commitment.customer, self.customer)
        self.assertEqual(commitment.amount, Decimal('500.00'))


class SetOpeningBalanceFormTest(TestCase):
    """Test cases for SetOpeningBalanceForm"""
    
    def test_opening_balance_form_valid_data(self):
        """Test opening balance form with valid data"""
        form_data = {
            'amount': '1000.00',
            'description': 'Opening balance'
        }
        form = SetOpeningBalanceForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_opening_balance_form_required_amount(self):
        """Test opening balance form required amount field"""
        form = SetOpeningBalanceForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)


class CustomerViewsTest(TestCase):
    """Test cases for Customer views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        
        self.customer = Customer.objects.create(
            name="Test Customer",
            customer_type="retail",
            contact_person="John Doe",
            phone="1234567890",
            address="123 Test Street",
            credit_limit=Decimal('1000.00')
        )
    
    def test_customer_list_view(self):
        """Test customer list view"""
        response = self.client.get(reverse('customers:customer_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Customer")
        self.assertIn('customers', response.context)
        self.assertIn('total_receivable', response.context)
        self.assertIn('total_payable', response.context)
        self.assertIn('active_customers', response.context)
    
    def test_customer_detail_view(self):
        """Test customer detail view"""
        response = self.client.get(reverse('customers:customer_detail', kwargs={'pk': self.customer.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Customer")
    
    def test_customer_create_view_get(self):
        """Test customer create view GET"""
        response = self.client.get(reverse('customers:customer_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
    
    def test_customer_create_view_post(self):
        """Test customer create view POST"""
        form_data = {
            'name': 'New Customer',
            'customer_type': 'retail',
            'contact_person': 'Jane Doe',
            'phone': '0987654321',
            'address': '456 New Street',
            'credit_limit': '2000.00',
            'is_active': True
        }
        response = self.client.post(reverse('customers:customer_create'), form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Check if customer was created
        self.assertTrue(Customer.objects.filter(name='New Customer').exists())
    
    def test_customer_update_view_get(self):
        """Test customer update view GET"""
        response = self.client.get(reverse('customers:customer_edit', kwargs={'pk': self.customer.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
    
    def test_customer_update_view_post(self):
        """Test customer update view POST"""
        form_data = {
            'name': 'Updated Customer',
            'customer_type': 'wholesale',
            'contact_person': 'John Updated',
            'phone': '1111111111',
            'address': '789 Updated Street',
            'credit_limit': '3000.00',
            'is_active': True
        }
        response = self.client.post(reverse('customers:customer_edit', kwargs={'pk': self.customer.pk}), form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        
        # Check if customer was updated
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.name, 'Updated Customer')
        self.assertEqual(self.customer.customer_type, 'wholesale')
    
    def test_customer_delete_view_get(self):
        """Test customer delete view GET"""
        response = self.client.get(reverse('customers:customer_delete', kwargs={'pk': self.customer.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Confirm Delete')
    
    def test_customer_delete_view_post(self):
        """Test customer delete view POST"""
        response = self.client.post(reverse('customers:customer_delete', kwargs={'pk': self.customer.pk}))
        self.assertEqual(response.status_code, 302)  # Redirect after successful deletion
        
        # Check if customer was deleted
        self.assertFalse(Customer.objects.filter(pk=self.customer.pk).exists())
    
    def test_customer_ledger_detail_view(self):
        """Test customer ledger detail view"""
        response = self.client.get(reverse('customers:customer_ledger_detail', kwargs={'pk': self.customer.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('transactions', response.context)
        self.assertIn('total_debit', response.context)
        self.assertIn('total_credit', response.context)
        self.assertIn('opening_balance', response.context)
        self.assertIn('current_balance', response.context)
    
    def test_customer_ledger_create_view_get(self):
        """Test customer ledger create view GET"""
        response = self.client.get(reverse('customers:customer_ledger_create', kwargs={'pk': self.customer.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        self.assertIn('customer_id', response.context)
    
    def test_customer_ledger_create_view_post(self):
        """Test customer ledger create view POST"""
        form_data = {
            'transaction_type': 'sale',
            'amount': '100.00',
            'description': 'Test sale',
            'reference': 'TEST-001',
            'transaction_date': date.today(),
            'payment_method': 'cash'
        }
        response = self.client.post(reverse('customers:customer_ledger_create', kwargs={'pk': self.customer.pk}), form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Check if ledger entry was created
        self.assertTrue(CustomerLedger.objects.filter(customer=self.customer).exists())
    
    def test_set_opening_balance_view_get(self):
        """Test set opening balance view GET"""
        response = self.client.get(reverse('customers:customer_opening_balance', kwargs={'pk': self.customer.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        self.assertIn('customer', response.context)
    
    def test_set_opening_balance_view_post(self):
        """Test set opening balance view POST"""
        form_data = {
            'amount': '500.00',
            'description': 'Opening balance'
        }
        response = self.client.post(reverse('customers:customer_opening_balance', kwargs={'pk': self.customer.pk}), form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Check if opening balance was set
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.opening_balance, Decimal('500.00'))
        self.assertEqual(self.customer.current_balance, Decimal('500.00'))
        
        # Check if ledger entry was created
        self.assertTrue(CustomerLedger.objects.filter(
            customer=self.customer,
            transaction_type='opening_balance'
        ).exists())


class CustomerCommitmentViewsTest(TestCase):
    """Test cases for CustomerCommitment views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        
        self.customer = Customer.objects.create(
            name="Test Customer",
            customer_type="retail"
        )
        
        self.commitment = CustomerCommitment.objects.create(
            customer=self.customer,
            commitment_date=date.today(),
            amount=Decimal('500.00'),
            description="Test commitment"
        )
    
    def test_commitment_list_view(self):
        """Test commitment list view"""
        response = self.client.get(reverse('customers:commitment_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('items', response.context)
    
    def test_commitment_create_view_get(self):
        """Test commitment create view GET"""
        response = self.client.get(reverse('customers:commitment_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        self.assertIn('customers', response.context)
    
    def test_commitment_create_view_post(self):
        """Test commitment create view POST"""
        form_data = {
            'customer': self.customer.id,
            'commitment_date': date.today(),
            'amount': '1000.00',
            'description': 'New commitment'
        }
        response = self.client.post(reverse('customers:commitment_create'), form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Check if commitment was created
        self.assertTrue(CustomerCommitment.objects.filter(
            customer=self.customer,
            amount=Decimal('1000.00')
        ).exists())
    
    def test_commitment_update_view_get(self):
        """Test commitment update view GET"""
        response = self.client.get(reverse('customers:commitment_edit', kwargs={'pk': self.commitment.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        self.assertIn('customers', response.context)
    
    def test_commitment_update_view_post(self):
        """Test commitment update view POST"""
        form_data = {
            'customer': self.customer.id,
            'commitment_date': date.today(),
            'amount': '750.00',
            'description': 'Updated commitment'
        }
        response = self.client.post(reverse('customers:commitment_edit', kwargs={'pk': self.commitment.pk}), form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        
        # Check if commitment was updated
        self.commitment.refresh_from_db()
        self.assertEqual(self.commitment.amount, Decimal('750.00'))
        self.assertEqual(self.commitment.description, 'Updated commitment')
    
    def test_commitment_delete_view_get(self):
        """Test commitment delete view GET"""
        response = self.client.get(reverse('customers:commitment_delete', kwargs={'pk': self.commitment.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Delete Commitment')
    
    def test_commitment_delete_view_post(self):
        """Test commitment delete view POST"""
        response = self.client.post(reverse('customers:commitment_delete', kwargs={'pk': self.commitment.pk}))
        self.assertEqual(response.status_code, 302)  # Redirect after successful deletion
        
        # Check if commitment was deleted
        self.assertFalse(CustomerCommitment.objects.filter(pk=self.commitment.pk).exists())


class CustomerURLsTest(TestCase):
    """Test cases for Customer URLs"""
    
    def test_customer_list_url(self):
        """Test customer list URL"""
        url = reverse('customers:customer_list')
        self.assertEqual(url, '/customers/')
    
    def test_customer_create_url(self):
        """Test customer create URL"""
        url = reverse('customers:customer_create')
        self.assertEqual(url, '/customers/create/')
    
    def test_customer_detail_url(self):
        """Test customer detail URL"""
        url = reverse('customers:customer_detail', kwargs={'pk': 1})
        self.assertEqual(url, '/customers/1/')
    
    def test_customer_edit_url(self):
        """Test customer edit URL"""
        url = reverse('customers:customer_edit', kwargs={'pk': 1})
        self.assertEqual(url, '/customers/1/edit/')
    
    def test_customer_delete_url(self):
        """Test customer delete URL"""
        url = reverse('customers:customer_delete', kwargs={'pk': 1})
        self.assertEqual(url, '/customers/1/delete/')
    
    def test_customer_ledger_detail_url(self):
        """Test customer ledger detail URL"""
        url = reverse('customers:customer_ledger_detail', kwargs={'pk': 1})
        self.assertEqual(url, '/customers/1/ledger/')
    
    def test_customer_ledger_create_url(self):
        """Test customer ledger create URL"""
        url = reverse('customers:customer_ledger_create', kwargs={'pk': 1})
        self.assertEqual(url, '/customers/1/ledger/create/')
    
    def test_customer_opening_balance_url(self):
        """Test customer opening balance URL"""
        url = reverse('customers:customer_opening_balance', kwargs={'pk': 1})
        self.assertEqual(url, '/customers/1/opening-balance/')
    
    def test_commitment_list_url(self):
        """Test commitment list URL"""
        url = reverse('customers:commitment_list')
        self.assertEqual(url, '/customers/commitment/')
    
    def test_commitment_create_url(self):
        """Test commitment create URL"""
        url = reverse('customers:commitment_create')
        self.assertEqual(url, '/customers/commitment/create/')
    
    def test_commitment_edit_url(self):
        """Test commitment edit URL"""
        url = reverse('customers:commitment_edit', kwargs={'pk': 1})
        self.assertEqual(url, '/customers/commitment/1/edit/')
    
    def test_commitment_delete_url(self):
        """Test commitment delete URL"""
        url = reverse('customers:commitment_delete', kwargs={'pk': 1})
        self.assertEqual(url, '/customers/commitment/1/delete/')


class CustomerBusinessLogicTest(TestCase):
    """Test cases for Customer business logic"""
    
    def setUp(self):
        """Set up test data"""
        self.customer = Customer.objects.create(
            name="Test Customer",
            customer_type="retail",
            credit_limit=Decimal('1000.00')
        )
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_balance_calculation_after_sale(self):
        """Test balance calculation after sale transaction"""
        # Create a sale transaction
        CustomerLedger.objects.create(
            customer=self.customer,
            transaction_type='sale',
            amount=Decimal('100.00'),
            description="Test sale",
            transaction_date=timezone.now(),
            created_by=self.user
        )
        
        # Update customer balance (simulating the view logic)
        ledger_entries = CustomerLedger.objects.filter(customer=self.customer)
        total_balance = Decimal('0.00')
        for entry in ledger_entries:
            if entry.transaction_type in ['sale', 'opening_balance']:
                total_balance += entry.amount
            elif entry.transaction_type in ['payment', 'return']:
                total_balance -= entry.amount
            elif entry.transaction_type == 'adjustment':
                total_balance += entry.amount
        
        self.customer.current_balance = total_balance
        self.customer.save()
        
        self.assertEqual(self.customer.current_balance, Decimal('100.00'))
    
    def test_balance_calculation_after_payment(self):
        """Test balance calculation after payment transaction"""
        # Set opening balance
        self.customer.set_opening_balance(Decimal('200.00'), self.user)
        
        # Create a payment transaction
        CustomerLedger.objects.create(
            customer=self.customer,
            transaction_type='payment',
            amount=Decimal('50.00'),
            description="Test payment",
            transaction_date=timezone.now(),
            created_by=self.user
        )
        
        # Update customer balance
        ledger_entries = CustomerLedger.objects.filter(customer=self.customer)
        total_balance = Decimal('0.00')
        for entry in ledger_entries:
            if entry.transaction_type in ['sale', 'opening_balance']:
                total_balance += entry.amount
            elif entry.transaction_type in ['payment', 'return']:
                total_balance -= entry.amount
            elif entry.transaction_type == 'adjustment':
                total_balance += entry.amount
        
        self.customer.current_balance = total_balance
        self.customer.save()
        
        self.assertEqual(self.customer.current_balance, Decimal('150.00'))
    
    def test_balance_calculation_with_multiple_transactions(self):
        """Test balance calculation with multiple transactions"""
        # Set opening balance
        self.customer.set_opening_balance(Decimal('100.00'), self.user)
        
        # Create multiple transactions
        CustomerLedger.objects.create(
            customer=self.customer,
            transaction_type='sale',
            amount=Decimal('200.00'),
            description="Sale 1",
            transaction_date=timezone.now(),
            created_by=self.user
        )
        
        CustomerLedger.objects.create(
            customer=self.customer,
            transaction_type='payment',
            amount=Decimal('50.00'),
            description="Payment 1",
            transaction_date=timezone.now(),
            created_by=self.user
        )
        
        CustomerLedger.objects.create(
            customer=self.customer,
            transaction_type='sale',
            amount=Decimal('150.00'),
            description="Sale 2",
            transaction_date=timezone.now(),
            created_by=self.user
        )
        
        # Update customer balance
        ledger_entries = CustomerLedger.objects.filter(customer=self.customer)
        total_balance = Decimal('0.00')
        for entry in ledger_entries:
            if entry.transaction_type in ['sale', 'opening_balance']:
                total_balance += entry.amount
            elif entry.transaction_type in ['payment', 'return']:
                total_balance -= entry.amount
            elif entry.transaction_type == 'adjustment':
                total_balance += entry.amount
        
        self.customer.current_balance = total_balance
        self.customer.save()
        
        # Expected balance: 100 (opening) + 200 (sale 1) - 50 (payment) + 150 (sale 2) = 400
        self.assertEqual(self.customer.current_balance, Decimal('400.00'))
    
    def test_credit_limit_validation(self):
        """Test credit limit validation logic"""
        # Set a low credit limit
        self.customer.credit_limit = Decimal('100.00')
        self.customer.save()
        
        # Set opening balance within limit
        self.customer.set_opening_balance(Decimal('50.00'), self.user)
        self.assertTrue(self.customer.current_balance <= self.customer.credit_limit)
        
        # Try to exceed credit limit
        CustomerLedger.objects.create(
            customer=self.customer,
            transaction_type='sale',
            amount=Decimal('200.00'),
            description="Sale exceeding limit",
            transaction_date=timezone.now(),
            created_by=self.user
        )
        
        # Update balance
        ledger_entries = CustomerLedger.objects.filter(customer=self.customer)
        total_balance = Decimal('0.00')
        for entry in ledger_entries:
            if entry.transaction_type in ['sale', 'opening_balance']:
                total_balance += entry.amount
            elif entry.transaction_type in ['payment', 'return']:
                total_balance -= entry.amount
            elif entry.transaction_type == 'adjustment':
                total_balance += entry.amount
        
        self.customer.current_balance = total_balance
        self.customer.save()
        
        # Balance should exceed credit limit
        self.assertTrue(self.customer.current_balance > self.customer.credit_limit)
    
    def test_opening_balance_creates_ledger_entry(self):
        """Test that setting opening balance creates a ledger entry"""
        amount = Decimal('500.00')
        self.customer.set_opening_balance(amount, self.user)
        
        # Check that ledger entry was created
        ledger_entry = CustomerLedger.objects.get(
            customer=self.customer,
            transaction_type='opening_balance'
        )
        
        self.assertEqual(ledger_entry.amount, amount)
        self.assertEqual(ledger_entry.reference, "OPENING")
        self.assertEqual(ledger_entry.created_by, self.user)
        self.assertIn("Opening balance set to", ledger_entry.description)


class CustomerIntegrationTest(TestCase):
    """Integration tests for Customer module"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
    
    def test_complete_customer_workflow(self):
        """Test complete customer workflow from creation to ledger management"""
        # 1. Create a customer
        form_data = {
            'name': 'Integration Test Customer',
            'customer_type': 'retail',
            'contact_person': 'Test Person',
            'phone': '1234567890',
            'address': 'Test Address',
            'credit_limit': '2000.00',
            'is_active': True
        }
        response = self.client.post(reverse('customers:customer_create'), form_data)
        self.assertEqual(response.status_code, 302)
        
        customer = Customer.objects.get(name='Integration Test Customer')
        
        # 2. Set opening balance
        opening_balance_data = {
            'amount': '500.00',
            'description': 'Initial balance'
        }
        response = self.client.post(
            reverse('customers:customer_opening_balance', kwargs={'pk': customer.pk}),
            opening_balance_data
        )
        self.assertEqual(response.status_code, 302)
        
        customer.refresh_from_db()
        self.assertEqual(customer.opening_balance, Decimal('500.00'))
        self.assertEqual(customer.current_balance, Decimal('500.00'))
        
        # 3. Add a sale transaction
        sale_data = {
            'transaction_type': 'sale',
            'amount': '200.00',
            'description': 'Test sale',
            'reference': 'SALE-001',
            'transaction_date': date.today(),
            'payment_method': 'cash'
        }
        response = self.client.post(
            reverse('customers:customer_ledger_create', kwargs={'pk': customer.pk}),
            sale_data
        )
        self.assertEqual(response.status_code, 302)
        
        # 4. Add a payment transaction
        payment_data = {
            'transaction_type': 'payment',
            'amount': '100.00',
            'description': 'Test payment',
            'reference': 'PAY-001',
            'transaction_date': date.today(),
            'payment_method': 'cash'
        }
        response = self.client.post(
            reverse('customers:customer_ledger_create', kwargs={'pk': customer.pk}),
            payment_data
        )
        self.assertEqual(response.status_code, 302)
        
        # 5. Check final balance
        customer.refresh_from_db()
        # Expected: 500 (opening) + 200 (sale) - 100 (payment) = 600
        self.assertEqual(customer.current_balance, Decimal('600.00'))
        
        # 6. Create a commitment
        commitment_data = {
            'customer': customer.id,
            'commitment_date': date.today(),
            'amount': '300.00',
            'description': 'Test commitment'
        }
        response = self.client.post(reverse('customers:commitment_create'), commitment_data)
        self.assertEqual(response.status_code, 302)
        
        # 7. Verify commitment was created
        self.assertTrue(CustomerCommitment.objects.filter(
            customer=customer,
            amount=Decimal('300.00')
        ).exists())
    
    def test_customer_ledger_detail_integration(self):
        """Test customer ledger detail view with all transaction types"""
        # Create customer and transactions
        customer = Customer.objects.create(
            name="Ledger Test Customer",
            customer_type="retail"
        )
        
        # Set opening balance
        customer.set_opening_balance(Decimal('1000.00'), self.user)
        
        # Create various transactions
        CustomerLedger.objects.create(
            customer=customer,
            transaction_type='sale',
            amount=Decimal('500.00'),
            description="Sale transaction",
            reference="SALE-001",
            transaction_date=timezone.now(),
            created_by=self.user
        )
        
        CustomerLedger.objects.create(
            customer=customer,
            transaction_type='payment',
            amount=Decimal('200.00'),
            description="Payment transaction",
            reference="PAY-001",
            transaction_date=timezone.now(),
            payment_method='cash',
            created_by=self.user
        )
        
        CustomerLedger.objects.create(
            customer=customer,
            transaction_type='adjustment',
            amount=Decimal('50.00'),
            description="Adjustment transaction",
            reference="ADJ-001",
            transaction_date=timezone.now(),
            created_by=self.user
        )
        
        # Test ledger detail view
        response = self.client.get(reverse('customers:customer_ledger_detail', kwargs={'pk': customer.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Check context data
        self.assertIn('transactions', response.context)
        self.assertIn('total_debit', response.context)
        self.assertIn('total_credit', response.context)
        self.assertIn('opening_balance', response.context)
        self.assertIn('current_balance', response.context)
        
        # Verify transaction count
        transactions = response.context['transactions']
        self.assertGreaterEqual(len(transactions), 4)  # Opening balance + 3 transactions


# Tests should be run using Django's manage.py test command
# or the custom run_customer_tests.py script
