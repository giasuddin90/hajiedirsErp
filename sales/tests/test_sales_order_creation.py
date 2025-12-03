"""
Test cases for Sales Order Creation
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import date, timedelta
from customers.models import Customer
from stock.models import Product, ProductCategory, ProductBrand, UnitType
from sales.models import SalesOrder, SalesOrderItem


class SalesOrderCreationTest(TestCase):
    """Test sales order creation functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Create customer
        self.customer = Customer.objects.create(
            name='Test Customer',
            contact_person='John Doe',
            email='customer@example.com',
            phone='1234567890',
            address='123 Test St',
            is_active=True
        )
        
        # Create unit type
        self.unit_type = UnitType.objects.create(
            code='pcs',
            name='Pieces',
            is_active=True
        )
        
        # Create category
        self.category = ProductCategory.objects.create(
            name='Test Category',
            is_active=True
        )
        
        # Create brand
        self.brand = ProductBrand.objects.create(
            name='Test Brand',
            is_active=True
        )
        
        # Create product
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            brand=self.brand,
            unit_type=self.unit_type,
            cost_price=Decimal('100.00'),
            selling_price=Decimal('150.00'),
            delivery_charge_per_unit=Decimal('1.00'),
            is_active=True
        )
        
        # Create client
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_sales_order_create_page_loads(self):
        """Test that sales order create page loads successfully"""
        url = reverse('sales:order_create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'New Sales Order')
        self.assertContains(response, 'Customer')
        self.assertContains(response, 'Products')
    
    def test_sales_order_creation_with_products(self):
        """Test creating a sales order with products"""
        url = reverse('sales:order_create')
        order_date = date.today()
        delivery_date = order_date + timedelta(days=7)
        
        form_data = {
            'customer': self.customer.id,
            'order_date': order_date.strftime('%Y-%m-%d'),
            'delivery_date': delivery_date.strftime('%Y-%m-%d'),
            'status': 'order',
            'transportation_cost': '50.00',
            'notes': 'Test order',
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-product': self.product.id,
            'form-0-quantity': '10',
            'form-0-unit_price': '150.00',
            'form-0-total_price': '1500.00',
        }
        
        response = self.client.post(url, data=form_data, follow=True)
        
        # Check if order was created
        self.assertEqual(SalesOrder.objects.count(), 1)
        order = SalesOrder.objects.first()
        
        # Check order details
        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.order_date, order_date)
        self.assertEqual(order.status, 'order')
        self.assertEqual(order.transportation_cost, Decimal('50.00'))
        
        # Check order items
        self.assertEqual(order.items.count(), 1)
        item = order.items.first()
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, Decimal('10'))
        self.assertEqual(item.unit_price, Decimal('150.00'))
        self.assertEqual(item.total_price, Decimal('1500.00'))
        
        # Check total amount calculation
        # Subtotal: 1500.00
        # Delivery charges: 10 * 1.00 = 10.00
        # Transportation: 50.00
        # Total: 1500.00 + 10.00 + 50.00 = 1560.00
        expected_total = Decimal('1560.00')
        self.assertEqual(order.total_amount, expected_total)
        
        # Check redirect
        self.assertRedirects(response, reverse('sales:order_list'))
    
    def test_sales_order_creation_without_products(self):
        """Test creating a sales order without products (should still work)"""
        url = reverse('sales:order_create')
        order_date = date.today()
        
        form_data = {
            'customer': self.customer.id,
            'order_date': order_date.strftime('%Y-%m-%d'),
            'status': 'order',
            'transportation_cost': '0.00',
            'notes': 'Empty order',
            'form-TOTAL_FORMS': '0',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
        }
        
        response = self.client.post(url, data=form_data, follow=True)
        
        # Check if order was created
        self.assertEqual(SalesOrder.objects.count(), 1)
        order = SalesOrder.objects.first()
        
        # Check order details
        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.items.count(), 0)
        self.assertEqual(order.total_amount, Decimal('0.00'))
    
    def test_sales_order_creation_with_delivery_charges(self):
        """Test that delivery charges are calculated correctly"""
        url = reverse('sales:order_create')
        order_date = date.today()
        
        form_data = {
            'customer': self.customer.id,
            'order_date': order_date.strftime('%Y-%m-%d'),
            'status': 'order',
            'transportation_cost': '25.00',
            'notes': 'Test delivery charges',
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-product': self.product.id,
            'form-0-quantity': '5',
            'form-0-unit_price': '150.00',
            'form-0-total_price': '750.00',
            'form-1-product': self.product.id,
            'form-1-quantity': '3',
            'form-1-unit_price': '150.00',
            'form-1-total_price': '450.00',
        }
        
        response = self.client.post(url, data=form_data, follow=True)
        
        order = SalesOrder.objects.first()
        
        # Check total calculation
        # Subtotal: 750.00 + 450.00 = 1200.00
        # Delivery charges: (5 + 3) * 1.00 = 8.00
        # Transportation: 25.00
        # Total: 1200.00 + 8.00 + 25.00 = 1233.00
        expected_total = Decimal('1233.00')
        self.assertEqual(order.total_amount, expected_total)
    
    def test_sales_order_creation_validation_errors(self):
        """Test that validation errors are shown properly"""
        url = reverse('sales:order_create')
        
        # Submit form without required fields
        form_data = {
            'customer': '',
            'order_date': '',
            'form-TOTAL_FORMS': '0',
            'form-INITIAL_FORMS': '0',
        }
        
        response = self.client.post(url, data=form_data)
        
        # Should return form with errors (not redirect)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'error', count=None, status_code=200)
    
    def test_sales_order_creation_with_invalid_product_data(self):
        """Test creating order with invalid product data"""
        url = reverse('sales:order_create')
        order_date = date.today()
        
        form_data = {
            'customer': self.customer.id,
            'order_date': order_date.strftime('%Y-%m-%d'),
            'status': 'order',
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-product': self.product.id,
            'form-0-quantity': '0',  # Invalid: quantity must be > 0
            'form-0-unit_price': '150.00',
        }
        
        response = self.client.post(url, data=form_data)
        
        # Should return form with errors
        self.assertEqual(response.status_code, 200)
        # Order should not be created
        self.assertEqual(SalesOrder.objects.count(), 0)

