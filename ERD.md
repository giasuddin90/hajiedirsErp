# Entity Relationship Diagram (ERD)
## Django ERP System - Complete Database Schema

> **Note**: This ERD reflects the current system status with real-time inventory calculation. No Stock or StockAlert models exist.

```mermaid
erDiagram
    %% ============================================
    %% USER MANAGEMENT (Core)
    %% ============================================
    User {
        int id PK
        string username
        string email
        string first_name
        string last_name
    }

    %% ============================================
    %% CUSTOMER MODULE
    %% ============================================
    Customer ||--o{ CustomerLedger : "1 to Many\n(has transactions)"
    Customer ||--o{ CustomerCommitment : "1 to Many\n(has commitments)"
    Customer ||--o{ SalesOrder : "1 to Many\n(places orders)"
    User ||--o{ CustomerLedger : "1 to Many\n(creates ledger)"
    
    Customer {
        int id PK
        string name
        string customer_type
        string contact_person
        string phone
        text address
        decimal credit_limit
        decimal opening_balance
        decimal current_balance
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    CustomerLedger {
        int id PK
        int customer_id FK
        int created_by_id FK
        string transaction_type
        decimal amount
        text description
        string reference
        datetime transaction_date
        string payment_method
        datetime created_at
    }

    CustomerCommitment {
        int id PK
        int customer_id FK
        date commitment_date
        decimal amount
        text description
        boolean is_reminded
        boolean is_fulfilled
        datetime created_at
    }

    %% ============================================
    %% SUPPLIER MODULE
    %% ============================================
    Supplier ||--o{ SupplierLedger : "1 to Many\n(has transactions)"
    Supplier ||--o{ PurchaseOrder : "1 to Many\n(supplies orders)"
    User ||--o{ SupplierLedger : "1 to Many\n(creates ledger)"

    Supplier {
        int id PK
        string name
        string contact_person
        string phone
        text address
        string city
        decimal opening_balance
        decimal current_balance
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    SupplierLedger {
        int id PK
        int supplier_id FK
        int created_by_id FK
        string transaction_type
        decimal amount
        text description
        string reference
        datetime transaction_date
        string payment_method
        datetime created_at
    }

    %% ============================================
    %% STOCK MODULE (Real-Time Inventory)
    %% ============================================
    ProductCategory ||--o{ Product : "1 to Many\n(categorizes)"
    ProductBrand ||--o{ Product : "1 to Many\n(brands)"
    UnitType ||--o{ Product : "1 to Many\n(measures)"
    Product ||--o{ SalesOrderItem : "1 to Many\n(sold in orders)"
    Product ||--o{ PurchaseOrderItem : "1 to Many\n(purchased in orders)"

    ProductCategory {
        int id PK
        string name UK
        text description
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    ProductBrand {
        int id PK
        string name UK
        text description
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    UnitType {
        int id PK
        string code UK
        string name
        text description
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    Product {
        int id PK
        int category_id FK "nullable"
        int brand_id FK "nullable"
        int unit_type_id FK
        string name
        text description
        decimal cost_price
        decimal selling_price
        decimal min_stock_level
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    %% ============================================
    %% SALES MODULE
    %% ============================================
    SalesOrder ||--o{ SalesOrderItem : "1 to Many\n(contains items)"
    SalesOrder }o--|| Customer : "Many to 1\n(belongs to)"
    SalesOrderItem }o--|| Product : "Many to 1\n(references)"
    User ||--o{ SalesOrder : "1 to Many\n(creates order)"

    SalesOrder {
        int id PK
        int customer_id FK "nullable"
        int created_by_id FK "nullable"
        string order_number UK
        string sales_type
        string customer_name
        date order_date
        date delivery_date "nullable"
        string status
        decimal total_amount
        text notes
        datetime created_at
        datetime updated_at
    }

    SalesOrderItem {
        int id PK
        int sales_order_id FK
        int product_id FK
        decimal quantity
        decimal unit_price
        decimal total_price
    }

    %% ============================================
    %% PURCHASE MODULE
    %% ============================================
    PurchaseOrder ||--o{ PurchaseOrderItem : "1 to Many\n(contains items)"
    PurchaseOrder }o--|| Supplier : "Many to 1\n(from supplier)"
    PurchaseOrderItem }o--|| Product : "Many to 1\n(references)"
    User ||--o{ PurchaseOrder : "1 to Many\n(creates order)"

    PurchaseOrder {
        int id PK
        int supplier_id FK
        int created_by_id FK "nullable"
        string order_number UK
        date order_date
        date expected_date
        string status
        string invoice_id
        decimal total_amount
        text notes
        datetime created_at
        datetime updated_at
    }

    PurchaseOrderItem {
        int id PK
        int purchase_order_id FK
        int product_id FK
        decimal quantity
        decimal unit_price
        decimal total_price
    }

    %% ============================================
    %% EXPENSE MODULE
    %% ============================================
    ExpenseCategory ||--o{ Expense : "1 to Many\n(categorizes)"
    Expense }o--|| ExpenseCategory : "Many to 1\n(belongs to)"
    User ||--o{ Expense : "1 to Many\n(creates expense)"

    ExpenseCategory {
        int id PK
        string name UK
        text description
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    Expense {
        int id PK
        int category_id FK "nullable"
        int created_by_id FK "nullable"
        string title
        text description
        decimal amount
        string payment_method
        string status
        date expense_date
        date paid_date "nullable"
        string vendor_name
        string receipt_number
        text notes
        datetime created_at
        datetime updated_at
    }
```

## Relationship Diagram with Arrows

The Mermaid diagram above shows all relationships with arrows indicating:
- **`||--o{`**: One-to-Many (Parent has many children)
- **`}o--||`**: Many-to-One (Children belong to one parent)
- **Arrow direction**: Points from parent to child

### Visual Relationship Flow:

```
USER (Creator)
  ├─→ CustomerLedger (creates)
  ├─→ SupplierLedger (creates)
  ├─→ SalesOrder (creates)
  ├─→ PurchaseOrder (creates)
  └─→ Expense (creates)

CUSTOMER (Master)
  ├─→ CustomerLedger (has transactions)
  ├─→ CustomerCommitment (has commitments)
  └─→ SalesOrder (places orders)

SUPPLIER (Master)
  ├─→ SupplierLedger (has transactions)
  └─→ PurchaseOrder (supplies orders)

PRODUCT (Master)
  ←─ ProductCategory (categorizes)
  ←─ ProductBrand (brands)
  ←─ UnitType (measures)
  ├─→ SalesOrderItem (sold in orders)
  └─→ PurchaseOrderItem (purchased in orders)

SALESORDER (Header)
  ←─ Customer (belongs to)
  ├─→ SalesOrderItem (contains items)
  └─ SalesOrderItem → Product (references)

PURCHASEORDER (Header)
  ←─ Supplier (from supplier)
  ├─→ PurchaseOrderItem (contains items)
  └─ PurchaseOrderItem → Product (references)

EXPENSE
  ←─ ExpenseCategory (belongs to)
  ←─ User (created by)
```

## Key Relationships

### Customer Module
- **Customer** → **CustomerLedger**: One-to-Many (Customer has multiple ledger entries)
- **Customer** → **CustomerCommitment**: One-to-Many (Customer has multiple commitments)
- **Customer** → **SalesOrder**: One-to-Many (Customer places multiple orders)
- **CustomerLedger** → **User**: Many-to-One (Ledger entries created by users)

### Supplier Module
- **Supplier** → **SupplierLedger**: One-to-Many (Supplier has multiple ledger entries)
- **Supplier** → **PurchaseOrder**: One-to-Many (Supplier fulfills multiple orders)
- **SupplierLedger** → **User**: Many-to-One (Ledger entries created by users)

### Stock Module (Real-Time Inventory)
- **ProductCategory** → **Product**: One-to-Many (Category has multiple products)
- **ProductBrand** → **Product**: One-to-Many (Brand has multiple products)
- **UnitType** → **Product**: One-to-Many (Unit type used by multiple products)
- **Product** → **SalesOrderItem**: One-to-Many (Product sold in multiple orders)
- **Product** → **PurchaseOrderItem**: One-to-Many (Product purchased in multiple orders)

**⚠️ Important**: No `Stock` model exists. Inventory is calculated in real-time:
```
Current Stock = SUM(PurchaseOrderItem.quantity WHERE PurchaseOrder.status = 'goods-received')
               - SUM(SalesOrderItem.quantity WHERE SalesOrder.status = 'delivered')
```

### Sales Module
- **SalesOrder** → **SalesOrderItem**: One-to-Many (Order contains multiple items)
- **SalesOrder** → **Customer**: Many-to-One (Order belongs to a customer, nullable for instant sales)
- **SalesOrderItem** → **Product**: Many-to-One (Item references a product)
- **SalesOrder** → **User**: Many-to-One (Order created by a user)

### Purchase Module
- **PurchaseOrder** → **PurchaseOrderItem**: One-to-Many (Order contains multiple items)
- **PurchaseOrder** → **Supplier**: Many-to-One (Order from a supplier)
- **PurchaseOrderItem** → **Product**: Many-to-One (Item references a product)
- **PurchaseOrder** → **User**: Many-to-One (Order created by a user)

### Expense Module
- **ExpenseCategory** → **Expense**: One-to-Many (Category has multiple expenses)
- **Expense** → **User**: Many-to-One (Expense created by a user)

## Inventory Calculation Flow

### When Purchase Order is Received (`status = 'goods-received'`)
```
PurchaseOrder.status = 'goods-received'
→ Inventory Increases
→ Product.get_realtime_quantity() includes this purchase
```

### When Sales Order is Delivered (`status = 'delivered'`)
```
SalesOrder.status = 'delivered'
→ Inventory Decreases
→ Product.get_realtime_quantity() excludes this sale
```

### Stock Alert Calculation
- Alerts are calculated dynamically using `get_low_stock_products()` function
- Condition: `current_quantity ≤ min_stock_level AND min_stock_level > 0`
- No database storage - computed in real-time

## Removed Models
The following models were removed in favor of real-time calculation:
- ❌ `Stock` - Removed (inventory calculated from transactions)
- ❌ `StockAlert` - Removed (alerts calculated dynamically)
- ❌ `StockAdjustment` - Removed (use purchase/sales orders for adjustments)
- ❌ `StockMovement` - Never existed in current system

## Indexes

### Product
- `name`, `category`, `brand`, `is_active`, `selling_price`

### Customer
- `name`, `customer_type`, `is_active`, `current_balance`

### SalesOrder
- `order_date`, `status`, `customer`, `sales_type`, `created_at`

### SalesOrderItem
- `sales_order`, `product`

### PurchaseOrder
- Standard Django indexes

## Foreign Key Constraints
- **CASCADE**: Deleting a parent deletes children (e.g., Customer → CustomerLedger)
- **SET_NULL**: Deleting a parent sets FK to NULL (e.g., ProductCategory → Product)
- **PROTECT**: Prevents deletion if children exist (e.g., UnitType → Product)

