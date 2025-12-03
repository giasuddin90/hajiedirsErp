"""
Test cases for the Sales module
Tests all sales functionality including regular sales, instant sales, and inventory management
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from sales.models import SalesOrder, SalesOrderItem
from customers.models import Customer
from stock.models import Product, ProductCategory, ProductBrand
from suppliers.models import Supplier


class SalesModelTests(TestCase):
    """Test cases for Sales models"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Create test customer
        self.customer = Customer.objects.create(
            name='Test Customer',
            phone='1234567890',
            address='Test Address',
            is_active=True
        )
        
        # Create test category and brand
        self.category = ProductCategory.objects.create(
            name='Test Category',
            is_active=True
        )
        
        self.brand = ProductBrand.objects.create(
            name='Test Brand',
            is_active=True
        )
        
        # Create test product
        self.product = Product.objects.create(
            name='Test Product',
            unit_type='pcs',
            selling_price=Decimal('100.00'),
            category=self.category,
            brand=self.brand,
            is_active=True
        )
        
        # Create stock for the product
        Stock.objects.create(
            product=self.product,
            quantity=Decimal('100.00'),
            unit_cost=Decimal('50.00')
        )
    
    def test_sales_order_creation(self):
        """Test creating a sales order"""
        order = SalesOrder.objects.create(
            order_number='SO-TEST001',
            sales_type='regular',
            customer=self.customer,
            order_date=date.today(),
            delivery_date=date.today() + timedelta(days=7),
            status='order',
            total_amount=Decimal('200.00'),
            created_by=self.user
        )
        
        self.assertEqual(order.order_number, 'SO-TEST001')
        self.assertEqual(order.sales_type, 'regular')
        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.status, 'order')
        self.assertEqual(order.total_amount, Decimal('200.00'))
    
    def test_instant_sales_order_creation(self):
        """Test creating an instant sales order"""
        order = SalesOrder.objects.create(
            order_number='IS-TEST001',
            sales_type='instant',
            customer_name='Anonymous Customer',
            order_date=date.today(),
            status='delivered',
            total_amount=Decimal('150.00'),
            created_by=self.user
        )
        
        self.assertEqual(order.order_number, 'IS-TEST001')
        self.assertEqual(order.sales_type, 'instant')
        self.assertIsNone(order.customer)
        self.assertEqual(order.customer_name, 'Anonymous Customer')
        self.assertEqual(order.status, 'delivered')
    
    def test_sales_order_item_creation(self):
        """Test creating sales order items"""
        order = SalesOrder.objects.create(
            order_number='SO-TEST002',
            sales_type='regular',
            customer=self.customer,
            order_date=date.today(),
            status='order',
            created_by=self.user
        )
        
        item = SalesOrderItem.objects.create(
            sales_order=order,
            product=self.product,
            quantity=Decimal('2.00'),
            unit_price=Decimal('100.00'),
            total_price=Decimal('200.00')
        )
        
        self.assertEqual(item.sales_order, order)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, Decimal('2.00'))
        self.assertEqual(item.unit_price, Decimal('100.00'))
        self.assertEqual(item.total_price, Decimal('200.00'))
    
    def test_mark_delivered_regular_sale(self):
        """Test marking a regular sale as delivered"""
        order = SalesOrder.objects.create(
            order_number='SO-TEST003',
            sales_type='regular',
            customer=self.customer,
            order_date=date.today(),
            status='order',
            created_by=self.user
        )
        
        # Add item to order
        SalesOrderItem.objects.create(
            sales_order=order,
            product=self.product,
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            total_price=Decimal('100.00')
        )
        
        # Mark as delivered
        order.mark_delivered(user=self.user)
        
        # Check status changed
        order.refresh_from_db()
        self.assertEqual(order.status, 'delivered')
        
        # Check stock was reduced
        stock = Stock.objects.get(product=self.product)
        self.assertEqual(stock.quantity, Decimal('99.00'))
    
    def test_mark_delivered_instant_sale(self):
        """Test marking an instant sale as delivered"""
        order = SalesOrder.objects.create(
            order_number='IS-TEST002',
            sales_type='instant',
            customer_name='Anonymous',
            order_date=date.today(),
            status='order',  # Start as order, not delivered
            created_by=self.user
        )
        
        # Add item to order
        SalesOrderItem.objects.create(
            sales_order=order,
            product=self.product,
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            total_price=Decimal('100.00')
        )
        
        # Mark as delivered (should update stock)
        order.mark_delivered(user=self.user)
        
        # Check status changed and stock was reduced
        order.refresh_from_db()
        self.assertEqual(order.status, 'delivered')
        
        stock = Stock.objects.get(product=self.product)
        self.assertEqual(stock.quantity, Decimal('99.00'))
    
    def test_cancel_order(self):
        """Test cancelling an order"""
        order = SalesOrder.objects.create(
            order_number='SO-TEST004',
            sales_type='regular',
            customer=self.customer,
            order_date=date.today(),
            status='order',
            created_by=self.user
        )
        
        # Add item to order
        SalesOrderItem.objects.create(
            sales_order=order,
            product=self.product,
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            total_price=Decimal('100.00')
        )
        
        # Cancel order
        order.cancel_order(user=self.user)
        
        # Check status changed
        order.refresh_from_db()
        self.assertEqual(order.status, 'cancel')
    
    def test_cancel_delivered_order(self):
        """Test cancelling a delivered order (should restore stock)"""
        order = SalesOrder.objects.create(
            order_number='SO-TEST005',
            sales_type='regular',
            customer=self.customer,
            order_date=date.today(),
            status='delivered',
            created_by=self.user
        )
        
        # Add item to order
        SalesOrderItem.objects.create(
            sales_order=order,
            product=self.product,
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            total_price=Decimal('100.00')
        )
        
        # Cancel delivered order
        order.cancel_order(user=self.user)
        
        # Check status changed
        order.refresh_from_db()
        self.assertEqual(order.status, 'cancel')
        
        # Check stock was restored
        stock = Stock.objects.get(product=self.product)
        self.assertEqual(stock.quantity, Decimal('101.00'))
    
    def test_sales_order_str_representation(self):
        """Test string representation of sales order"""
        # Regular sale
        order1 = SalesOrder.objects.create(
            order_number='SO-TEST006',
            sales_type='regular',
            customer=self.customer,
            order_date=date.today(),
            created_by=self.user
        )
        self.assertIn('SO-TEST006', str(order1))
        self.assertIn('Test Customer', str(order1))
        
        # Instant sale
        order2 = SalesOrder.objects.create(
            order_number='IS-TEST003',
            sales_type='instant',
            customer_name='Anonymous',
            order_date=date.today(),
            created_by=self.user
        )
        self.assertIn('IS-TEST003', str(order2))
        self.assertIn('Anonymous', str(order2))
    
    def test_sales_order_item_str_representation(self):
        """Test string representation of sales order item"""
        order = SalesOrder.objects.create(
            order_number='SO-TEST007',
            sales_type='regular',
            customer=self.customer,
            order_date=date.today(),
            created_by=self.user
        )
        
        item = SalesOrderItem.objects.create(
            sales_order=order,
            product=self.product,
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            total_price=Decimal('100.00')
        )
        
        self.assertIn('SO-TEST007', str(item))
        self.assertIn('Test Product', str(item))


class SalesViewTests(TestCase):
    """Test cases for Sales views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Create test data
        self.customer = Customer.objects.create(
            name='Test Customer',
            phone='1234567890',
            address='Test Address',
            is_active=True
        )
        
        self.category = ProductCategory.objects.create(
            name='Test Category',
            is_active=True
        )
        
        self.brand = ProductBrand.objects.create(
            name='Test Brand',
            is_active=True
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            unit_type='pcs',
            selling_price=Decimal('100.00'),
            category=self.category,
            brand=self.brand,
            is_active=True
        )
        
        Stock.objects.create(
            product=self.product,
            quantity=Decimal('100.00'),
            unit_cost=Decimal('50.00')
        )
    
    def test_sales_order_list_view(self):
        """Test sales order list view"""
        # Create test order
        order = SalesOrder.objects.create(
            order_number='SO-TEST001',
            sales_type='regular',
            customer=self.customer,
            order_date=date.today(),
            status='order',
            created_by=self.user
        )
        
        response = self.client.get(reverse('sales:order_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SO-TEST001')
        self.assertContains(response, 'Test Customer')
    
    def test_sales_order_create_view(self):
        """Test sales order create view"""
        response = self.client.get(reverse('sales:order_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'New Order')
    
    def test_instant_sales_create_view(self):
        """Test instant sales create view"""
        response = self.client.get(reverse('sales:instant_sales'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Instant Sale')
    
    def test_sales_order_detail_view(self):
        """Test sales order detail view"""
        order = SalesOrder.objects.create(
            order_number='SO-TEST002',
            sales_type='regular',
            customer=self.customer,
            order_date=date.today(),
            status='order',
            created_by=self.user
        )
        
        response = self.client.get(reverse('sales:order_detail', kwargs={'pk': order.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SO-TEST002')
        self.assertContains(response, 'Test Customer')
    
    def test_mark_order_delivered(self):
        """Test marking an order as delivered"""
        order = SalesOrder.objects.create(
            order_number='SO-TEST003',
            sales_type='regular',
            customer=self.customer,
            order_date=date.today(),
            status='order',
            created_by=self.user
        )
        
        # Add item to order
        SalesOrderItem.objects.create(
            sales_order=order,
            product=self.product,
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            total_price=Decimal('100.00')
        )
        
        response = self.client.get(reverse('sales:mark_order_delivered', kwargs={'order_id': order.pk}))
        self.assertEqual(response.status_code, 302)  # Redirect after action
        
        # Check order status changed
        order.refresh_from_db()
        self.assertEqual(order.status, 'delivered')
    
    def test_cancel_sales_order(self):
        """Test cancelling a sales order"""
        order = SalesOrder.objects.create(
            order_number='SO-TEST004',
            sales_type='regular',
            customer=self.customer,
            order_date=date.today(),
            status='order',
            created_by=self.user
        )
        
        response = self.client.get(reverse('sales:cancel_sales_order', kwargs={'order_id': order.pk}))
        self.assertEqual(response.status_code, 302)  # Redirect after action
        
        # Check order status changed
        order.refresh_from_db()
        self.assertEqual(order.status, 'cancel')
    
    def test_sales_order_invoice(self):
        """Test sales order invoice generation"""
        order = SalesOrder.objects.create(
            order_number='SO-TEST005',
            sales_type='regular',
            customer=self.customer,
            order_date=date.today(),
            status='order',
            created_by=self.user
        )
        
        response = self.client.get(reverse('sales:order_invoice', kwargs={'order_id': order.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'INVOICE')
        self.assertContains(response, 'SO-TEST005')
        self.assertContains(response, 'Test Customer')
    
    def test_instant_sales_invoice(self):
        """Test instant sales invoice generation"""
        order = SalesOrder.objects.create(
            order_number='IS-TEST001',
            sales_type='instant',
            customer_name='Anonymous Customer',
            order_date=date.today(),
            status='delivered',
            created_by=self.user
        )
        
        response = self.client.get(reverse('sales:order_invoice', kwargs={'order_id': order.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'INVOICE')
        self.assertContains(response, 'IS-TEST001')
        self.assertContains(response, 'Anonymous Customer')
        self.assertContains(response, 'Instant Sale')


class SalesFormTests(TestCase):
    """Test cases for Sales forms"""
    
    def setUp(self):
        """Set up test data"""
        self.customer = Customer.objects.create(
            name='Test Customer',
            phone='1234567890',
            address='Test Address',
            is_active=True
        )
    
    def test_sales_order_form_valid_data(self):
        """Test sales order form with valid data"""
        from sales.forms import SalesOrderForm
        
        form_data = {
            'sales_type': 'regular',
            'customer': self.customer.id,
            'order_date': date.today(),
            'delivery_date': date.today() + timedelta(days=7),
            'status': 'order',
            'notes': 'Test order'
        }
        
        form = SalesOrderForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_sales_order_form_instant_sale(self):
        """Test sales order form for instant sale"""
        from sales.forms import SalesOrderForm
        
        form_data = {
            'sales_type': 'instant',
            'customer_name': 'Anonymous Customer',
            'order_date': date.today(),
            'status': 'delivered',
            'notes': 'Test instant sale'
        }
        
        form = SalesOrderForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_sales_order_form_validation_errors(self):
        """Test sales order form validation errors"""
        from sales.forms import SalesOrderForm
        
        # Test regular sale without customer
        form_data = {
            'sales_type': 'regular',
            'order_date': date.today(),
            'status': 'order'
        }
        
        form = SalesOrderForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
    
    def test_instant_sales_form_valid_data(self):
        """Test instant sales form with valid data"""
        from sales.forms import InstantSalesForm
        
        form_data = {
            'customer_name': 'Anonymous Customer',
            'order_date': date.today(),
            'notes': 'Test instant sale',
            'sales_type': 'instant'  # Add the required field
        }
        
        form = InstantSalesForm(data=form_data)
        # The form should be valid
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        self.assertTrue(form.is_valid())
    
    def test_instant_sales_form_save(self):
        """Test instant sales form save method"""
        from sales.forms import InstantSalesForm
        
        form_data = {
            'customer_name': 'Anonymous Customer',
            'order_date': date.today(),
            'notes': 'Test instant sale',
            'sales_type': 'instant'  # Add the required field
        }
        
        form = InstantSalesForm(data=form_data)
        # The form should be valid
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        self.assertTrue(form.is_valid())
        
        instance = form.save()
        self.assertEqual(instance.sales_type, 'instant')
        self.assertEqual(instance.status, 'delivered')
        self.assertEqual(instance.customer_name, 'Anonymous Customer')


class SalesIntegrationTests(TestCase):
    """Integration tests for Sales module"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Create test data
        self.customer = Customer.objects.create(
            name='Test Customer',
            phone='1234567890',
            address='Test Address',
            is_active=True
        )
        
        self.category = ProductCategory.objects.create(
            name='Test Category',
            is_active=True
        )
        
        self.brand = ProductBrand.objects.create(
            name='Test Brand',
            is_active=True
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            unit_type='pcs',
            selling_price=Decimal('100.00'),
            category=self.category,
            brand=self.brand,
            is_active=True
        )
        
        Stock.objects.create(
            product=self.product,
            quantity=Decimal('100.00'),
            unit_cost=Decimal('50.00')
        )
    
    def test_complete_sales_workflow(self):
        """Test complete sales workflow from creation to delivery"""
        # Create sales order directly (simpler than form submission)
        order = SalesOrder.objects.create(
            order_number='SO-TEST001',
            sales_type='regular',
            customer=self.customer,
            order_date=date.today(),
            delivery_date=date.today() + timedelta(days=7),
            status='order',
            created_by=self.user
        )
        
        # Add item to order
        SalesOrderItem.objects.create(
            sales_order=order,
            product=self.product,
            quantity=Decimal('2.00'),
            unit_price=Decimal('100.00'),
            total_price=Decimal('200.00')
        )
        
        # Mark as delivered
        response = self.client.get(reverse('sales:mark_order_delivered', kwargs={'order_id': order.pk}))
        self.assertEqual(response.status_code, 302)
        
        # Check order status and stock
        order.refresh_from_db()
        self.assertEqual(order.status, 'delivered')
        
        stock = Stock.objects.get(product=self.product)
        self.assertEqual(stock.quantity, Decimal('98.00'))  # 100 - 2
    
    def test_instant_sales_workflow(self):
        """Test complete instant sales workflow"""
        # Create instant sale directly (simpler than form submission)
        order = SalesOrder.objects.create(
            order_number='IS-TEST001',
            sales_type='instant',
            customer_name='Anonymous Customer',
            order_date=date.today(),
            status='delivered',
            created_by=self.user
        )
        
        # Add item to order
        SalesOrderItem.objects.create(
            sales_order=order,
            product=self.product,
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            total_price=Decimal('100.00')
        )
        
        # Check instant sale properties
        self.assertEqual(order.sales_type, 'instant')
        self.assertEqual(order.status, 'delivered')
        self.assertEqual(order.customer_name, 'Anonymous Customer')
        
        # For instant sales, stock should be reduced when the order is created
        # (This would happen in the actual view when creating instant sales)
        # Stock model removed - inventory calculated in real-time
        # Inventory decreases automatically when order status = 'delivered'
        # No need to manually update stock
        
        # Check stock using real-time calculation
        current_stock = self.product.get_realtime_quantity()
        self.assertEqual(stock.quantity, Decimal('99.00'))  # 100 - 1
    
    def test_cancel_delivered_order_workflow(self):
        """Test cancelling a delivered order and stock restoration"""
        # Create and deliver order
        order = SalesOrder.objects.create(
            order_number='SO-TEST001',
            sales_type='regular',
            customer=self.customer,
            order_date=date.today(),
            status='delivered',
            created_by=self.user
        )
        
        SalesOrderItem.objects.create(
            sales_order=order,
            product=self.product,
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            total_price=Decimal('100.00')
        )
        
        # Cancel delivered order
        response = self.client.get(reverse('sales:cancel_sales_order', kwargs={'order_id': order.pk}))
        self.assertEqual(response.status_code, 302)
        
        # Check order status and stock restoration
        order.refresh_from_db()
        self.assertEqual(order.status, 'cancel')
        
        stock = Stock.objects.get(product=self.product)
        self.assertEqual(stock.quantity, Decimal('101.00'))  # 100 + 1 (restored)


class SalesURLTests(TestCase):
    """Test cases for Sales URLs"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_sales_urls(self):
        """Test all sales URLs are accessible"""
        urls = [
            'sales:order_list',
            'sales:order_create',
            'sales:instant_sales',
        ]
        
        for url_name in urls:
            with self.subTest(url=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)
    
    def test_sales_order_detail_url(self):
        """Test sales order detail URL"""
        # Create test order
        customer = Customer.objects.create(
            name='Test Customer',
            phone='1234567890',
            address='Test Address',
            is_active=True
        )
        
        order = SalesOrder.objects.create(
            order_number='SO-TEST001',
            sales_type='regular',
            customer=customer,
            order_date=date.today(),
            status='order',
            created_by=self.user
        )
        
        response = self.client.get(reverse('sales:order_detail', kwargs={'pk': order.pk}))
        self.assertEqual(response.status_code, 200)
    
    def test_sales_order_actions_urls(self):
        """Test sales order action URLs"""
        # Create test order
        customer = Customer.objects.create(
            name='Test Customer',
            phone='1234567890',
            address='Test Address',
            is_active=True
        )
        
        order = SalesOrder.objects.create(
            order_number='SO-TEST001',
            sales_type='regular',
            customer=customer,
            order_date=date.today(),
            status='order',
            created_by=self.user
        )
        
        action_urls = [
            ('sales:mark_order_delivered', {'order_id': order.pk}),
            ('sales:cancel_sales_order', {'order_id': order.pk}),
            ('sales:order_invoice', {'order_id': order.pk}),
        ]
        
        for url_name, kwargs in action_urls:
            with self.subTest(url=url_name):
                response = self.client.get(reverse(url_name, kwargs=kwargs))
                self.assertIn(response.status_code, [200, 302])  # 200 for invoice, 302 for redirects
