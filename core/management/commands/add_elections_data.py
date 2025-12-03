from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
import random

from customers.models import Customer, CustomerLedger, CustomerCommitment
from suppliers.models import Supplier, SupplierLedger
from stock.models import Product, ProductCategory, ProductBrand, UnitType
from sales.models import SalesOrder, SalesOrderItem
from purchases.models import PurchaseOrder, PurchaseOrderItem


class Command(BaseCommand):
    help = 'Add electronics business related data to the ERP system'

    def handle(self, *args, **options):
        self.stdout.write('Creating electronics business data...')
        
        # Get or create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@electronics.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('✓ Created admin user (username: admin, password: admin123)')
        
        # Create unit types
        self.create_unit_types()
        
        # Create product categories
        self.create_product_categories()
        
        # Create product brands
        self.create_product_brands()
        
        # Create demo customers (electronics-related)
        self.create_electronics_customers(admin_user)
        
        # Create demo suppliers (electronics-related)
        self.create_electronics_suppliers(admin_user)
        
        # Create demo products (electronics)
        self.create_electronics_products()
        
        # Create purchase orders to build inventory
        self.create_purchase_orders(admin_user)
        
        # Create sales orders
        self.create_sales_orders(admin_user)
        
        self.stdout.write(
            self.style.SUCCESS('✓ Electronics business data created successfully!')
        )
        self.stdout.write('Login credentials:')
        self.stdout.write('Username: admin')
        self.stdout.write('Password: admin123')

    def create_unit_types(self):
        """Create unit types for electronics products"""
        units = [
            {'name': 'Piece', 'code': 'pcs', 'description': 'Individual pieces'},
            {'name': 'Box', 'code': 'box', 'description': 'Box of items'},
            {'name': 'Pack', 'code': 'pack', 'description': 'Pack of items'},
            {'name': 'Set', 'code': 'set', 'description': 'Set of items'},
            {'name': 'Pair', 'code': 'pair', 'description': 'Pair of items'},
        ]
        
        for unit in units:
            UnitType.objects.get_or_create(
                code=unit['code'],
                defaults={
                    'name': unit['name'],
                    'description': unit['description']
                }
            )
        self.stdout.write('✓ Created unit types')

    def create_product_categories(self):
        """Create product categories for electronics"""
        categories = [
            'Smartphones',
            'Laptops & Computers',
            'Tablets',
            'Audio Devices',
            'TVs & Monitors',
            'Accessories',
            'Gaming Devices',
            'Smart Home',
        ]
        
        for cat_name in categories:
            ProductCategory.objects.get_or_create(
                name=cat_name,
                defaults={'is_active': True}
            )
        self.stdout.write('✓ Created product categories')

    def create_product_brands(self):
        """Create product brands"""
        brands = [
            'Samsung',
            'Apple',
            'HP',
            'Dell',
            'Sony',
            'LG',
            'Xiaomi',
            'OnePlus',
        ]
        
        for brand_name in brands:
            ProductBrand.objects.get_or_create(
                name=brand_name,
                defaults={'is_active': True}
            )
        self.stdout.write('✓ Created product brands')

    def create_electronics_customers(self, user):
        """Create electronics-related customers"""
        customers_data = [
            {
                'name': 'Tech World Retail',
                'customer_type': 'retail',
                'contact_person': 'Mohammad Rahman',
                'phone': '+880-2-12345678',
                'address': 'Gulshan, Dhaka',
                'opening_balance': Decimal('50000.00')
            },
            {
                'name': 'Digital Hub Stores',
                'customer_type': 'wholesale',
                'contact_person': 'Abdul Karim',
                'phone': '+880-31-2345678',
                'address': 'Chittagong, Bangladesh',
                'opening_balance': Decimal('75000.00')
            },
            {
                'name': 'Smart Electronics Ltd',
                'customer_type': 'wholesale',
                'contact_person': 'Fatema Begum',
                'phone': '+880-821-3456789',
                'address': 'Sylhet, Bangladesh',
                'opening_balance': Decimal('60000.00')
            },
            {
                'name': 'Gadget Zone',
                'customer_type': 'retail',
                'contact_person': 'Hasan Ali',
                'phone': '+880-721-4567890',
                'address': 'Rajshahi, Bangladesh',
                'opening_balance': Decimal('40000.00')
            },
            {
                'name': 'Electronics Wholesale Co',
                'customer_type': 'wholesale',
                'contact_person': 'Nurul Islam',
                'phone': '+880-2-98765432',
                'address': 'Dhanmondi, Dhaka',
                'opening_balance': Decimal('100000.00')
            },
        ]
        
        for data in customers_data:
            customer, created = Customer.objects.get_or_create(
                name=data['name'],
                defaults={
                    'customer_type': data['customer_type'],
                    'contact_person': data['contact_person'],
                    'phone': data['phone'],
                    'address': data['address'],
                    'opening_balance': data['opening_balance'],
                    'current_balance': data['opening_balance'],
                    'is_active': True
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
                    created_by=user
                )
        
        self.stdout.write('✓ Created electronics customers')

    def create_electronics_suppliers(self, user):
        """Create electronics-related suppliers"""
        suppliers_data = [
            {
                'name': 'Samsung Electronics Bangladesh',
                'contact_person': 'Ahmed Hossain',
                'phone': '+880-2-11111111',
                'address': 'Gulshan, Dhaka',
                'opening_balance': Decimal('-50000.00')
            },
            {
                'name': 'Apple Authorized Distributor',
                'contact_person': 'Sultana Khatun',
                'phone': '+880-2-22222222',
                'address': 'Banani, Dhaka',
                'opening_balance': Decimal('-75000.00')
            },
            {
                'name': 'HP & Dell Supplier Co',
                'contact_person': 'Rashid Mia',
                'phone': '+880-2-33333333',
                'address': 'Dhanmondi, Dhaka',
                'opening_balance': Decimal('-40000.00')
            },
            {
                'name': 'Sony & LG Electronics',
                'contact_person': 'Farida Begum',
                'phone': '+880-2-44444444',
                'address': 'Motijheel, Dhaka',
                'opening_balance': Decimal('-30000.00')
            },
        ]
        
        for data in suppliers_data:
            supplier, created = Supplier.objects.get_or_create(
                name=data['name'],
                defaults={
                    'contact_person': data['contact_person'],
                    'phone': data['phone'],
                    'address': data['address'],
                    'opening_balance': data['opening_balance'],
                    'current_balance': data['opening_balance'],
                    'is_active': True
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
                    created_by=user
                )
        
        self.stdout.write('✓ Created electronics suppliers')

    def create_electronics_products(self):
        """Create electronics products"""
        category_smartphones = ProductCategory.objects.get(name='Smartphones')
        category_laptops = ProductCategory.objects.get(name='Laptops & Computers')
        category_tablets = ProductCategory.objects.get(name='Tablets')
        category_audio = ProductCategory.objects.get(name='Audio Devices')
        category_tv = ProductCategory.objects.get(name='TVs & Monitors')
        category_accessories = ProductCategory.objects.get(name='Accessories')
        category_gaming = ProductCategory.objects.get(name='Gaming Devices')
        category_smart_home = ProductCategory.objects.get(name='Smart Home')
        
        brand_samsung = ProductBrand.objects.get(name='Samsung')
        brand_apple = ProductBrand.objects.get(name='Apple')
        brand_hp = ProductBrand.objects.get(name='HP')
        brand_dell = ProductBrand.objects.get(name='Dell')
        brand_sony = ProductBrand.objects.get(name='Sony')
        brand_lg = ProductBrand.objects.get(name='LG')
        brand_xiaomi = ProductBrand.objects.get(name='Xiaomi')
        brand_oneplus = ProductBrand.objects.get(name='OnePlus')
        
        products_data = [
            # Smartphones
            {
                'name': 'Samsung Galaxy S24',
                'category': category_smartphones,
                'brand': brand_samsung,
                'unit_code': 'pcs',
                'cost_price': Decimal('80000.00'),
                'selling_price': Decimal('95000.00'),
                'min_stock_level': Decimal('10.00'),
            },
            {
                'name': 'iPhone 15 Pro',
                'category': category_smartphones,
                'brand': brand_apple,
                'unit_code': 'pcs',
                'cost_price': Decimal('120000.00'),
                'selling_price': Decimal('140000.00'),
                'min_stock_level': Decimal('5.00'),
            },
            {
                'name': 'Xiaomi Redmi Note 13',
                'category': category_smartphones,
                'brand': brand_xiaomi,
                'unit_code': 'pcs',
                'cost_price': Decimal('25000.00'),
                'selling_price': Decimal('30000.00'),
                'min_stock_level': Decimal('20.00'),
            },
            {
                'name': 'OnePlus 12',
                'category': category_smartphones,
                'brand': brand_oneplus,
                'unit_code': 'pcs',
                'cost_price': Decimal('65000.00'),
                'selling_price': Decimal('75000.00'),
                'min_stock_level': Decimal('15.00'),
            },
            # Laptops & Computers
            {
                'name': 'HP Pavilion 15',
                'category': category_laptops,
                'brand': brand_hp,
                'unit_code': 'pcs',
                'cost_price': Decimal('65000.00'),
                'selling_price': Decimal('80000.00'),
                'min_stock_level': Decimal('10.00'),
            },
            {
                'name': 'Dell Inspiron 15',
                'category': category_laptops,
                'brand': brand_dell,
                'unit_code': 'pcs',
                'cost_price': Decimal('70000.00'),
                'selling_price': Decimal('85000.00'),
                'min_stock_level': Decimal('10.00'),
            },
            {
                'name': 'MacBook Air M2',
                'category': category_laptops,
                'brand': brand_apple,
                'unit_code': 'pcs',
                'cost_price': Decimal('120000.00'),
                'selling_price': Decimal('140000.00'),
                'min_stock_level': Decimal('5.00'),
            },
            # Tablets
            {
                'name': 'iPad Air',
                'category': category_tablets,
                'brand': brand_apple,
                'unit_code': 'pcs',
                'cost_price': Decimal('55000.00'),
                'selling_price': Decimal('65000.00'),
                'min_stock_level': Decimal('10.00'),
            },
            {
                'name': 'Samsung Galaxy Tab S9',
                'category': category_tablets,
                'brand': brand_samsung,
                'unit_code': 'pcs',
                'cost_price': Decimal('60000.00'),
                'selling_price': Decimal('72000.00'),
                'min_stock_level': Decimal('8.00'),
            },
            # Audio Devices
            {
                'name': 'Sony WH-1000XM5 Headphones',
                'category': category_audio,
                'brand': brand_sony,
                'unit_code': 'pcs',
                'cost_price': Decimal('35000.00'),
                'selling_price': Decimal('42000.00'),
                'min_stock_level': Decimal('15.00'),
            },
            {
                'name': 'AirPods Pro',
                'category': category_audio,
                'brand': brand_apple,
                'unit_code': 'pcs',
                'cost_price': Decimal('28000.00'),
                'selling_price': Decimal('35000.00'),
                'min_stock_level': Decimal('20.00'),
            },
            # TVs & Monitors
            {
                'name': 'Samsung 55" 4K Smart TV',
                'category': category_tv,
                'brand': brand_samsung,
                'unit_code': 'pcs',
                'cost_price': Decimal('80000.00'),
                'selling_price': Decimal('95000.00'),
                'min_stock_level': Decimal('8.00'),
            },
            {
                'name': 'LG 43" LED TV',
                'category': category_tv,
                'brand': brand_lg,
                'unit_code': 'pcs',
                'cost_price': Decimal('45000.00'),
                'selling_price': Decimal('55000.00'),
                'min_stock_level': Decimal('10.00'),
            },
            # Accessories
            {
                'name': 'USB-C Cable',
                'category': category_accessories,
                'brand': brand_samsung,
                'unit_code': 'pcs',
                'cost_price': Decimal('300.00'),
                'selling_price': Decimal('500.00'),
                'min_stock_level': Decimal('100.00'),
            },
            {
                'name': 'Phone Case - Universal',
                'category': category_accessories,
                'brand': brand_samsung,
                'unit_code': 'pcs',
                'cost_price': Decimal('200.00'),
                'selling_price': Decimal('350.00'),
                'min_stock_level': Decimal('150.00'),
            },
            {
                'name': 'Wireless Charger',
                'category': category_accessories,
                'brand': brand_samsung,
                'unit_code': 'pcs',
                'cost_price': Decimal('1500.00'),
                'selling_price': Decimal('2500.00'),
                'min_stock_level': Decimal('50.00'),
            },
            # Gaming Devices
            {
                'name': 'PlayStation 5',
                'category': category_gaming,
                'brand': brand_sony,
                'unit_code': 'pcs',
                'cost_price': Decimal('55000.00'),
                'selling_price': Decimal('65000.00'),
                'min_stock_level': Decimal('5.00'),
            },
            # Smart Home
            {
                'name': 'Smart Bulb - WiFi',
                'category': category_smart_home,
                'brand': brand_xiaomi,
                'unit_code': 'pcs',
                'cost_price': Decimal('800.00'),
                'selling_price': Decimal('1200.00'),
                'min_stock_level': Decimal('50.00'),
            },
        ]
        
        for data in products_data:
            # Get unit type by code
            unit_type = UnitType.objects.get(code=data.get('unit_code', 'pcs'))
            Product.objects.get_or_create(
                name=data['name'],
                defaults={
                    'category': data['category'],
                    'brand': data['brand'],
                    'unit_type': unit_type,
                    'cost_price': data['cost_price'],
                    'selling_price': data['selling_price'],
                    'min_stock_level': data['min_stock_level'],
                    'is_active': True
                }
            )
        
        self.stdout.write('✓ Created electronics products')

    def create_purchase_orders(self, user):
        """Create purchase orders to build inventory"""
        suppliers = Supplier.objects.all()
        products = Product.objects.all()
        
        if not suppliers.exists() or not products.exists():
            return
        
        # Create purchase orders with status='goods-received' to build inventory
        existing_po_count = PurchaseOrder.objects.count()
        for i in range(8):
            supplier = random.choice(list(suppliers))
            order_date = timezone.now() - timedelta(days=random.randint(1, 25))
            
            order = PurchaseOrder.objects.create(
                order_number=f'PO-ELEC-{existing_po_count + i + 1:04d}',
                supplier=supplier,
                order_date=order_date,
                expected_date=order_date + timedelta(days=3),
                status='goods-received',  # This will add to inventory
                total_amount=Decimal('0.00'),
                created_by=user
            )
            
            # Add items to order
            num_items = random.randint(2, 5)
            selected_products = random.sample(list(products), min(num_items, products.count()))
            total_amount = Decimal('0.00')
            
            for product in selected_products:
                # Realistic quantities for electronics products
                if 'phone' in product.name.lower() or 'smartphone' in product.name.lower() or 'iphone' in product.name.lower():
                    quantity = Decimal(str(random.randint(5, 30)))
                elif 'laptop' in product.name.lower() or 'macbook' in product.name.lower():
                    quantity = Decimal(str(random.randint(3, 15)))
                elif 'tablet' in product.name.lower() or 'ipad' in product.name.lower():
                    quantity = Decimal(str(random.randint(5, 20)))
                elif 'tv' in product.name.lower() or 'monitor' in product.name.lower():
                    quantity = Decimal(str(random.randint(2, 10)))
                elif 'headphone' in product.name.lower() or 'airpod' in product.name.lower():
                    quantity = Decimal(str(random.randint(10, 50)))
                elif 'playstation' in product.name.lower() or 'gaming' in product.name.lower():
                    quantity = Decimal(str(random.randint(2, 8)))
                elif 'cable' in product.name.lower() or 'case' in product.name.lower() or 'charger' in product.name.lower() or 'bulb' in product.name.lower():
                    quantity = Decimal(str(random.randint(50, 200)))
                else:
                    quantity = Decimal(str(random.randint(5, 30)))
                
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
        
        self.stdout.write('✓ Created purchase orders (inventory built)')

    def create_sales_orders(self, user):
        """Create sales orders for electronics"""
        customers = Customer.objects.all()
        products = Product.objects.all()
        
        if not customers.exists() or not products.exists():
            return
        
        # Create sales orders with status='delivered'
        existing_so_count = SalesOrder.objects.count()
        for i in range(15):
            customer = random.choice(list(customers))
            order_date = timezone.now() - timedelta(days=random.randint(1, 20))
            
            order = SalesOrder.objects.create(
                order_number=f'SO-ELEC-{existing_so_count + i + 1:04d}',
                customer=customer,
                order_date=order_date,
                delivery_date=order_date + timedelta(days=2),
                status='delivered',  # This will reduce inventory
                sales_type='regular',
                total_amount=Decimal('0.00'),
                created_by=user
            )
            
            # Add items to order
            num_items = random.randint(2, 5)
            selected_products = random.sample(list(products), min(num_items, products.count()))
            total_amount = Decimal('0.00')
            
            for product in selected_products:
                # Realistic quantities for electronics sales
                if 'phone' in product.name.lower() or 'smartphone' in product.name.lower() or 'iphone' in product.name.lower():
                    quantity = Decimal(str(random.randint(1, 15)))
                elif 'laptop' in product.name.lower() or 'macbook' in product.name.lower():
                    quantity = Decimal(str(random.randint(1, 8)))
                elif 'tablet' in product.name.lower() or 'ipad' in product.name.lower():
                    quantity = Decimal(str(random.randint(1, 10)))
                elif 'tv' in product.name.lower() or 'monitor' in product.name.lower():
                    quantity = Decimal(str(random.randint(1, 5)))
                elif 'headphone' in product.name.lower() or 'airpod' in product.name.lower():
                    quantity = Decimal(str(random.randint(2, 20)))
                elif 'playstation' in product.name.lower() or 'gaming' in product.name.lower():
                    quantity = Decimal(str(random.randint(1, 3)))
                elif 'cable' in product.name.lower() or 'case' in product.name.lower() or 'charger' in product.name.lower() or 'bulb' in product.name.lower():
                    quantity = Decimal(str(random.randint(10, 100)))
                else:
                    quantity = Decimal(str(random.randint(1, 10)))
                
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
        
        self.stdout.write('✓ Created sales orders')

