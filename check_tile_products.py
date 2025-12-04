#!/usr/bin/env python
"""
Quick script to check tile products
Run: python manage.py shell < check_tile_products.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from stock.models import Product, ProductCategory

print("=" * 60)
print("Checking Tile Products")
print("=" * 60)

# Find Tiles category
tiles_category = ProductCategory.objects.filter(name__iexact='tiles').first()

if tiles_category:
    print(f"✓ Found category: '{tiles_category.name}'")
    print()
    
    # Get all tile products
    tile_products = Product.objects.filter(category=tiles_category)
    print(f"Total tile products: {tile_products.count()}")
    print()
    
    if tile_products.exists():
        print("Tile Products:")
        print("-" * 60)
        for product in tile_products:
            print(f"Product: {product.name}")
            print(f"  Category: {product.category.name}")
            print(f"  Pieces per Carton: {product.pcs_per_carton}")
            print(f"  Square Feet per Piece: {product.sqft_per_pcs}")
            
            # Check if it will show calculation
            if product.pcs_per_carton > 0 and product.sqft_per_pcs > 0:
                print(f"  ✓ Will show tile calculation in invoice")
            else:
                print(f"  ⚠ Missing tile fields (won't calculate)")
            print()
    else:
        print("No products found in Tiles category")
else:
    print("✗ Tiles category not found!")
    print("\nAvailable categories:")
    for cat in ProductCategory.objects.all():
        print(f"  - {cat.name}")

print("=" * 60)
print("\nHow to check if a product is a tile:")
print("=" * 60)
print("""
In Python code:
    if product.category and product.category.name.lower() == 'tiles':
        # This is a tile product
        
In Django Query:
    tile_products = Product.objects.filter(category__name__iexact='tiles')
    
Manual check:
    1. Product must have category assigned
    2. Category name must be 'Tiles' (case-insensitive)
    3. For calculations: pcs_per_carton > 0 AND sqft_per_pcs > 0
""")


