from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from stock.models import Product, ProductCategory, ProductBrand, UnitType


class Command(BaseCommand):
    help = 'Load building materials data (Rod, Cement, Tiles) for Bangladeshi market and remove past data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-categories',
            action='store_true',
            help='Keep existing categories and brands',
        )

    def handle(self, *args, **options):
        self.stdout.write('Loading building materials data for Bangladeshi market...')
        
        with transaction.atomic():
            # Clear existing products
            product_count = Product.objects.count()
            Product.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'Deleted {product_count} existing products')
            )
            
            if not options['keep_categories']:
                # Clear existing categories and brands
                ProductCategory.objects.all().delete()
                ProductBrand.objects.all().delete()
                self.stdout.write(
                    self.style.WARNING('Deleted existing categories and brands')
                )
            
            # Create or get unit types (keep these as they're standard)
            unit_types = self.create_unit_types()
            
            # Create categories
            categories = self.create_categories()
            
            # Create brands
            brands = self.create_brands()
            
            # Create products
            self.create_products(unit_types, categories, brands)
            
            self.stdout.write(
                self.style.SUCCESS('✓ Building materials data loaded successfully!')
            )

    def create_unit_types(self):
        """Create or get unit types for building materials"""
        unit_types_data = [
            {'code': 'ton', 'name': 'Ton', 'description': 'Metric ton (1000 kg)'},
            {'code': 'kg', 'name': 'Kilogram', 'description': 'Kilogram'},
            {'code': 'bag', 'name': 'Bag', 'description': '50kg bag'},
            {'code': 'pcs', 'name': 'Pieces', 'description': 'Number of pieces'},
            {'code': 'sqft', 'name': 'Square Feet', 'description': 'Square feet'},
            {'code': 'bundle', 'name': 'Bundle', 'description': 'Bundle of rods'},
        ]
        
        unit_types = {}
        for data in unit_types_data:
            unit_type, created = UnitType.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'is_active': True
                }
            )
            unit_types[data['code']] = unit_type
            if created:
                self.stdout.write(f'  Created unit type: {data["name"]}')
        
        return unit_types

    def create_categories(self):
        """Create product categories"""
        categories_data = [
            {'name': 'Steel Rod', 'description': 'Steel reinforcement bars (Rebar)'},
            {'name': 'Cement', 'description': 'Portland cement and other cement types'},
            {'name': 'Tiles', 'description': 'Ceramic, vitrified, and other tiles'},
        ]
        
        categories = {}
        for data in categories_data:
            category, created = ProductCategory.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'is_active': True
                }
            )
            categories[data['name']] = category
            if created:
                self.stdout.write(f'  Created category: {data["name"]}')
        
        return categories

    def create_brands(self):
        """Create brands for Bangladeshi market"""
        brands_data = [
            # Steel Rod brands
            {'name': 'BSRM', 'description': 'Bangladesh Steel Re-Rolling Mills'},
            {'name': 'KSRM', 'description': 'Kabir Steel Re-Rolling Mills'},
            {'name': 'Anwar', 'description': 'Anwar Ispat Limited'},
            {'name': 'GPH', 'description': 'GPH Ispat Limited'},
            {'name': 'RRM', 'description': 'Ratanpur Steel Re-Rolling Mills'},
            
            # Cement brands
            {'name': 'Shah Cement', 'description': 'Shah Cement Industries Limited'},
            {'name': 'Crown Cement', 'description': 'Crown Cement'},
            {'name': 'Seven Rings', 'description': 'Seven Rings Cement'},
            {'name': 'Fresh Cement', 'description': 'Fresh Cement'},
            {'name': 'Lafarge Holcim', 'description': 'LafargeHolcim Bangladesh'},
            {'name': 'Bashundhara', 'description': 'Bashundhara Cement'},
            
            # Tile brands
            {'name': 'RAK Ceramics', 'description': 'RAK Ceramics Bangladesh'},
            {'name': 'Fu-Wang', 'description': 'Fu-Wang Ceramic Industries'},
            {'name': 'Monno', 'description': 'Monno Ceramic Industries'},
            {'name': 'Great Wall', 'description': 'Great Wall Ceramic Industries'},
            {'name': 'Concorde', 'description': 'Concorde Ceramic Industries'},
        ]
        
        brands = {}
        for data in brands_data:
            brand, created = ProductBrand.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'is_active': True
                }
            )
            brands[data['name']] = brand
            if created:
                self.stdout.write(f'  Created brand: {data["name"]}')
        
        return brands

    def create_products(self, unit_types, categories, brands):
        """Create building material products for Bangladeshi market"""
        
        # Steel Rod products (prices in BDT per ton, typical market prices)
        rod_products = [
            {
                'name': 'Steel Rod 40mm',
                'category': categories['Steel Rod'],
                'brand': brands['BSRM'],
                'unit_type': unit_types['ton'],
                'cost_price': Decimal('85000.00'),  # BDT per ton
                'selling_price': Decimal('92000.00'),
                'min_stock_level': Decimal('5.00'),  # 5 tons minimum
                'description': '40mm diameter steel reinforcement bar'
            },
            {
                'name': 'Steel Rod 32mm',
                'category': categories['Steel Rod'],
                'brand': brands['BSRM'],
                'unit_type': unit_types['ton'],
                'cost_price': Decimal('85000.00'),
                'selling_price': Decimal('92000.00'),
                'min_stock_level': Decimal('5.00'),
                'description': '32mm diameter steel reinforcement bar'
            },
            {
                'name': 'Steel Rod 25mm',
                'category': categories['Steel Rod'],
                'brand': brands['BSRM'],
                'unit_type': unit_types['ton'],
                'cost_price': Decimal('85000.00'),
                'selling_price': Decimal('92000.00'),
                'min_stock_level': Decimal('5.00'),
                'description': '25mm diameter steel reinforcement bar'
            },
            {
                'name': 'Steel Rod 20mm',
                'category': categories['Steel Rod'],
                'brand': brands['KSRM'],
                'unit_type': unit_types['ton'],
                'cost_price': Decimal('85000.00'),
                'selling_price': Decimal('92000.00'),
                'min_stock_level': Decimal('5.00'),
                'description': '20mm diameter steel reinforcement bar'
            },
            {
                'name': 'Steel Rod 16mm',
                'category': categories['Steel Rod'],
                'brand': brands['KSRM'],
                'unit_type': unit_types['ton'],
                'cost_price': Decimal('85000.00'),
                'selling_price': Decimal('92000.00'),
                'min_stock_level': Decimal('5.00'),
                'description': '16mm diameter steel reinforcement bar'
            },
            {
                'name': 'Steel Rod 12mm',
                'category': categories['Steel Rod'],
                'brand': brands['Anwar'],
                'unit_type': unit_types['ton'],
                'cost_price': Decimal('85000.00'),
                'selling_price': Decimal('92000.00'),
                'min_stock_level': Decimal('5.00'),
                'description': '12mm diameter steel reinforcement bar'
            },
            {
                'name': 'Steel Rod 10mm',
                'category': categories['Steel Rod'],
                'brand': brands['Anwar'],
                'unit_type': unit_types['ton'],
                'cost_price': Decimal('85000.00'),
                'selling_price': Decimal('92000.00'),
                'min_stock_level': Decimal('5.00'),
                'description': '10mm diameter steel reinforcement bar'
            },
            {
                'name': 'Steel Rod 8mm',
                'category': categories['Steel Rod'],
                'brand': brands['GPH'],
                'unit_type': unit_types['ton'],
                'cost_price': Decimal('85000.00'),
                'selling_price': Decimal('92000.00'),
                'min_stock_level': Decimal('5.00'),
                'description': '8mm diameter steel reinforcement bar'
            },
        ]
        
        # Cement products (prices in BDT per 50kg bag)
        cement_products = [
            {
                'name': 'Portland Cement 50kg',
                'category': categories['Cement'],
                'brand': brands['Shah Cement'],
                'unit_type': unit_types['bag'],
                'cost_price': Decimal('520.00'),  # BDT per bag
                'selling_price': Decimal('580.00'),
                'min_stock_level': Decimal('100.00'),  # 100 bags minimum
                'description': 'Shah Portland Cement 50kg bag'
            },
            {
                'name': 'Portland Cement 50kg',
                'category': categories['Cement'],
                'brand': brands['Crown Cement'],
                'unit_type': unit_types['bag'],
                'cost_price': Decimal('510.00'),
                'selling_price': Decimal('570.00'),
                'min_stock_level': Decimal('100.00'),
                'description': 'Crown Portland Cement 50kg bag'
            },
            {
                'name': 'Portland Cement 50kg',
                'category': categories['Cement'],
                'brand': brands['Seven Rings'],
                'unit_type': unit_types['bag'],
                'cost_price': Decimal('515.00'),
                'selling_price': Decimal('575.00'),
                'min_stock_level': Decimal('100.00'),
                'description': 'Seven Rings Portland Cement 50kg bag'
            },
            {
                'name': 'Portland Cement 50kg',
                'category': categories['Cement'],
                'brand': brands['Fresh Cement'],
                'unit_type': unit_types['bag'],
                'cost_price': Decimal('505.00'),
                'selling_price': Decimal('565.00'),
                'min_stock_level': Decimal('100.00'),
                'description': 'Fresh Portland Cement 50kg bag'
            },
            {
                'name': 'Portland Cement 50kg',
                'category': categories['Cement'],
                'brand': brands['Lafarge Holcim'],
                'unit_type': unit_types['bag'],
                'cost_price': Decimal('530.00'),
                'selling_price': Decimal('590.00'),
                'min_stock_level': Decimal('100.00'),
                'description': 'LafargeHolcim Portland Cement 50kg bag'
            },
            {
                'name': 'Portland Cement 50kg',
                'category': categories['Cement'],
                'brand': brands['Bashundhara'],
                'unit_type': unit_types['bag'],
                'cost_price': Decimal('525.00'),
                'selling_price': Decimal('585.00'),
                'min_stock_level': Decimal('100.00'),
                'description': 'Bashundhara Portland Cement 50kg bag'
            },
        ]
        
        # Tile products (prices in BDT per square feet)
        tile_products = [
            {
                'name': 'Ceramic Floor Tile 2x2',
                'category': categories['Tiles'],
                'brand': brands['RAK Ceramics'],
                'unit_type': unit_types['sqft'],
                'cost_price': Decimal('45.00'),  # BDT per sqft
                'selling_price': Decimal('65.00'),
                'min_stock_level': Decimal('500.00'),  # 500 sqft minimum
                'description': 'RAK Ceramic floor tile 2x2 feet',
                'sqft_per_pcs': Decimal('4.00')  # 2x2 = 4 sqft
            },
            {
                'name': 'Ceramic Floor Tile 2x2',
                'category': categories['Tiles'],
                'brand': brands['Fu-Wang'],
                'unit_type': unit_types['sqft'],
                'cost_price': Decimal('40.00'),
                'selling_price': Decimal('58.00'),
                'min_stock_level': Decimal('500.00'),
                'description': 'Fu-Wang Ceramic floor tile 2x2 feet',
                'sqft_per_pcs': Decimal('4.00')
            },
            {
                'name': 'Vitrified Tile 2x2',
                'category': categories['Tiles'],
                'brand': brands['RAK Ceramics'],
                'unit_type': unit_types['sqft'],
                'cost_price': Decimal('85.00'),
                'selling_price': Decimal('120.00'),
                'min_stock_level': Decimal('300.00'),
                'description': 'RAK Vitrified tile 2x2 feet',
                'sqft_per_pcs': Decimal('4.00')
            },
            {
                'name': 'Vitrified Tile 2x2',
                'category': categories['Tiles'],
                'brand': brands['Monno'],
                'unit_type': unit_types['sqft'],
                'cost_price': Decimal('75.00'),
                'selling_price': Decimal('110.00'),
                'min_stock_level': Decimal('300.00'),
                'description': 'Monno Vitrified tile 2x2 feet',
                'sqft_per_pcs': Decimal('4.00')
            },
            {
                'name': 'Wall Tile 1x1',
                'category': categories['Tiles'],
                'brand': brands['RAK Ceramics'],
                'unit_type': unit_types['sqft'],
                'cost_price': Decimal('35.00'),
                'selling_price': Decimal('50.00'),
                'min_stock_level': Decimal('500.00'),
                'description': 'RAK Wall tile 1x1 feet',
                'sqft_per_pcs': Decimal('1.00')
            },
            {
                'name': 'Wall Tile 1x1',
                'category': categories['Tiles'],
                'brand': brands['Great Wall'],
                'unit_type': unit_types['sqft'],
                'cost_price': Decimal('30.00'),
                'selling_price': Decimal('45.00'),
                'min_stock_level': Decimal('500.00'),
                'description': 'Great Wall wall tile 1x1 feet',
                'sqft_per_pcs': Decimal('1.00')
            },
            {
                'name': 'Ceramic Floor Tile 1.5x1.5',
                'category': categories['Tiles'],
                'brand': brands['Concorde'],
                'unit_type': unit_types['sqft'],
                'cost_price': Decimal('38.00'),
                'selling_price': Decimal('55.00'),
                'min_stock_level': Decimal('500.00'),
                'description': 'Concorde Ceramic floor tile 1.5x1.5 feet',
                'sqft_per_pcs': Decimal('2.25')
            },
        ]
        
        # Combine all products
        all_products = rod_products + cement_products + tile_products
        
        # Create products
        created_count = 0
        for product_data in all_products:
            product = Product.objects.create(
                name=product_data['name'],
                category=product_data['category'],
                brand=product_data['brand'],
                unit_type=product_data['unit_type'],
                cost_price=product_data['cost_price'],
                selling_price=product_data['selling_price'],
                min_stock_level=product_data['min_stock_level'],
                description=product_data.get('description', ''),
                sqft_per_pcs=product_data.get('sqft_per_pcs', Decimal('0.00')),
                is_active=True
            )
            created_count += 1
            self.stdout.write(f'  Created: {product.name} ({product.brand.name})')
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Created {created_count} building material products')
        )

