from django.core.management.base import BaseCommand
from stock.models import Product
from decimal import Decimal


class Command(BaseCommand):
    help = 'Update delivery charge per unit to 1 for all products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--charge',
            type=float,
            default=1.0,
            help='Delivery charge amount (default: 1.0)',
        )

    def handle(self, *args, **options):
        charge_amount = Decimal(str(options['charge']))
        
        self.stdout.write(f'Updating delivery charge to {charge_amount} for all products...')
        
        # Update all products
        updated_count = Product.objects.update(delivery_charge_per_unit=charge_amount)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Successfully updated {updated_count} products with delivery charge = {charge_amount}'
            )
        )

