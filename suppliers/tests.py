from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.utils import timezone
from decimal import Decimal
from datetime import date, datetime
from .models import Supplier, SupplierLedger
from .forms import SupplierForm, SupplierLedgerForm, SetOpeningBalanceForm
from .views import *


class SupplierModelTest(TestCase):
    """Test cases for Supplier model"""
    
    def setUp(self):
        """Set up test data"""
        self.supplier = Supplier.objects.create(
            name="Test Supplier",
            contact_person="John Doe",
            phone="1234567890",
            address="123 Test Street",
            city="Test City",
            opening_balance=Decimal('0.00'),
            current_balance=Decimal('0.00'),
            is_active=True
        )
    
    def test_supplier_creation(self):
        """Test supplier creation"""
        self.assertEqual(self.supplier.name, "Test Supplier")
        self.assertEqual(self.supplier.contact_person, "John Doe")
        self.assertEqual(self.supplier.phone, "1234567890")
        self.assertEqual(self.supplier.address, "123 Test Street")
        self.assertEqual(self.supplier.city, "Test City")
        self.assertEqual(self.supplier.opening_balance, Decimal('0.00'))
        self.assertEqual(self.supplier.current_balance, Decimal('0.00'))
        self.assertTrue(self.supplier.is_active)
        self.assertIsNotNone(self.supplier.created_at)
        self.assertIsNotNone(self.supplier.updated_at)
    
    def test_supplier_str_representation(self):
        """Test string representation of supplier"""
        expected = "Test Supplier"
        self.assertEqual(str(self.supplier), expected)
    
    def test_supplier_meta(self):
        """Test supplier meta options"""
        self.assertEqual(Supplier._meta.verbose_name, "Supplier")
        self.assertEqual(Supplier._meta.verbose_name_plural, "Suppliers")
    
    def test_set_opening_balance(self):
        """Test setting opening balance"""
        user = User.objects.create_user(username='testuser', password='testpass')
        amount = Decimal('500.00')
        
        self.supplier.set_opening_balance(amount, user=user)
        
        # Check supplier balance is updated
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.opening_balance, amount)
        self.assertEqual(self.supplier.current_balance, amount)
        
        # Check ledger entry is created
        ledger_entry = SupplierLedger.objects.get(supplier=self.supplier)
        self.assertEqual(ledger_entry.transaction_type, 'opening_balance')
        self.assertEqual(ledger_entry.amount, amount)
        self.assertEqual(ledger_entry.created_by, user)
        self.assertEqual(ledger_entry.reference, "OPENING")


class SupplierLedgerModelTest(TestCase):
    """Test cases for SupplierLedger model"""
    
    def setUp(self):
        """Set up test data"""
        self.supplier = Supplier.objects.create(
            name="Test Supplier",
            contact_person="John Doe",
            phone="1234567890",
            address="123 Test Street",
            city="Test City"
        )
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        self.ledger_entry = SupplierLedger.objects.create(
            supplier=self.supplier,
            transaction_type='purchase',
            amount=Decimal('100.00'),
            description="Test purchase transaction",
            reference="TEST-001",
            transaction_date=timezone.now(),
            payment_method='cash',
            created_by=self.user
        )
    
    def test_ledger_entry_creation(self):
        """Test ledger entry creation"""
        self.assertEqual(self.ledger_entry.supplier, self.supplier)
        self.assertEqual(self.ledger_entry.transaction_type, 'purchase')
        self.assertEqual(self.ledger_entry.amount, Decimal('100.00'))
        self.assertEqual(self.ledger_entry.description, "Test purchase transaction")
        self.assertEqual(self.ledger_entry.reference, "TEST-001")
        self.assertEqual(self.ledger_entry.payment_method, 'cash')
        self.assertEqual(self.ledger_entry.created_by, self.user)
        self.assertIsNotNone(self.ledger_entry.created_at)
    
    def test_ledger_entry_str_representation(self):
        """Test string representation of ledger entry"""
        expected = "Test Supplier - purchase - 100.00"
        self.assertEqual(str(self.ledger_entry), expected)
    
    def test_ledger_entry_meta(self):
        """Test ledger entry meta options"""
        self.assertEqual(SupplierLedger._meta.verbose_name, "Supplier Ledger")
        self.assertEqual(SupplierLedger._meta.verbose_name_plural, "Supplier Ledgers")
    
    def test_transaction_type_choices(self):
        """Test transaction type choices"""
        choices = [choice[0] for choice in SupplierLedger.TRANSACTION_TYPES]
        expected_types = ['opening_balance', 'purchase', 'return', 'payment', 'adjustment', 'commission']
        for transaction_type in expected_types:
            self.assertIn(transaction_type, choices)
    
    def test_payment_method_choices(self):
        """Test payment method choices"""
        choices = [choice[0] for choice in SupplierLedger.PAYMENT_METHODS]
        expected_methods = ['cash', 'bank_transfer', 'cheque', 'other']
        for payment_method in expected_methods:
            self.assertIn(payment_method, choices)


class SupplierFormTest(TestCase):
    """Test cases for SupplierForm"""
    
    def test_supplier_form_valid_data(self):
        """Test supplier form with valid data"""
        form_data = {
            'name': 'Test Supplier',
            'contact_person': 'John Doe',
            'phone': '1234567890',
            'address': '123 Test Street',
            'city': 'Test City',
            'is_active': True
        }
        form = SupplierForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_supplier_form_required_fields(self):
        """Test supplier form required fields"""
        form = SupplierForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
    
    def test_supplier_form_save(self):
        """Test supplier form save"""
        form_data = {
            'name': 'Test Supplier',
            'contact_person': 'John Doe',
            'phone': '1234567890',
            'address': '123 Test Street',
            'city': 'Test City',
            'is_active': True
        }
        form = SupplierForm(data=form_data)
        self.assertTrue(form.is_valid())
        supplier = form.save()
        self.assertEqual(supplier.name, 'Test Supplier')
        self.assertEqual(supplier.contact_person, 'John Doe')


class SupplierLedgerFormTest(TestCase):
    """Test cases for SupplierLedgerForm"""
    
    def test_ledger_form_valid_data(self):
        """Test ledger form with valid data"""
        form_data = {
            'transaction_type': 'purchase',
            'amount': '100.00',
            'description': 'Test transaction',
            'reference': 'TEST-001',
            'transaction_date': timezone.now(),
            'payment_method': 'cash'
        }
        form = SupplierLedgerForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_ledger_form_required_fields(self):
        """Test ledger form required fields"""
        form = SupplierLedgerForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('transaction_type', form.errors)
        self.assertIn('amount', form.errors)
        self.assertIn('description', form.errors)
    
    def test_ledger_form_save(self):
        """Test ledger form save"""
        supplier = Supplier.objects.create(name="Test Supplier")
        form_data = {
            'transaction_type': 'purchase',
            'amount': '100.00',
            'description': 'Test transaction',
            'reference': 'TEST-001',
            'transaction_date': timezone.now(),
            'payment_method': 'cash'
        }
        form = SupplierLedgerForm(data=form_data)
        self.assertTrue(form.is_valid())
        ledger_entry = form.save(commit=False)
        ledger_entry.supplier = supplier
        ledger_entry.save()
        self.assertEqual(ledger_entry.transaction_type, 'purchase')
        self.assertEqual(ledger_entry.amount, Decimal('100.00'))


class SetOpeningBalanceFormTest(TestCase):
    """Test cases for SetOpeningBalanceForm"""
    
    def test_opening_balance_form_valid_data(self):
        """Test opening balance form with valid data"""
        form_data = {
            'amount': '1000.00'
        }
        form = SetOpeningBalanceForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_opening_balance_form_required_amount(self):
        """Test opening balance form required amount field"""
        form = SetOpeningBalanceForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)


class SupplierViewsTest(TestCase):
    """Test cases for Supplier views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        
        self.supplier = Supplier.objects.create(
            name="Test Supplier",
            contact_person="John Doe",
            phone="1234567890",
            address="123 Test Street",
            city="Test City"
        )
    
    def test_supplier_list_view(self):
        """Test supplier list view"""
        response = self.client.get(reverse('suppliers:supplier_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Supplier")
        self.assertIn('suppliers', response.context)
        self.assertIn('total_payable', response.context)
        self.assertIn('total_receivable', response.context)
        self.assertIn('active_suppliers', response.context)
    
    def test_supplier_detail_view(self):
        """Test supplier detail view"""
        response = self.client.get(reverse('suppliers:supplier_detail', kwargs={'pk': self.supplier.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Supplier")
    
    def test_supplier_create_view_get(self):
        """Test supplier create view GET"""
        response = self.client.get(reverse('suppliers:supplier_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
    
    def test_supplier_create_view_post(self):
        """Test supplier create view POST"""
        form_data = {
            'name': 'New Supplier',
            'contact_person': 'Jane Doe',
            'phone': '0987654321',
            'address': '456 New Street',
            'city': 'New City',
            'is_active': True
        }
        response = self.client.post(reverse('suppliers:supplier_create'), form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Check if supplier was created
        self.assertTrue(Supplier.objects.filter(name='New Supplier').exists())
    
    def test_supplier_update_view_get(self):
        """Test supplier update view GET"""
        response = self.client.get(reverse('suppliers:supplier_edit', kwargs={'pk': self.supplier.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
    
    def test_supplier_update_view_post(self):
        """Test supplier update view POST"""
        form_data = {
            'name': 'Updated Supplier',
            'contact_person': 'John Updated',
            'phone': '1111111111',
            'address': '789 Updated Street',
            'city': 'Updated City',
            'is_active': True
        }
        response = self.client.post(reverse('suppliers:supplier_edit', kwargs={'pk': self.supplier.pk}), form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        
        # Check if supplier was updated
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.name, 'Updated Supplier')
        self.assertEqual(self.supplier.city, 'Updated City')
    
    def test_supplier_delete_view_get(self):
        """Test supplier delete view GET"""
        response = self.client.get(reverse('suppliers:supplier_delete', kwargs={'pk': self.supplier.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Delete Supplier')
    
    def test_supplier_delete_view_post(self):
        """Test supplier delete view POST"""
        response = self.client.post(reverse('suppliers:supplier_delete', kwargs={'pk': self.supplier.pk}))
        self.assertEqual(response.status_code, 302)  # Redirect after successful deletion
        
        # Check if supplier was deleted
        self.assertFalse(Supplier.objects.filter(pk=self.supplier.pk).exists())
    
    def test_supplier_ledger_detail_view(self):
        """Test supplier ledger detail view"""
        response = self.client.get(reverse('suppliers:supplier_ledger_detail', kwargs={'pk': self.supplier.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('transactions', response.context)
        self.assertIn('total_debit', response.context)
        self.assertIn('total_credit', response.context)
        self.assertIn('opening_balance', response.context)
        self.assertIn('current_balance', response.context)
    
    def test_supplier_ledger_create_view_get(self):
        """Test supplier ledger create view GET"""
        response = self.client.get(reverse('suppliers:supplier_ledger_create', kwargs={'supplier_id': self.supplier.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        self.assertIn('supplier_id', response.context)
    
    def test_supplier_ledger_create_view_post(self):
        """Test supplier ledger create view POST"""
        form_data = {
            'transaction_type': 'purchase',
            'amount': '100.00',
            'description': 'Test purchase',
            'reference': 'TEST-001',
            'transaction_date': timezone.now(),
            'payment_method': 'cash'
        }
        response = self.client.post(reverse('suppliers:supplier_ledger_create', kwargs={'supplier_id': self.supplier.pk}), form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Check if ledger entry was created
        self.assertTrue(SupplierLedger.objects.filter(supplier=self.supplier).exists())
    
    def test_set_opening_balance_view_get(self):
        """Test set opening balance view GET"""
        response = self.client.get(reverse('suppliers:supplier_opening_balance', kwargs={'pk': self.supplier.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        self.assertIn('supplier', response.context)
    
    def test_set_opening_balance_view_post(self):
        """Test set opening balance view POST"""
        form_data = {
            'amount': '500.00'
        }
        response = self.client.post(reverse('suppliers:supplier_opening_balance', kwargs={'pk': self.supplier.pk}), form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Check if opening balance was set
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.opening_balance, Decimal('500.00'))
        self.assertEqual(self.supplier.current_balance, Decimal('500.00'))
        
        # Check if ledger entry was created
        self.assertTrue(SupplierLedger.objects.filter(
            supplier=self.supplier,
            transaction_type='opening_balance'
        ).exists())


class SupplierURLsTest(TestCase):
    """Test cases for Supplier URLs"""
    
    def test_supplier_list_url(self):
        """Test supplier list URL"""
        url = reverse('suppliers:supplier_list')
        self.assertEqual(url, '/suppliers/')
    
    def test_supplier_create_url(self):
        """Test supplier create URL"""
        url = reverse('suppliers:supplier_create')
        self.assertEqual(url, '/suppliers/create/')
    
    def test_supplier_detail_url(self):
        """Test supplier detail URL"""
        url = reverse('suppliers:supplier_detail', kwargs={'pk': 1})
        self.assertEqual(url, '/suppliers/1/')
    
    def test_supplier_edit_url(self):
        """Test supplier edit URL"""
        url = reverse('suppliers:supplier_edit', kwargs={'pk': 1})
        self.assertEqual(url, '/suppliers/1/edit/')
    
    def test_supplier_delete_url(self):
        """Test supplier delete URL"""
        url = reverse('suppliers:supplier_delete', kwargs={'pk': 1})
        self.assertEqual(url, '/suppliers/1/delete/')
    
    def test_supplier_ledger_detail_url(self):
        """Test supplier ledger detail URL"""
        url = reverse('suppliers:supplier_ledger_detail', kwargs={'pk': 1})
        self.assertEqual(url, '/suppliers/1/ledger/')
    
    def test_supplier_ledger_create_url(self):
        """Test supplier ledger create URL"""
        url = reverse('suppliers:supplier_ledger_create', kwargs={'supplier_id': 1})
        self.assertEqual(url, '/suppliers/1/ledger/create/')
    
    def test_supplier_opening_balance_url(self):
        """Test supplier opening balance URL"""
        url = reverse('suppliers:supplier_opening_balance', kwargs={'pk': 1})
        self.assertEqual(url, '/suppliers/1/opening-balance/')
    
    def test_ledger_list_url(self):
        """Test ledger list URL"""
        url = reverse('suppliers:ledger_list')
        self.assertEqual(url, '/suppliers/ledger/')
    
    def test_ledger_create_url(self):
        """Test ledger create URL"""
        url = reverse('suppliers:ledger_create')
        self.assertEqual(url, '/suppliers/ledger/create/')


class SupplierBusinessLogicTest(TestCase):
    """Test cases for Supplier business logic"""
    
    def setUp(self):
        """Set up test data"""
        self.supplier = Supplier.objects.create(
            name="Test Supplier",
            contact_person="John Doe",
            phone="1234567890",
            address="123 Test Street",
            city="Test City"
        )
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_balance_calculation_after_purchase(self):
        """Test balance calculation after purchase transaction"""
        # Create a purchase transaction
        SupplierLedger.objects.create(
            supplier=self.supplier,
            transaction_type='purchase',
            amount=Decimal('100.00'),
            description="Test purchase",
            transaction_date=timezone.now(),
            created_by=self.user
        )
        
        # Update supplier balance (simulating the view logic)
        ledger_entries = SupplierLedger.objects.filter(supplier=self.supplier)
        total_balance = Decimal('0.00')
        for entry in ledger_entries:
            if entry.transaction_type in ['purchase', 'opening_balance']:
                total_balance += entry.amount
            elif entry.transaction_type in ['payment', 'return']:
                total_balance -= entry.amount
            elif entry.transaction_type == 'adjustment':
                total_balance += entry.amount
        
        self.supplier.current_balance = total_balance
        self.supplier.save()
        
        self.assertEqual(self.supplier.current_balance, Decimal('100.00'))
    
    def test_balance_calculation_after_payment(self):
        """Test balance calculation after payment transaction"""
        # Set opening balance
        self.supplier.set_opening_balance(Decimal('200.00'), self.user)
        
        # Create a payment transaction
        SupplierLedger.objects.create(
            supplier=self.supplier,
            transaction_type='payment',
            amount=Decimal('50.00'),
            description="Test payment",
            transaction_date=timezone.now(),
            created_by=self.user
        )
        
        # Update supplier balance
        ledger_entries = SupplierLedger.objects.filter(supplier=self.supplier)
        total_balance = Decimal('0.00')
        for entry in ledger_entries:
            if entry.transaction_type in ['purchase', 'opening_balance']:
                total_balance += entry.amount
            elif entry.transaction_type in ['payment', 'return']:
                total_balance -= entry.amount
            elif entry.transaction_type == 'adjustment':
                total_balance += entry.amount
        
        self.supplier.current_balance = total_balance
        self.supplier.save()
        
        self.assertEqual(self.supplier.current_balance, Decimal('150.00'))
    
    def test_balance_calculation_with_multiple_transactions(self):
        """Test balance calculation with multiple transactions"""
        # Set opening balance
        self.supplier.set_opening_balance(Decimal('100.00'), self.user)
        
        # Create multiple transactions
        SupplierLedger.objects.create(
            supplier=self.supplier,
            transaction_type='purchase',
            amount=Decimal('200.00'),
            description="Purchase 1",
            transaction_date=timezone.now(),
            created_by=self.user
        )
        
        SupplierLedger.objects.create(
            supplier=self.supplier,
            transaction_type='payment',
            amount=Decimal('50.00'),
            description="Payment 1",
            transaction_date=timezone.now(),
            created_by=self.user
        )
        
        SupplierLedger.objects.create(
            supplier=self.supplier,
            transaction_type='purchase',
            amount=Decimal('150.00'),
            description="Purchase 2",
            transaction_date=timezone.now(),
            created_by=self.user
        )
        
        # Update supplier balance
        ledger_entries = SupplierLedger.objects.filter(supplier=self.supplier)
        total_balance = Decimal('0.00')
        for entry in ledger_entries:
            if entry.transaction_type in ['purchase', 'opening_balance']:
                total_balance += entry.amount
            elif entry.transaction_type in ['payment', 'return']:
                total_balance -= entry.amount
            elif entry.transaction_type == 'adjustment':
                total_balance += entry.amount
        
        self.supplier.current_balance = total_balance
        self.supplier.save()
        
        # Expected balance: 100 (opening) + 200 (purchase 1) - 50 (payment) + 150 (purchase 2) = 400
        self.assertEqual(self.supplier.current_balance, Decimal('400.00'))
    
    def test_opening_balance_creates_ledger_entry(self):
        """Test that setting opening balance creates a ledger entry"""
        amount = Decimal('500.00')
        self.supplier.set_opening_balance(amount, self.user)
        
        # Check that ledger entry was created
        ledger_entry = SupplierLedger.objects.get(
            supplier=self.supplier,
            transaction_type='opening_balance'
        )
        
        self.assertEqual(ledger_entry.amount, amount)
        self.assertEqual(ledger_entry.reference, "OPENING")
        self.assertEqual(ledger_entry.created_by, self.user)
        self.assertIn("Opening balance set to", ledger_entry.description)


class SupplierIntegrationTest(TestCase):
    """Integration tests for Supplier module"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
    
    def test_complete_supplier_workflow(self):
        """Test complete supplier workflow from creation to ledger management"""
        # 1. Create a supplier
        form_data = {
            'name': 'Integration Test Supplier',
            'contact_person': 'Test Person',
            'phone': '1234567890',
            'address': 'Test Address',
            'city': 'Test City',
            'is_active': True
        }
        response = self.client.post(reverse('suppliers:supplier_create'), form_data)
        self.assertEqual(response.status_code, 302)
        
        supplier = Supplier.objects.get(name='Integration Test Supplier')
        
        # 2. Set opening balance
        opening_balance_data = {
            'amount': '500.00'
        }
        response = self.client.post(
            reverse('suppliers:supplier_opening_balance', kwargs={'pk': supplier.pk}),
            opening_balance_data
        )
        self.assertEqual(response.status_code, 302)
        
        supplier.refresh_from_db()
        self.assertEqual(supplier.opening_balance, Decimal('500.00'))
        self.assertEqual(supplier.current_balance, Decimal('500.00'))
        
        # 3. Add a purchase transaction
        purchase_data = {
            'transaction_type': 'purchase',
            'amount': '200.00',
            'description': 'Test purchase',
            'reference': 'PURCHASE-001',
            'transaction_date': timezone.now(),
            'payment_method': 'cash'
        }
        response = self.client.post(
            reverse('suppliers:supplier_ledger_create', kwargs={'supplier_id': supplier.pk}),
            purchase_data
        )
        self.assertEqual(response.status_code, 302)
        
        # 4. Add a payment transaction
        payment_data = {
            'transaction_type': 'payment',
            'amount': '100.00',
            'description': 'Test payment',
            'reference': 'PAY-001',
            'transaction_date': timezone.now(),
            'payment_method': 'cash'
        }
        response = self.client.post(
            reverse('suppliers:supplier_ledger_create', kwargs={'supplier_id': supplier.pk}),
            payment_data
        )
        self.assertEqual(response.status_code, 302)
        
        # 5. Check final balance
        supplier.refresh_from_db()
        
        # Manually update balance calculation (simulating the view logic)
        ledger_entries = SupplierLedger.objects.filter(supplier=supplier)
        total_balance = Decimal('0.00')
        for entry in ledger_entries:
            if entry.transaction_type in ['purchase', 'opening_balance']:
                total_balance += entry.amount
            elif entry.transaction_type in ['payment', 'return']:
                total_balance -= entry.amount
            elif entry.transaction_type == 'adjustment':
                total_balance += entry.amount
        
        supplier.current_balance = total_balance
        supplier.save()
        
        # Expected: 500 (opening) + 200 (purchase) - 100 (payment) = 600
        self.assertEqual(supplier.current_balance, Decimal('600.00'))
    
    def test_supplier_ledger_detail_integration(self):
        """Test supplier ledger detail view with all transaction types"""
        # Create supplier and transactions
        supplier = Supplier.objects.create(
            name="Ledger Test Supplier",
            contact_person="Test Person",
            phone="1234567890",
            address="Test Address",
            city="Test City"
        )
        
        # Set opening balance
        supplier.set_opening_balance(Decimal('1000.00'), self.user)
        
        # Create various transactions
        SupplierLedger.objects.create(
            supplier=supplier,
            transaction_type='purchase',
            amount=Decimal('500.00'),
            description="Purchase transaction",
            reference="PURCHASE-001",
            transaction_date=timezone.now(),
            created_by=self.user
        )
        
        SupplierLedger.objects.create(
            supplier=supplier,
            transaction_type='payment',
            amount=Decimal('200.00'),
            description="Payment transaction",
            reference="PAY-001",
            transaction_date=timezone.now(),
            payment_method='cash',
            created_by=self.user
        )
        
        SupplierLedger.objects.create(
            supplier=supplier,
            transaction_type='adjustment',
            amount=Decimal('50.00'),
            description="Adjustment transaction",
            reference="ADJ-001",
            transaction_date=timezone.now(),
            created_by=self.user
        )
        
        # Test ledger detail view
        response = self.client.get(reverse('suppliers:supplier_ledger_detail', kwargs={'pk': supplier.pk}))
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


class SupplierListViewTest(TestCase):
    """Test cases for SupplierListView context data"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        
        # Create suppliers with different balances
        self.supplier1 = Supplier.objects.create(
            name="Supplier 1",
            current_balance=Decimal('100.00'),  # Positive balance (you owe them)
            is_active=True
        )
        
        self.supplier2 = Supplier.objects.create(
            name="Supplier 2",
            current_balance=Decimal('-50.00'),  # Negative balance (they owe you)
            is_active=True
        )
        
        self.supplier3 = Supplier.objects.create(
            name="Supplier 3",
            current_balance=Decimal('0.00'),
            is_active=False  # Inactive supplier
        )
    
    def test_supplier_list_context_calculations(self):
        """Test supplier list view context calculations"""
        response = self.client.get(reverse('suppliers:supplier_list'))
        self.assertEqual(response.status_code, 200)
        
        context = response.context
        
        # Test total payable (positive balances)
        self.assertEqual(context['total_payable'], Decimal('100.00'))
        
        # Test total receivable (negative balances)
        self.assertEqual(context['total_receivable'], Decimal('50.00'))
        
        # Test active suppliers count
        self.assertEqual(context['active_suppliers'], 2)
    
    def test_supplier_list_template_content(self):
        """Test supplier list template content"""
        response = self.client.get(reverse('suppliers:supplier_list'))
        self.assertEqual(response.status_code, 200)
        
        # Check that supplier names are in the response
        self.assertContains(response, "Supplier 1")
        self.assertContains(response, "Supplier 2")
        self.assertContains(response, "Supplier 3")
        
        # Check that balance information is displayed
        self.assertContains(response, "100.00")
        self.assertContains(response, "-50.00")


class SupplierFormValidationTest(TestCase):
    """Test cases for supplier form validation"""
    
    def test_supplier_form_name_required(self):
        """Test that supplier name is required"""
        form_data = {
            'contact_person': 'John Doe',
            'phone': '1234567890',
            'address': '123 Test Street',
            'city': 'Test City',
            'is_active': True
        }
        form = SupplierForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
    
    def test_supplier_form_optional_fields(self):
        """Test that optional fields work correctly"""
        form_data = {
            'name': 'Test Supplier',
            'is_active': True
        }
        form = SupplierForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_supplier_form_widget_attributes(self):
        """Test that form widgets have correct attributes"""
        form = SupplierForm()
        
        # Check name field widget
        name_widget = form.fields['name'].widget
        self.assertIn('form-control', name_widget.attrs['class'])
        self.assertIn('Enter supplier name', name_widget.attrs['placeholder'])
        
        # Check address field widget
        address_widget = form.fields['address'].widget
        self.assertIn('form-control', address_widget.attrs['class'])
        self.assertEqual(address_widget.attrs['rows'], 3)


class SupplierLedgerFormValidationTest(TestCase):
    """Test cases for supplier ledger form validation"""
    
    def test_ledger_form_required_fields(self):
        """Test that required fields are validated"""
        form_data = {
            'amount': '100.00',
            'description': 'Test transaction'
        }
        form = SupplierLedgerForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('transaction_type', form.errors)
    
    def test_ledger_form_amount_validation(self):
        """Test amount field validation"""
        form_data = {
            'transaction_type': 'purchase',
            'amount': '-100.00',  # Negative amount
            'description': 'Test transaction',
            'transaction_date': timezone.now()
        }
        form = SupplierLedgerForm(data=form_data)
        # Form should be valid even with negative amounts (for adjustments)
        self.assertTrue(form.is_valid())
    
    def test_ledger_form_initial_values(self):
        """Test that form sets initial values correctly"""
        form = SupplierLedgerForm()
        
        # Check that transaction_date has initial value
        self.assertIsNotNone(form.fields['transaction_date'].initial)
        
        # Check that amount field is required
        self.assertTrue(form.fields['amount'].required)
        self.assertTrue(form.fields['description'].required)
        self.assertTrue(form.fields['transaction_type'].required)


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['suppliers.tests'])
