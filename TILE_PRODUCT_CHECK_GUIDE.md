# How to Check if a Product is a Tile Type

## Overview
The system identifies tile products by checking the product's **category name**. If the category is "Tiles", the product is treated as a tile and special calculations are performed.

## The Check Logic

### In Python/Django Code:

```python
# Check if product is a tile
if product.category and product.category.name.lower() == 'tiles':
    # This is a tile product
    # Perform tile-specific calculations
    pass
```

### Step-by-Step Explanation:

1. **Check if category exists**: `product.category`
   - Products can have no category (null), so we check first
   
2. **Get category name**: `product.category.name`
   - Gets the name of the category (e.g., "Tiles", "Steel Rod", "Cement")
   
3. **Case-insensitive comparison**: `.lower() == 'tiles'`
   - Converts to lowercase for comparison
   - Matches: "Tiles", "TILES", "tiles", "TiLeS" - all work

## Required Fields for Tile Products

For a tile product to work correctly, it needs:

1. **Category**: Must be set to "Tiles"
2. **pcs_per_carton**: Number of pieces per carton (e.g., 10)
3. **sqft_per_pcs**: Square feet per piece (e.g., 4.00 for 2x2 tiles)

## Example: How It Works in Invoice

```python
# From sales/views.py - sales_order_invoice function

for item in order.items.all():
    tile_info = None
    
    # STEP 1: Check if category is "Tiles"
    if item.product.category and item.product.category.name.lower() == 'tiles':
        
        # STEP 2: Get tile-specific fields
        pcs_per_carton = item.product.pcs_per_carton or 0
        sqft_per_pcs = item.product.sqft_per_pcs or Decimal('0')
        
        # STEP 3: Only calculate if both fields are set
        if sqft_per_pcs > 0 and pcs_per_carton > 0:
            # Calculate tile information
            # ... calculations here
```

## How to Verify if a Product is a Tile

### Method 1: Check in Django Shell

```python
python manage.py shell

from stock.models import Product

# Get a product
product = Product.objects.get(name="Ceramic Floor Tile 2x2")

# Check if it's a tile
if product.category:
    print(f"Category: {product.category.name}")
    print(f"Is Tile: {product.category.name.lower() == 'tiles'}")
    print(f"Pieces per Carton: {product.pcs_per_carton}")
    print(f"Sqft per Piece: {product.sqft_per_pcs}")
else:
    print("No category assigned")
```

### Method 2: Check in Admin/UI

1. Go to Products list
2. Open a product
3. Check the **Category** field
4. If it says "Tiles", it's a tile product
5. Check **Pieces per Carton** and **Square Feet per Piece** fields

### Method 3: Check in Code

```python
def is_tile_product(product):
    """Helper function to check if product is a tile"""
    if not product.category:
        return False
    return product.category.name.lower() == 'tiles'

# Usage
if is_tile_product(product):
    print("This is a tile product")
```

## Example Products

### ✅ Tile Product (Will Show Calculation):
- **Name**: Ceramic Floor Tile 2x2
- **Category**: Tiles
- **Pieces per Carton**: 10
- **Square Feet per Piece**: 4.00
- **Unit Type**: Square Feet (sqft)

**Result in Invoice**: 
```
Ceramic Floor Tile 2x2 - 500 sqft (12 carton 5 pieces)
```

### ❌ Non-Tile Product (Normal Display):
- **Name**: Steel Rod 20mm
- **Category**: Steel Rod
- **Pieces per Carton**: 0
- **Square Feet per Piece**: 0.00
- **Unit Type**: Ton

**Result in Invoice**: 
```
Steel Rod 20mm
```

## Calculation Logic

When a tile product is found:

1. **If quantity is in sqft** (unit_type.code == 'sqft'):
   - `total_sqft = quantity`
   - `total_pieces = total_sqft / sqft_per_pcs`
   
2. **If quantity is in pieces** (other unit types):
   - `total_pieces = quantity`
   - `total_sqft = total_pieces * sqft_per_pcs`

3. **Calculate cartons and remaining pieces**:
   - `cartons = total_pieces // pcs_per_carton` (integer division)
   - `remaining_pieces = total_pieces % pcs_per_carton` (remainder)

## Example Calculation

**Product**: Ceramic Floor Tile 2x2
- **sqft_per_pcs**: 4.00 (2x2 feet = 4 sqft)
- **pcs_per_carton**: 10
- **Quantity ordered**: 500 sqft

**Calculation**:
1. `total_sqft = 500`
2. `total_pieces = 500 / 4 = 125 pieces`
3. `cartons = 125 // 10 = 12 cartons`
4. `remaining_pieces = 125 % 10 = 5 pieces`

**Display**: `Ceramic Floor Tile 2x2 - 500 sqft (12 carton 5 pieces)`

## Common Issues

### Issue 1: Product not showing tile calculation
**Check**:
- Is category set to "Tiles"? (case-insensitive)
- Are `pcs_per_carton` and `sqft_per_pcs` both > 0?

### Issue 2: Wrong calculation
**Check**:
- Is the unit type correct? (sqft vs pieces)
- Are the `pcs_per_carton` and `sqft_per_pcs` values correct?

### Issue 3: Category name mismatch
**Solution**: Make sure the category name is exactly "Tiles" (case doesn't matter due to `.lower()`)

## Quick Test Script

```python
# test_tile_check.py
from stock.models import Product

# Get all tile products
tile_products = Product.objects.filter(
    category__name__iexact='tiles'
)

print(f"Found {tile_products.count()} tile products:")
for product in tile_products:
    print(f"- {product.name}")
    print(f"  Category: {product.category.name}")
    print(f"  Pcs/Carton: {product.pcs_per_carton}")
    print(f"  Sqft/Pcs: {product.sqft_per_pcs}")
    print()
```

## Summary

**To check if a product is a tile:**
```python
product.category.name.lower() == 'tiles'
```

**Key Points:**
- ✅ Case-insensitive check (Tiles, TILES, tiles all work)
- ✅ Must have category assigned
- ✅ Needs `pcs_per_carton` > 0 and `sqft_per_pcs` > 0 for calculations
- ✅ Works automatically in invoice generation


