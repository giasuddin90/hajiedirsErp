from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from .models import PurchaseOrder, PurchaseOrderItem
from suppliers.models import Supplier
from stock.models import Product, Warehouse


class PurchaseOrderModelTest(TestCase):
    """Test cases for PurchaseOrder model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            contact_person='John Doe',
            phone='1234567890',
            email='supplier@test.com',
            address='Test Address',
            city='Test City'
        )
        self.warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            location='Test Location'
        )
        self.product = Product.objects.create(
            name='Test Product',
            unit_type='pcs',
            unit_name='Pieces',
            cost_price=Decimal('100.00'),
            selling_price=Decimal('150.00'),
            min_stock_level=Decimal('10.00')
        )
    
    def test_purchase_order_creation(self):
        """Test creating a purchase order"""
        order = PurchaseOrder.objects.create(
            order_number='PO-TEST-001',
            supplier=self.supplier,
            order_date=date.today(),
            expected_date=date.today() + timedelta(days=7),
            status='draft',
            total_amount=Decimal('1000.00'),
            notes='Test order',
            created_by=self.user
        )
        
        self.assertEqual(str(order), f"PO-{order.order_number} - {self.supplier.name}")
        self.assertEqual(order.supplier, self.supplier)
        self.assertEqual(order.status, 'draft')
        self.assertEqual(order.total_amount, Decimal('1000.00'))
    
    def test_purchase_order_with_items(self):
        """Test creating a purchase order with items"""
        order = PurchaseOrder.objects.create(
            order_number='PO-TEST-002',
            supplier=self.supplier,
            order_date=date.today(),
            expected_date=date.today() + timedelta(days=7),
            status='draft',
            total_amount=Decimal('0.00'),
            created_by=self.user
        )
        
        # Add items
        item1 = PurchaseOrderItem.objects.create(
            purchase_order=order,
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal('10.00'),
            unit_price=Decimal('100.00'),
            total_price=Decimal('1000.00')
        )
        
        item2 = PurchaseOrderItem.objects.create(
            purchase_order=order,
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal('5.00'),
            unit_price=Decimal('200.00'),
            total_price=Decimal('1000.00')
        )
        
        # Update total
        total = sum(item.total_price for item in order.items.all())
        order.total_amount = total
        order.save()
        
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.total_amount, Decimal('2000.00'))
        self.assertEqual(str(item1), f"{order.order_number} - {self.product.name}")
    
    def test_purchase_order_receive_goods(self):
        """Test receiving goods and updating inventory"""
        order = PurchaseOrder.objects.create(
            order_number='PO-TEST-003',
            supplier=self.supplier,
            order_date=date.today(),
            expected_date=date.today() + timedelta(days=7),
            status='sent',
            total_amount=Decimal('1000.00'),
            created_by=self.user
        )
        
        # Add item
        PurchaseOrderItem.objects.create(
            purchase_order=order,
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal('10.00'),
            unit_price=Decimal('100.00'),
            total_price=Decimal('1000.00')
        )
        
        # Receive goods
        order.receive_goods(user=self.user)
        
        self.assertEqual(order.status, 'received')
        
        # Check if stock was updated
        from stock.models import Stock
        stock = Stock.objects.get(product=self.product, warehouse=self.warehouse)
        self.assertEqual(stock.quantity, Decimal('10.00'))
        self.assertEqual(stock.unit_cost, Decimal('100.00'))


class PurchaseOrderViewTest(TestCase):
    """Test cases for PurchaseOrder views"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            contact_person='John Doe',
            phone='1234567890',
            email='supplier@test.com',
            address='Test Address',
            city='Test City'
        )
        self.warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            location='Test Location'
        )
        self.product = Product.objects.create(
            name='Test Product',
            unit_type='pcs',
            unit_name='Pieces',
            cost_price=Decimal('100.00'),
            selling_price=Decimal('150.00'),
            min_stock_level=Decimal('10.00')
        )
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_purchase_order_list_view(self):
        """Test purchase order list view"""
        # Create test orders
        PurchaseOrder.objects.create(
            order_number='PO-TEST-001',
            supplier=self.supplier,
            order_date=date.today(),
            expected_date=date.today() + timedelta(days=7),
            status='draft',
            total_amount=Decimal('1000.00'),
            created_by=self.user
        )
        
        response = self.client.get(reverse('purchases:order_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PO-TEST-001')
        self.assertContains(response, 'Test Supplier')
    
    def test_purchase_order_create_view_get(self):
        """Test purchase order create view GET request"""
        response = self.client.get(reverse('purchases:order_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'New Purchase Order')
        self.assertContains(response, 'Test Supplier')
        self.assertContains(response, 'Test Product')
        self.assertContains(response, 'Test Warehouse')
    
    def test_purchase_order_create_view_post_success(self):
        """Test successful purchase order creation"""
        data = {
            'supplier': self.supplier.id,
            'order_date': date.today().strftime('%Y-%m-%d'),
            'expected_date': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'status': 'draft',
            'notes': 'Test order',
            'total_amount': '0'
        }
        
        response = self.client.post(reverse('purchases:order_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Check if order was created
        order = PurchaseOrder.objects.get(supplier=self.supplier)
        self.assertEqual(order.notes, 'Test order')
        self.assertEqual(order.created_by, self.user)
        self.assertTrue(order.order_number.startswith('PO-'))
    
    def test_purchase_order_create_with_products(self):
        """Test purchase order creation with products"""
        data = {
            'supplier': self.supplier.id,
            'order_date': date.today().strftime('%Y-%m-%d'),
            'expected_date': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'status': 'draft',
            'notes': 'Test order with products',
            'total_amount': '0',
            'products[]': [str(self.product.id)],
            'warehouses[]': [str(self.warehouse.id)],
            'quantities[]': ['10'],
            'prices[]': ['100.00']
        }
        
        response = self.client.post(reverse('purchases:order_create'), data)
        self.assertEqual(response.status_code, 302)
        
        # Check if order and items were created
        order = PurchaseOrder.objects.get(supplier=self.supplier)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.total_amount, Decimal('1000.00'))
        
        item = order.items.first()
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.warehouse, self.warehouse)
        self.assertEqual(item.quantity, Decimal('10.00'))
        self.assertEqual(item.unit_price, Decimal('100.00'))
    
    def test_purchase_order_create_with_multiple_products(self):
        """Test purchase order creation with multiple products"""
        # Create another product
        product2 = Product.objects.create(
            name='Test Product 2',
            unit_type='kg',
            unit_name='Kilogram',
            cost_price=Decimal('50.00'),
            selling_price=Decimal('75.00'),
            min_stock_level=Decimal('5.00')
        )
        
        data = {
            'supplier': self.supplier.id,
            'order_date': date.today().strftime('%Y-%m-%d'),
            'expected_date': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'status': 'draft',
            'notes': 'Test order with multiple products',
            'total_amount': '0',
            'products[]': [str(self.product.id), str(product2.id)],
            'warehouses[]': [str(self.warehouse.id), str(self.warehouse.id)],
            'quantities[]': ['10', '5'],
            'prices[]': ['100.00', '50.00']
        }
        
        response = self.client.post(reverse('purchases:order_create'), data)
        self.assertEqual(response.status_code, 302)
        
        # Check if order and items were created
        order = PurchaseOrder.objects.get(supplier=self.supplier)
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.total_amount, Decimal('1250.00'))  # 1000 + 250
    
    def test_purchase_order_create_invalid_data(self):
        """Test purchase order creation with invalid data"""
        data = {
            'supplier': self.supplier.id,
            'order_date': 'invalid-date',
            'expected_date': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'status': 'draft',
            'notes': 'Test order with invalid date',
            'total_amount': '0'
        }
        
        response = self.client.post(reverse('purchases:order_create'), data)
        self.assertEqual(response.status_code, 200)  # Form should be re-displayed with errors
    
    def test_purchase_order_detail_view(self):
        """Test purchase order detail view"""
        order = PurchaseOrder.objects.create(
            order_number='PO-TEST-001',
            supplier=self.supplier,
            order_date=date.today(),
            expected_date=date.today() + timedelta(days=7),
            status='draft',
            total_amount=Decimal('1000.00'),
            created_by=self.user
        )
        
        response = self.client.get(reverse('purchases:order_detail', kwargs={'pk': order.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PO-TEST-001')
        self.assertContains(response, 'Test Supplier')
    
    def test_purchase_order_update_view(self):
        """Test purchase order update view"""
        order = PurchaseOrder.objects.create(
            order_number='PO-TEST-001',
            supplier=self.supplier,
            order_date=date.today(),
            expected_date=date.today() + timedelta(days=7),
            status='draft',
            total_amount=Decimal('1000.00'),
            created_by=self.user
        )
        
        # Test GET request
        response = self.client.get(reverse('purchases:order_edit', kwargs={'pk': order.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Test POST request
        data = {
            'supplier': self.supplier.id,
            'order_date': date.today().strftime('%Y-%m-%d'),
            'expected_date': (date.today() + timedelta(days=10)).strftime('%Y-%m-%d'),
            'status': 'confirmed',
            'notes': 'Updated test order',
            'total_amount': '1000.00'
        }
        
        response = self.client.post(reverse('purchases:order_edit', kwargs={'pk': order.pk}), data)
        self.assertEqual(response.status_code, 302)
        
        # Check if order was updated
        order.refresh_from_db()
        self.assertEqual(order.status, 'confirmed')
        self.assertEqual(order.notes, 'Updated test order')
    
    def test_purchase_order_delete_view(self):
        """Test purchase order delete view"""
        order = PurchaseOrder.objects.create(
            order_number='PO-TEST-001',
            supplier=self.supplier,
            order_date=date.today(),
            expected_date=date.today() + timedelta(days=7),
            status='draft',
            total_amount=Decimal('1000.00'),
            created_by=self.user
        )
        
        # Test GET request (confirmation page)
        response = self.client.get(reverse('purchases:order_delete', kwargs={'pk': order.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Test POST request (actual deletion)
        response = self.client.post(reverse('purchases:order_delete', kwargs={'pk': order.pk}))
        self.assertEqual(response.status_code, 302)
        
        # Check if order was deleted
        self.assertFalse(PurchaseOrder.objects.filter(pk=order.pk).exists())


class PurchaseOrderIntegrationTest(TestCase):
    """Integration test cases for purchase order workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            contact_person='John Doe',
            phone='1234567890',
            email='supplier@test.com',
            address='Test Address',
            city='Test City'
        )
        self.warehouse = Warehouse.objects.create(
            name='Test Warehouse',
            location='Test Location'
        )
        self.product = Product.objects.create(
            name='Test Product',
            unit_type='pcs',
            unit_name='Pieces',
            cost_price=Decimal('100.00'),
            selling_price=Decimal('150.00'),
            min_stock_level=Decimal('10.00')
        )
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_complete_purchase_order_workflow(self):
        """Test complete purchase order workflow from creation to receiving"""
        # Step 1: Create purchase order
        data = {
            'supplier': self.supplier.id,
            'order_date': date.today().strftime('%Y-%m-%d'),
            'expected_date': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'status': 'draft',
            'notes': 'Complete workflow test',
            'total_amount': '0',
            'products[]': [str(self.product.id)],
            'warehouses[]': [str(self.warehouse.id)],
            'quantities[]': ['20'],
            'prices[]': ['100.00']
        }
        
        response = self.client.post(reverse('purchases:order_create'), data)
        self.assertEqual(response.status_code, 302)
        
        # Step 2: Verify order was created
        order = PurchaseOrder.objects.get(supplier=self.supplier)
        self.assertEqual(order.status, 'draft')
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.total_amount, Decimal('2000.00'))
        
        # Step 3: Update order status to 'sent'
        order.status = 'sent'
        order.save()
        
        # Step 4: Receive goods
        order.receive_goods(user=self.user)
        
        # Step 5: Verify order status and stock update
        order.refresh_from_db()
        self.assertEqual(order.status, 'received')
        
        # Check stock was updated
        from stock.models import Stock
        stock = Stock.objects.get(product=self.product, warehouse=self.warehouse)
        self.assertEqual(stock.quantity, Decimal('20.00'))
        self.assertEqual(stock.unit_cost, Decimal('100.00'))
    
    def test_purchase_order_with_invalid_products(self):
        """Test purchase order creation with invalid product data"""
        data = {
            'supplier': self.supplier.id,
            'order_date': date.today().strftime('%Y-%m-%d'),
            'expected_date': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'status': 'draft',
            'notes': 'Test with invalid products',
            'total_amount': '0',
            'products[]': ['999'],  # Non-existent product ID
            'warehouses[]': [str(self.warehouse.id)],
            'quantities[]': ['10'],
            'prices[]': ['100.00']
        }
        
        response = self.client.post(reverse('purchases:order_create'), data)
        self.assertEqual(response.status_code, 302)  # Should still redirect
        
        # Check if order was created but without items
        order = PurchaseOrder.objects.get(supplier=self.supplier)
        self.assertEqual(order.items.count(), 0)
        self.assertEqual(order.total_amount, Decimal('0.00'))
    
    def test_purchase_order_authentication_required(self):
        """Test that purchase order views require authentication"""
        self.client.logout()
        
        # Test list view
        response = self.client.get(reverse('purchases:order_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test create view
        response = self.client.get(reverse('purchases:order_create'))
        self.assertEqual(response.status_code, 302)  # Redirect to login


class PurchaseOrderAPITest(TestCase):
    """Test cases for purchase order API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            contact_person='John Doe',
            phone='1234567890',
            email='supplier@test.com',
            address='Test Address',
            city='Test City'
        )
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_purchase_order_list_api(self):
        """Test purchase order list API"""
        # Create test orders
        for i in range(3):
            PurchaseOrder.objects.create(
                order_number=f'PO-TEST-{i:03d}',
                supplier=self.supplier,
                order_date=date.today(),
                expected_date=date.today() + timedelta(days=7),
                status='draft',
                total_amount=Decimal('1000.00'),
                created_by=self.user
            )
        
        response = self.client.get(reverse('purchases:order_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PO-TEST-000')
        self.assertContains(response, 'PO-TEST-001')
        self.assertContains(response, 'PO-TEST-002')
    
    def test_purchase_order_search_filter(self):
        """Test purchase order search and filtering"""
        # Create orders with different statuses
        PurchaseOrder.objects.create(
            order_number='PO-DRAFT-001',
            supplier=self.supplier,
            order_date=date.today(),
            expected_date=date.today() + timedelta(days=7),
            status='draft',
            total_amount=Decimal('1000.00'),
            created_by=self.user
        )
        
        PurchaseOrder.objects.create(
            order_number='PO-CONFIRMED-001',
            supplier=self.supplier,
            order_date=date.today(),
            expected_date=date.today() + timedelta(days=7),
            status='confirmed',
            total_amount=Decimal('2000.00'),
            created_by=self.user
        )
        
        # Test filtering by status (if implemented)
        response = self.client.get(reverse('purchases:order_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PO-DRAFT-001')
        self.assertContains(response, 'PO-CONFIRMED-001')
