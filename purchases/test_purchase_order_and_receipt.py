"""
Test cases for Purchase Order creation and Goods Receipt functionality
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.db import transaction
from decimal import Decimal
from datetime import date, timedelta

from .models import PurchaseOrder, PurchaseOrderItem, GoodsReceipt, GoodsReceiptItem
from suppliers.models import Supplier
from stock.models import Product, ProductCategory, ProductBrand, UnitType, Warehouse


class PurchaseOrderCreationTest(TestCase):
    """Test cases for creating purchase orders"""
    
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
            address='Test Address',
            city='Test City',
            is_active=True
        )
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            is_active=True
        )
        
        # Create unit type
        self.unit_type = UnitType.objects.create(
            code='pcs',
            name='Pieces',
            is_active=True
        )
        
        # Create category and brand
        self.category = ProductCategory.objects.create(
            name='Test Category',
            is_active=True
        )
        self.brand = ProductBrand.objects.create(
            name='Test Brand',
            is_active=True
        )
        
        # Create products
        self.product1 = Product.objects.create(
            name='Test Product 1',
            category=self.category,
            brand=self.brand,
            unit_type=self.unit_type,
            cost_price=Decimal('100.00'),
            selling_price=Decimal('150.00'),
            min_stock_level=Decimal('10.00'),
            is_active=True
        )
        
        self.product2 = Product.objects.create(
            name='Test Product 2',
            category=self.category,
            brand=self.brand,
            unit_type=self.unit_type,
            cost_price=Decimal('200.00'),
            selling_price=Decimal('300.00'),
            min_stock_level=Decimal('5.00'),
            is_active=True
        )
        
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_create_purchase_order_via_view(self):
        """Test creating a purchase order through the view"""
        url = reverse('purchases:order_create')
        
        # Prepare formset data
        data = {
            'supplier': self.supplier.id,
            'order_date': date.today().strftime('%Y-%m-%d'),
            'expected_date': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'status': 'purchase-order',
            'notes': 'Test purchase order',
            
            # Formset management form
            'items-TOTAL_FORMS': '2',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            
            # First item
            'items-0-product': self.product1.id,
            'items-0-quantity': '10.00',
            'items-0-unit_price': '100.00',
            'items-0-total_price': '1000.00',
            
            # Second item
            'items-1-product': self.product2.id,
            'items-1-quantity': '5.00',
            'items-1-unit_price': '200.00',
            'items-1-total_price': '1000.00',
        }
        
        response = self.client.post(url, data)
        
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        
        # Verify order was created
        order = PurchaseOrder.objects.get(supplier=self.supplier)
        self.assertEqual(order.status, 'purchase-order')
        self.assertEqual(order.notes, 'Test purchase order')
        self.assertEqual(order.created_by, self.user)
        self.assertTrue(order.order_number.startswith('PO-'))
        
        # Verify items were created
        self.assertEqual(order.items.count(), 2)
        
        item1 = order.items.get(product=self.product1)
        self.assertEqual(item1.quantity, Decimal('10.00'))
        self.assertEqual(item1.unit_price, Decimal('100.00'))
        self.assertEqual(item1.total_price, Decimal('1000.00'))
        
        item2 = order.items.get(product=self.product2)
        self.assertEqual(item2.quantity, Decimal('5.00'))
        self.assertEqual(item2.unit_price, Decimal('200.00'))
        self.assertEqual(item2.total_price, Decimal('1000.00'))
        
        # Verify total amount
        self.assertEqual(order.total_amount, Decimal('2000.00'))
    
    def test_create_purchase_order_with_single_item(self):
        """Test creating a purchase order with a single item"""
        url = reverse('purchases:order_create')
        
        data = {
            'supplier': self.supplier.id,
            'order_date': date.today().strftime('%Y-%m-%d'),
            'expected_date': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'status': 'purchase-order',
            
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            
            'items-0-product': self.product1.id,
            'items-0-quantity': '20.00',
            'items-0-unit_price': '100.00',
            'items-0-total_price': '2000.00',
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        order = PurchaseOrder.objects.get(supplier=self.supplier)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.total_amount, Decimal('2000.00'))
    
    def test_create_purchase_order_programmatically(self):
        """Test creating a purchase order programmatically"""
        order = PurchaseOrder.objects.create(
            supplier=self.supplier,
            order_date=date.today(),
            expected_date=date.today() + timedelta(days=7),
            status='purchase-order',
            notes='Programmatic test',
            created_by=self.user
        )
        
        # Add items
        item1 = PurchaseOrderItem.objects.create(
            purchase_order=order,
            product=self.product1,
            quantity=Decimal('15.00'),
            unit_price=Decimal('100.00'),
            total_price=Decimal('1500.00')
        )
        
        item2 = PurchaseOrderItem.objects.create(
            purchase_order=order,
            product=self.product2,
            quantity=Decimal('8.00'),
            unit_price=Decimal('200.00'),
            total_price=Decimal('1600.00')
        )
        
        # Update total
        order.total_amount = sum(item.total_price for item in order.items.all())
        order.save()
        
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.total_amount, Decimal('3100.00'))
        self.assertEqual(str(order), f"PO-{order.order_number} - {self.supplier.name}")


class GoodsReceiptTest(TestCase):
    """Test cases for goods receipt functionality"""
    
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
            address='Test Address',
            city='Test City',
            is_active=True
        )
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            is_active=True
        )
        
        self.unit_type = UnitType.objects.create(
            code='pcs',
            name='Pieces',
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
            category=self.category,
            brand=self.brand,
            unit_type=self.unit_type,
            cost_price=Decimal('100.00'),
            selling_price=Decimal('150.00'),
            min_stock_level=Decimal('10.00'),
            is_active=True
        )
        
        # Create a purchase order
        self.purchase_order = PurchaseOrder.objects.create(
            supplier=self.supplier,
            order_date=date.today(),
            expected_date=date.today() + timedelta(days=7),
            status='purchase-order',
            created_by=self.user
        )
        
        # Add order items
        self.order_item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            product=self.product,
            quantity=Decimal('100.00'),
            unit_price=Decimal('100.00'),
            total_price=Decimal('10000.00')
        )
        
        self.purchase_order.total_amount = Decimal('10000.00')
        self.purchase_order.save()
        
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_create_goods_receipt_via_view(self):
        """Test creating a goods receipt through the view"""
        url = reverse('purchases:receipt_create')
        
        data = {
            'purchase_order': self.purchase_order.id,
            'receipt_date': date.today().strftime('%Y-%m-%d'),
            'notes': 'First receipt',
            
            # Formset management form
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            
            # Receipt item
            'items-0-purchase_order_item': self.order_item.id,
            'items-0-warehouse': self.warehouse.id,
            'items-0-quantity': '50.00',
            'items-0-unit_cost': '100.00',
            'items-0-total_cost': '5000.00',
        }
        
        response = self.client.post(url, data)
        
        # Debug: print response if not redirecting
        if response.status_code != 302:
            print(f"Response status: {response.status_code}")
            if hasattr(response, 'context') and 'formset' in response.context:
                formset = response.context['formset']
                if not formset.is_valid():
                    print(f"Formset errors: {formset.errors}")
                    print(f"Formset non_form_errors: {formset.non_form_errors()}")
        
        # Should redirect to detail page
        self.assertEqual(response.status_code, 302, 
                        f"Expected redirect but got {response.status_code}. Check formset errors above.")
        
        # Verify receipt was created
        receipt = GoodsReceipt.objects.get(purchase_order=self.purchase_order)
        self.assertEqual(receipt.status, 'draft')
        self.assertEqual(receipt.notes, 'First receipt')
        self.assertEqual(receipt.created_by, self.user)
        self.assertTrue(receipt.receipt_number.startswith('GR-'))
        
        # Verify receipt item
        self.assertEqual(receipt.items.count(), 1)
        receipt_item = receipt.items.first()
        self.assertEqual(receipt_item.purchase_order_item, self.order_item)
        self.assertEqual(receipt_item.product, self.product)
        self.assertEqual(receipt_item.warehouse, self.warehouse)
        self.assertEqual(receipt_item.quantity, Decimal('50.00'))
        self.assertEqual(receipt_item.unit_cost, Decimal('100.00'))
        self.assertEqual(receipt_item.total_cost, Decimal('5000.00'))
        
        # Verify total amount
        self.assertEqual(receipt.total_amount, Decimal('5000.00'))
    
    def test_create_multiple_goods_receipts(self):
        """Test creating multiple goods receipts for the same purchase order"""
        # First receipt - receive 30 units
        receipt1 = GoodsReceipt.objects.create(
            purchase_order=self.purchase_order,
            receipt_date=date.today(),
            status='draft',
            created_by=self.user
        )
        
        GoodsReceiptItem.objects.create(
            goods_receipt=receipt1,
            purchase_order_item=self.order_item,
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal('30.00'),
            unit_cost=Decimal('100.00'),
            total_cost=Decimal('3000.00')
        )
        receipt1.save()  # Update total_amount
        
        # Second receipt - receive 40 units
        receipt2 = GoodsReceipt.objects.create(
            purchase_order=self.purchase_order,
            receipt_date=date.today() + timedelta(days=1),
            status='draft',
            created_by=self.user
        )
        
        GoodsReceiptItem.objects.create(
            goods_receipt=receipt2,
            purchase_order_item=self.order_item,
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal('40.00'),
            unit_cost=Decimal('100.00'),
            total_cost=Decimal('4000.00')
        )
        receipt2.save()  # Update total_amount
        
        # Verify both receipts exist
        self.assertEqual(self.purchase_order.goods_receipts.count(), 2)
        
        # Verify received quantities
        self.assertEqual(self.order_item.get_received_quantity(), Decimal('0.00'))  # Not confirmed yet
        self.assertEqual(self.order_item.get_remaining_quantity(), Decimal('100.00'))
        
        # Confirm first receipt
        receipt1.confirm_receipt()
        self.assertEqual(receipt1.status, 'received')
        self.assertEqual(self.order_item.get_received_quantity(), Decimal('30.00'))
        self.assertEqual(self.order_item.get_remaining_quantity(), Decimal('70.00'))
        
        # Confirm second receipt
        receipt2.confirm_receipt()
        self.assertEqual(receipt2.status, 'received')
        self.assertEqual(self.order_item.get_received_quantity(), Decimal('70.00'))
        self.assertEqual(self.order_item.get_remaining_quantity(), Decimal('30.00'))
    
    def test_confirm_goods_receipt_updates_inventory(self):
        """Test that confirming a goods receipt updates inventory"""
        # Initial inventory should be 0
        initial_qty = self.product.get_realtime_quantity()
        self.assertEqual(initial_qty, Decimal('0.00'))
        
        # Create and confirm receipt
        receipt = GoodsReceipt.objects.create(
            purchase_order=self.purchase_order,
            receipt_date=date.today(),
            status='draft',
            created_by=self.user
        )
        
        GoodsReceiptItem.objects.create(
            goods_receipt=receipt,
            purchase_order_item=self.order_item,
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal('50.00'),
            unit_cost=Decimal('100.00'),
            total_cost=Decimal('5000.00')
        )
        receipt.save()
        
        # Confirm receipt
        receipt.confirm_receipt()
        
        # Verify inventory increased
        new_qty = self.product.get_realtime_quantity()
        self.assertEqual(new_qty, Decimal('50.00'))
        
        # Verify received quantity
        self.assertEqual(self.order_item.get_received_quantity(), Decimal('50.00'))
        self.assertEqual(self.order_item.get_remaining_quantity(), Decimal('50.00'))
    
    def test_cancel_goods_receipt_reverses_inventory(self):
        """Test that cancelling a goods receipt reverses inventory"""
        # Create and confirm receipt
        receipt = GoodsReceipt.objects.create(
            purchase_order=self.purchase_order,
            receipt_date=date.today(),
            status='draft',
            created_by=self.user
        )
        
        GoodsReceiptItem.objects.create(
            goods_receipt=receipt,
            purchase_order_item=self.order_item,
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal('50.00'),
            unit_cost=Decimal('100.00'),
            total_cost=Decimal('5000.00')
        )
        receipt.save()
        
        # Confirm receipt
        receipt.confirm_receipt()
        self.assertEqual(self.product.get_realtime_quantity(), Decimal('50.00'))
        
        # Cancel receipt
        receipt.cancel_receipt()
        self.assertEqual(receipt.status, 'cancelled')
        
        # Verify inventory decreased
        self.assertEqual(self.product.get_realtime_quantity(), Decimal('0.00'))
        self.assertEqual(self.order_item.get_received_quantity(), Decimal('0.00'))
    
    def test_receive_quantity_validation(self):
        """Test that we cannot receive more than ordered quantity"""
        from .forms import GoodsReceiptItemFormSet
        
        receipt = GoodsReceipt.objects.create(
            purchase_order=self.purchase_order,
            receipt_date=date.today(),
            status='draft',
            created_by=self.user
        )
        
        # Try to create receipt item with quantity exceeding order quantity
        data = {
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-0-purchase_order_item': self.order_item.id,
            'items-0-warehouse': self.warehouse.id,
            'items-0-quantity': '150.00',  # More than ordered (100)
            'items-0-unit_cost': '100.00',
            'items-0-total_cost': '15000.00',
        }
        
        formset = GoodsReceiptItemFormSet(data, instance=receipt, purchase_order=self.purchase_order)
        
        # Formset should be invalid due to quantity validation
        self.assertFalse(formset.is_valid())
        # Check that the error is about quantity exceeding remaining
        if not formset.is_valid():
            form_errors = formset.errors[0] if formset.errors else {}
            # The validation should catch that 150 > 100 (remaining)
            self.assertTrue(any('quantity' in str(error).lower() or 'remaining' in str(error).lower() 
                              for error in form_errors.values() if error))
    
    def test_partial_receipt_workflow(self):
        """Test receiving goods in multiple partial receipts"""
        # First receipt: 30 units
        receipt1 = GoodsReceipt.objects.create(
            purchase_order=self.purchase_order,
            receipt_date=date.today(),
            status='draft',
            created_by=self.user
        )
        
        GoodsReceiptItem.objects.create(
            goods_receipt=receipt1,
            purchase_order_item=self.order_item,
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal('30.00'),
            unit_cost=Decimal('100.00'),
            total_cost=Decimal('3000.00')
        )
        receipt1.save()
        receipt1.confirm_receipt()
        
        # Verify
        self.assertEqual(self.order_item.get_received_quantity(), Decimal('30.00'))
        self.assertEqual(self.order_item.get_remaining_quantity(), Decimal('70.00'))
        self.assertEqual(self.product.get_realtime_quantity(), Decimal('30.00'))
        
        # Second receipt: 50 units
        receipt2 = GoodsReceipt.objects.create(
            purchase_order=self.purchase_order,
            receipt_date=date.today() + timedelta(days=1),
            status='draft',
            created_by=self.user
        )
        
        GoodsReceiptItem.objects.create(
            goods_receipt=receipt2,
            purchase_order_item=self.order_item,
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal('50.00'),
            unit_cost=Decimal('100.00'),
            total_cost=Decimal('5000.00')
        )
        receipt2.save()
        receipt2.confirm_receipt()
        
        # Verify
        self.assertEqual(self.order_item.get_received_quantity(), Decimal('80.00'))
        self.assertEqual(self.order_item.get_remaining_quantity(), Decimal('20.00'))
        self.assertEqual(self.product.get_realtime_quantity(), Decimal('80.00'))
        
        # Third receipt: remaining 20 units
        receipt3 = GoodsReceipt.objects.create(
            purchase_order=self.purchase_order,
            receipt_date=date.today() + timedelta(days=2),
            status='draft',
            created_by=self.user
        )
        
        GoodsReceiptItem.objects.create(
            goods_receipt=receipt3,
            purchase_order_item=self.order_item,
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal('20.00'),
            unit_cost=Decimal('100.00'),
            total_cost=Decimal('2000.00')
        )
        receipt3.save()
        receipt3.confirm_receipt()
        
        # Verify fully received
        self.assertEqual(self.order_item.get_received_quantity(), Decimal('100.00'))
        self.assertEqual(self.order_item.get_remaining_quantity(), Decimal('0.00'))
        self.assertTrue(self.order_item.is_fully_received())
        self.assertEqual(self.product.get_realtime_quantity(), Decimal('100.00'))
    
    def test_warehouse_specific_inventory(self):
        """Test inventory tracking by warehouse"""
        # Create second warehouse
        warehouse2 = Warehouse.objects.create(
            name='Secondary Warehouse',
            is_active=True
        )
        
        # Create receipt for first warehouse
        receipt1 = GoodsReceipt.objects.create(
            purchase_order=self.purchase_order,
            receipt_date=date.today(),
            status='draft',
            created_by=self.user
        )
        
        GoodsReceiptItem.objects.create(
            goods_receipt=receipt1,
            purchase_order_item=self.order_item,
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal('60.00'),
            unit_cost=Decimal('100.00'),
            total_cost=Decimal('6000.00')
        )
        receipt1.save()
        receipt1.confirm_receipt()
        
        # Create receipt for second warehouse
        receipt2 = GoodsReceipt.objects.create(
            purchase_order=self.purchase_order,
            receipt_date=date.today() + timedelta(days=1),
            status='draft',
            created_by=self.user
        )
        
        GoodsReceiptItem.objects.create(
            goods_receipt=receipt2,
            purchase_order_item=self.order_item,
            product=self.product,
            warehouse=warehouse2,
            quantity=Decimal('40.00'),
            unit_cost=Decimal('100.00'),
            total_cost=Decimal('4000.00')
        )
        receipt2.save()
        receipt2.confirm_receipt()
        
        # Verify total inventory
        total_qty = self.product.get_realtime_quantity()
        self.assertEqual(total_qty, Decimal('100.00'))
        
        # Verify warehouse-specific inventory
        warehouse1_qty = self.product.get_realtime_quantity(warehouse=self.warehouse)
        warehouse2_qty = self.product.get_realtime_quantity(warehouse=warehouse2)
        
        self.assertEqual(warehouse1_qty, Decimal('60.00'))
        self.assertEqual(warehouse2_qty, Decimal('40.00'))


class PurchaseOrderAndReceiptIntegrationTest(TestCase):
    """Integration tests for complete purchase order and receipt workflow"""
    
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
            address='Test Address',
            city='Test City',
            is_active=True
        )
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            is_active=True
        )
        
        self.unit_type = UnitType.objects.create(
            code='pcs',
            name='Pieces',
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
            category=self.category,
            brand=self.brand,
            unit_type=self.unit_type,
            cost_price=Decimal('100.00'),
            selling_price=Decimal('150.00'),
            min_stock_level=Decimal('10.00'),
            is_active=True
        )
        
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_complete_workflow_via_views(self):
        """Test complete workflow: create order -> create receipt -> confirm receipt"""
        # Step 1: Create purchase order
        order_data = {
            'supplier': self.supplier.id,
            'order_date': date.today().strftime('%Y-%m-%d'),
            'expected_date': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'status': 'purchase-order',
            'notes': 'Complete workflow test',
            
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            
            'items-0-product': self.product.id,
            'items-0-quantity': '100.00',
            'items-0-unit_price': '100.00',
            'items-0-total_price': '10000.00',
        }
        
        response = self.client.post(reverse('purchases:order_create'), order_data)
        self.assertEqual(response.status_code, 302)
        
        order = PurchaseOrder.objects.get(supplier=self.supplier)
        order_item = order.items.first()
        
        # Step 2: Create goods receipt
        receipt_data = {
            'purchase_order': order.id,
            'receipt_date': date.today().strftime('%Y-%m-%d'),
            'notes': 'First receipt',
            
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            
            'items-0-purchase_order_item': order_item.id,
            'items-0-warehouse': self.warehouse.id,
            'items-0-quantity': '60.00',
            'items-0-unit_cost': '100.00',
            'items-0-total_cost': '6000.00',
        }
        
        response = self.client.post(reverse('purchases:receipt_create'), receipt_data)
        self.assertEqual(response.status_code, 302)
        
        receipt = GoodsReceipt.objects.get(purchase_order=order)
        
        # Step 3: Confirm receipt
        response = self.client.post(reverse('purchases:receipt_confirm', kwargs={'pk': receipt.pk}))
        self.assertEqual(response.status_code, 302)
        
        receipt.refresh_from_db()
        self.assertEqual(receipt.status, 'received')
        
        # Verify inventory updated
        self.assertEqual(self.product.get_realtime_quantity(), Decimal('60.00'))
        self.assertEqual(order_item.get_received_quantity(), Decimal('60.00'))
        self.assertEqual(order_item.get_remaining_quantity(), Decimal('40.00'))
        
        # Step 4: Create second receipt for remaining quantity
        receipt2_data = {
            'purchase_order': order.id,
            'receipt_date': date.today().strftime('%Y-%m-%d'),
            'notes': 'Second receipt',
            
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            
            'items-0-purchase_order_item': order_item.id,
            'items-0-warehouse': self.warehouse.id,
            'items-0-quantity': '40.00',
            'items-0-unit_cost': '100.00',
            'items-0-total_cost': '4000.00',
        }
        
        response = self.client.post(reverse('purchases:receipt_create'), receipt2_data)
        self.assertEqual(response.status_code, 302)
        
        receipt2 = GoodsReceipt.objects.filter(purchase_order=order).exclude(pk=receipt.pk).first()
        
        # Confirm second receipt
        response = self.client.post(reverse('purchases:receipt_confirm', kwargs={'pk': receipt2.pk}))
        self.assertEqual(response.status_code, 302)
        
        # Verify fully received
        order_item.refresh_from_db()
        self.assertEqual(order_item.get_received_quantity(), Decimal('100.00'))
        self.assertEqual(order_item.get_remaining_quantity(), Decimal('0.00'))
        self.assertTrue(order_item.is_fully_received())
        self.assertEqual(self.product.get_realtime_quantity(), Decimal('100.00'))

