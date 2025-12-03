from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from reports.models import ReportTemplate, ReportSchedule
from datetime import datetime, timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Sets up default report templates and schedules'

    def handle(self, *args, **options):
        self.stdout.write('Setting up report templates...')
        
        # Get or create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        # Create report templates
        self.create_report_templates(admin_user)
        
        # Create report schedules
        self.create_report_schedules(admin_user)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up report templates and schedules!')
        )

    def create_report_templates(self, user):
        """Create default report templates"""
        
        # Financial Report Template
        financial_template, created = ReportTemplate.objects.get_or_create(
            name='Financial Report Template',
            defaults={
                'report_type': 'financial',
                'description': 'Comprehensive financial report including P&L, Balance Sheet, and Cash Flow',
                'template_content': '''
                <h1>Financial Report</h1>
                <h2>Period: {{ start_date }} to {{ end_date }}</h2>
                
                <h3>Revenue Summary</h3>
                <p>Total Sales: ৳{{ total_sales }}</p>
                <p>Other Income: ৳{{ other_income }}</p>
                <p>Total Revenue: ৳{{ total_revenue }}</p>
                
                <h3>Expense Summary</h3>
                <p>Total Expenses: ৳{{ total_expenses }}</p>
                
                <h3>Profit & Loss</h3>
                <p>Gross Profit: ৳{{ gross_profit }}</p>
                <p>Profit Margin: {{ profit_margin }}%</p>
                
                <h3>Cash Flow</h3>
                <p>Net Cash Flow: ৳{{ net_cash_flow }}</p>
                ''',
                'is_active': True,
                'created_by': user
            }
        )
        
        if created:
            self.stdout.write(f'Created financial report template: {financial_template.name}')
        
        # Inventory Report Template
        inventory_template, created = ReportTemplate.objects.get_or_create(
            name='Inventory Report Template',
            defaults={
                'report_type': 'inventory',
                'description': 'Comprehensive inventory report including stock levels, movements, and valuation',
                'template_content': '''
                <h1>Inventory Report</h1>
                
                <h3>Inventory Summary</h3>
                <p>Total Products: {{ total_products }}</p>
                <p>Total Stock Value: ৳{{ total_stock_value }}</p>
                <p>Low Stock Items: {{ low_stock_items|length }}</p>
                
                <h3>Low Stock Items</h3>
                <ul>
                {% for item in low_stock_items %}
                    <li>{{ item.product.name }} - {{ item.quantity }} units</li>
                {% endfor %}
                </ul>
                
                <h3>Top Selling Products</h3>
                <ul>
                {% for product in top_selling %}
                    <li>{{ product.product__name }} - {{ product.total_sold }} units</li>
                {% endfor %}
                </ul>
                ''',
                'is_active': True,
                'created_by': user
            }
        )
        
        if created:
            self.stdout.write(f'Created inventory report template: {inventory_template.name}')
        
        # Sales Report Template
        sales_template, created = ReportTemplate.objects.get_or_create(
            name='Sales Report Template',
            defaults={
                'report_type': 'sales',
                'description': 'Comprehensive sales report including orders, invoices, and payments',
                'template_content': '''
                <h1>Sales Report</h1>
                <h2>Period: {{ start_date }} to {{ end_date }}</h2>
                
                <h3>Sales Summary</h3>
                <p>Total Orders: {{ total_orders }}</p>
                <p>Total Invoices: {{ total_invoices }}</p>
                <p>Total Sales: ৳{{ total_sales }}</p>
                <p>Total Payments: ৳{{ total_payments }}</p>
                
                <h3>Top Customers</h3>
                <ul>
                {% for customer in top_customers %}
                    <li>{{ customer.customer__name }} - ৳{{ customer.total_sales }}</li>
                {% endfor %}
                </ul>
                
                <h3>Top Products</h3>
                <ul>
                {% for product in sales_by_product %}
                    <li>{{ product.product__name }} - {{ product.total_quantity }} units</li>
                {% endfor %}
                </ul>
                ''',
                'is_active': True,
                'created_by': user
            }
        )
        
        if created:
            self.stdout.write(f'Created sales report template: {sales_template.name}')
        
        # Purchase Report Template
        purchase_template, created = ReportTemplate.objects.get_or_create(
            name='Purchase Report Template',
            defaults={
                'report_type': 'purchase',
                'description': 'Comprehensive purchase report including orders, invoices, and payments',
                'template_content': '''
                <h1>Purchase Report</h1>
                <h2>Period: {{ start_date }} to {{ end_date }}</h2>
                
                <h3>Purchase Summary</h3>
                <p>Total Orders: {{ total_orders }}</p>
                <p>Total Invoices: {{ total_invoices }}</p>
                <p>Total Purchases: ৳{{ total_purchases }}</p>
                <p>Total Payments: ৳{{ total_payments }}</p>
                
                <h3>Top Suppliers</h3>
                <ul>
                {% for supplier in top_suppliers %}
                    <li>{{ supplier.supplier__name }} - ৳{{ supplier.total_purchases }}</li>
                {% endfor %}
                </ul>
                
                <h3>Top Products</h3>
                <ul>
                {% for product in purchases_by_product %}
                    <li>{{ product.product__name }} - {{ product.total_quantity }} units</li>
                {% endfor %}
                </ul>
                ''',
                'is_active': True,
                'created_by': user
            }
        )
        
        if created:
            self.stdout.write(f'Created purchase report template: {purchase_template.name}')

    def create_report_schedules(self, user):
        """Create default report schedules"""
        
        # Monthly Financial Report
        monthly_financial, created = ReportSchedule.objects.get_or_create(
            name='Monthly Financial Report',
            defaults={
                'report_template': ReportTemplate.objects.get(name='Financial Report Template'),
                'frequency': 'monthly',
                'is_active': True,
                'next_run': timezone.now() + timedelta(days=30),
                'created_by': user
            }
        )
        
        if created:
            self.stdout.write(f'Created monthly financial report schedule: {monthly_financial.name}')
        
        # Weekly Inventory Report
        weekly_inventory, created = ReportSchedule.objects.get_or_create(
            name='Weekly Inventory Report',
            defaults={
                'report_template': ReportTemplate.objects.get(name='Inventory Report Template'),
                'frequency': 'weekly',
                'is_active': True,
                'next_run': timezone.now() + timedelta(days=7),
                'created_by': user
            }
        )
        
        if created:
            self.stdout.write(f'Created weekly inventory report schedule: {weekly_inventory.name}')
        
        # Daily Sales Report
        daily_sales, created = ReportSchedule.objects.get_or_create(
            name='Daily Sales Report',
            defaults={
                'report_template': ReportTemplate.objects.get(name='Sales Report Template'),
                'frequency': 'daily',
                'is_active': True,
                'next_run': timezone.now() + timedelta(days=1),
                'created_by': user
            }
        )
        
        if created:
            self.stdout.write(f'Created daily sales report schedule: {daily_sales.name}')
