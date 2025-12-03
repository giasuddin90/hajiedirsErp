from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
import random

from customers.models import Customer, CustomerLedger, CustomerCommitment
from suppliers.models import Supplier, SupplierLedger
from stock.models import Product, Stock, StockAlert
from sales.models import SalesOrder, SalesOrderItem, SalesInvoice, SalesInvoiceItem, SalesPayment
from purchases.models import PurchaseOrder, PurchaseOrderItem, PurchaseInvoice, PurchaseInvoiceItem, PurchasePayment


class Command(BaseCommand):
    help = 'Add demo data to the ERP system'

    def handle(self, *args, **options):
        self.stdout.write('Creating demo data...')
        
        # Get admin user
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Admin user not found. Please create superuser first.')
            )
            return
        
        # Create demo customers
        self.create_demo_customers(admin_user)
        
        # Create demo suppliers
        self.create_demo_suppliers(admin_user)
        
        # Create demo products
        self.create_demo_products(admin_user)
        
        # Create demo sales data
        self.create_demo_sales_data(admin_user)
        
        # Create demo purchase data
        self.create_demo_purchase_data(admin_user)
        
        self.stdout.write(
            self.style.SUCCESS('Demo data created successfully!')
        )
        self.stdout.write('Login credentials:')
        self.stdout.write('Username: admin')
        self.stdout.write('Password: admin123')

    def create_demo_customers(self, user):
        """Create demo customers with sample data"""
        customers_data = [
            {
                'name': 'ABC Construction Ltd',
                'contact_person': 'John Smith',
                'email': 'john@abcconstruction.com',
                'phone': '+1-555-0101',
                'address': '123 Main St, New York, NY 10001',
                'opening_balance': Decimal('5000.00')
            },
            {
                'name': 'XYZ Builders Inc',
                'contact_person': 'Sarah Johnson',
                'email': 'sarah@xyzbuilders.com',
                'phone': '+1-555-0102',
                'address': '456 Oak Ave, Los Angeles, CA 90210',
                'opening_balance': Decimal('7500.00')
            },
            {
                'name': 'Metro Construction Co',
                'contact_person': 'Mike Davis',
                'email': 'mike@metroconstruction.com',
                'phone': '+1-555-0103',
                'address': '789 Pine St, Chicago, IL 60601',
                'opening_balance': Decimal('3000.00')
            },
            {
                'name': 'Elite Builders',
                'contact_person': 'Lisa Wilson',
                'email': 'lisa@elitebuilders.com',
                'phone': '+1-555-0104',
                'address': '321 Elm St, Houston, TX 77001',
                'opening_balance': Decimal('8500.00')
            }
        ]
        
        for data in customers_data:
            customer, created = Customer.objects.get_or_create(
                name=data['name'],
                defaults={
                    'customer_type': 'wholesale',
                    'contact_person': data['contact_person'],
                    'email': data['email'],
                    'phone': data['phone'],
                    'address': data['address'],
                    'opening_balance': data['opening_balance'],
                    'current_balance': data['opening_balance']
                }
            )
            
            if created:
                # Create opening balance ledger entry
                CustomerLedger.objects.create(
                    customer=customer,
                    transaction_type='opening_balance',
                    amount=data['opening_balance'],
                    description='Opening Balance',
                    transaction_date=timezone.now() - timedelta(days=30),
                    payment_method='cash',
                    created_by=user
                )
                
                # Create some demo commitments for this customer
                for i in range(random.randint(1, 3)):
                    CustomerCommitment.objects.create(
                        customer=customer,
                        commitment_date=timezone.now().date() + timedelta(days=random.randint(1, 30)),
                        amount=Decimal(str(random.randint(1000, 10000))),
                        description=f'Payment commitment for {customer.name} - Amount {random.randint(1000, 10000)}',
                        is_reminded=random.choice([True, False]),
                        is_fulfilled=random.choice([True, False])
                    )
        
        self.stdout.write('✓ Created demo customers and commitments')

    def create_demo_suppliers(self, user):
        """Create demo suppliers with sample data"""
        suppliers_data = [
            {
                'name': 'Premium Materials Co',
                'contact_person': 'Robert Brown',
                'email': 'robert@premiummaterials.com',
                'phone': '+1-555-0201',
                'address': '100 Industrial Blvd, Detroit, MI 48201',
                'opening_balance': Decimal('-2000.00')
            },
            {
                'name': 'Steel & Cement Ltd',
                'contact_person': 'Jennifer Lee',
                'email': 'jennifer@steelcement.com',
                'phone': '+1-555-0202',
                'address': '200 Factory St, Pittsburgh, PA 15201',
                'opening_balance': Decimal('-3500.00')
            },
            {
                'name': 'Quality Tools Inc',
                'contact_person': 'David Miller',
                'email': 'david@qualitytools.com',
                'phone': '+1-555-0203',
                'address': '300 Workshop Ave, Milwaukee, WI 53201',
                'opening_balance': Decimal('-1500.00')
            }
        ]
        
        for data in suppliers_data:
            supplier, created = Supplier.objects.get_or_create(
                name=data['name'],
                defaults={
                    'contact_person': data['contact_person'],
                    'email': data['email'],
                    'phone': data['phone'],
                    'address': data['address'],
                    'opening_balance': data['opening_balance'],
                    'current_balance': data['opening_balance']
                }
            )
            
            if created:
                # Create opening balance ledger entry
                SupplierLedger.objects.create(
                    supplier=supplier,
                    transaction_type='opening_balance',
                    amount=abs(data['opening_balance']),
                    description='Opening Balance',
                    transaction_date=timezone.now() - timedelta(days=30),
                    payment_method='cash',
                    created_by=user
                )
        
        self.stdout.write('✓ Created demo suppliers')

    def create_demo_products(self, user):
        """Create demo products with stock data"""
        products_data = [
            {
                'name': 'Portland Cement',
                'unit_type': 'bag',
                'unit_name': '50kg Bag',
                'brand': 'Premium Cement',
                'cost_price': Decimal('8.50'),
                'selling_price': Decimal('12.00'),
                'min_stock_level': Decimal('100.00'),
                'stock_quantity': Decimal('500.00')
            },
            {
                'name': 'Steel Rebar 12mm',
                'unit_type': 'kg',
                'unit_name': 'Kilogram',
                'brand': 'SteelMax',
                'cost_price': Decimal('2.50'),
                'selling_price': Decimal('3.50'),
                'min_stock_level': Decimal('1000.00'),
                'stock_quantity': Decimal('2500.00')
            },
            {
                'name': 'Concrete Blocks',
                'unit_type': 'pcs',
                'unit_name': 'Pieces',
                'brand': 'BlockMaster',
                'cost_price': Decimal('1.20'),
                'selling_price': Decimal('1.80'),
                'min_stock_level': Decimal('500.00'),
                'stock_quantity': Decimal('2000.00')
            },
            {
                'name': 'Sand (Fine)',
                'unit_type': 'kg',
                'unit_name': 'Kilogram',
                'brand': 'SandPro',
                'cost_price': Decimal('0.15'),
                'selling_price': Decimal('0.25'),
                'min_stock_level': Decimal('5000.00'),
                'stock_quantity': Decimal('15000.00')
            },
            {
                'name': 'Gravel (Coarse)',
                'unit_type': 'kg',
                'unit_name': 'Kilogram',
                'brand': 'GravelMax',
                'cost_price': Decimal('0.20'),
                'selling_price': Decimal('0.30'),
                'min_stock_level': Decimal('3000.00'),
                'stock_quantity': Decimal('8000.00')
            },
            {
                'name': 'Steel Wire Mesh',
                'unit_type': 'sqft',
                'unit_name': 'Square Feet',
                'brand': 'MeshPro',
                'cost_price': Decimal('2.00'),
                'selling_price': Decimal('3.00'),
                'min_stock_level': Decimal('200.00'),
                'stock_quantity': Decimal('500.00')
            }
        ]
        
        for data in products_data:
            product, created = Product.objects.get_or_create(
                name=data['name'],
                defaults={
                    'unit_type': data['unit_type'],
                    'unit_name': data['unit_name'],
                    'brand': data['brand'],
                    'cost_price': data['cost_price'],
                    'selling_price': data['selling_price'],
                    'min_stock_level': data['min_stock_level']
                }
            )
            
            if created:
                # Create stock record
                Stock.objects.create(
                    product=product,
                    quantity=data['stock_quantity'],
                    unit_cost=data['cost_price']
                )
        
        self.stdout.write('✓ Created demo products and stock')

    def create_demo_sales_data(self, user):
        """Create demo sales orders and invoices"""
        customers = Customer.objects.all()
        products = Product.objects.all()
        
        if not customers.exists() or not products.exists():
            return
        
        # Create sales orders
        for i in range(5):
            customer = random.choice(customers)
            order_date = timezone.now() - timedelta(days=random.randint(1, 20))
            
            order = SalesOrder.objects.create(
                order_number=f'SO-{i+1:04d}',
                customer=customer,
                order_date=order_date,
                delivery_date=order_date + timedelta(days=7),
                status='delivered' if i < 3 else 'pending',
                total_amount=Decimal('0.00'),
                created_by=user
            )
            
            # Add items to order
            num_items = random.randint(2, 4)
            selected_products = random.sample(list(products), num_items)
            total_amount = Decimal('0.00')
            
            for product in selected_products:
                quantity = Decimal(str(random.randint(10, 100)))
                unit_price = product.selling_price
                total_price = quantity * unit_price
                
                SalesOrderItem.objects.create(
                    sales_order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price
                )
                
                total_amount += total_price
            
            order.total_amount = total_amount
            order.save()
            
            # Create invoice for delivered orders
            if order.status == 'delivered':
                invoice = SalesInvoice.objects.create(
                    invoice_number=f'INV-{order.id:04d}',
                    customer=customer,
                    sales_order=order,
                    invoice_date=order_date + timedelta(days=1),
                    payment_type='credit',
                    subtotal=total_amount,
                    total_amount=total_amount,
                    paid_amount=total_amount if i < 2 else Decimal('0.00'),
                    due_amount=Decimal('0.00') if i < 2 else total_amount,
                    created_by=user
                )
                
                # Add invoice items
                for item in order.items.all():
                    SalesInvoiceItem.objects.create(
                        sales_invoice=invoice,
                        product=item.product,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        total_price=item.total_price
                    )
                
                # Create payment for paid invoices
                if invoice.paid_amount > 0:
                    SalesPayment.objects.create(
                        sales_invoice=invoice,
                        payment_date=invoice.invoice_date + timedelta(days=5),
                        payment_method='cash',
                        amount=total_amount,
                        reference=f'PAY-{invoice.id:04d}',
                        notes='Payment received'
                    )
        
        self.stdout.write('✓ Created demo sales data')

    def create_demo_purchase_data(self, user):
        """Create demo purchase orders and invoices"""
        suppliers = Supplier.objects.all()
        products = Product.objects.all()
        
        if not suppliers.exists() or not products.exists():
            return
        
        # Create purchase orders
        for i in range(4):
            supplier = random.choice(suppliers)
            order_date = timezone.now() - timedelta(days=random.randint(1, 15))
            
            order = PurchaseOrder.objects.create(
                order_number=f'PO-{i+1:04d}',
                supplier=supplier,
                order_date=order_date,
                expected_date=order_date + timedelta(days=5),
                status='received' if i < 3 else 'pending',
                total_amount=Decimal('0.00'),
                created_by=user
            )
            
            # Add items to order
            num_items = random.randint(2, 3)
            selected_products = random.sample(list(products), num_items)
            total_amount = Decimal('0.00')
            
            for product in selected_products:
                quantity = Decimal(str(random.randint(50, 200)))
                unit_price = product.cost_price
                total_price = quantity * unit_price
                
                PurchaseOrderItem.objects.create(
                    purchase_order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price
                )
                
                total_amount += total_price
            
            order.total_amount = total_amount
            order.save()
            
            # Create invoice for received orders
            if order.status == 'received':
                invoice = PurchaseInvoice.objects.create(
                    invoice_number=f'PINV-{order.id:04d}',
                    supplier=supplier,
                    purchase_order=order,
                    invoice_date=order_date + timedelta(days=2),
                    payment_type='credit',
                    subtotal=total_amount,
                    total_amount=total_amount,
                    paid_amount=total_amount if i < 2 else Decimal('0.00'),
                    due_amount=Decimal('0.00') if i < 2 else total_amount,
                    created_by=user
                )
                
                # Add invoice items
                for item in order.items.all():
                    PurchaseInvoiceItem.objects.create(
                        purchase_invoice=invoice,
                        product=item.product,
                        quantity=item.quantity,
                        unit_cost=item.unit_price,
                        total_cost=item.total_price
                    )
                
                # Create payment for paid invoices
                if invoice.paid_amount > 0:
                    PurchasePayment.objects.create(
                        purchase_invoice=invoice,
                        payment_date=invoice.invoice_date + timedelta(days=3),
                        payment_method='cash',
                        amount=total_amount,
                        reference=f'PAY-{invoice.id:04d}',
                        notes='Payment made'
                    )
        
        self.stdout.write('✓ Created demo purchase data')