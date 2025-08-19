# Query and Transform Examples

This page demonstrates practical examples of using JSL's query and transform operations for data manipulation.

## Basic Filtering with `where`

### Filter by Single Field

```jsl
(def users [@
  {"name": "Alice", "age": 30, "role": "admin"}
  {"name": "Bob", "age": 25, "role": "user"}
  {"name": "Charlie", "age": 35, "role": "admin"}
])

; Get all admins
(where users (= role "@admin"))
; Result: [{"name": "Alice", ...}, {"name": "Charlie", ...}]

; Get users over 30
(where users (> age 30))
; Result: [{"name": "Charlie", "age": 35, ...}]
```

### Complex Conditions

```jsl
; Combine conditions with AND
(where users (and (= role "@admin") (>= age 30)))

; Combine with OR
(where users (or (= role "@admin") (< age 30)))

; Nested conditions
(where users 
  (and (>= age 25)
       (or (= role "@admin") 
           (= role "@moderator"))))
```

## Data Transformation with `transform`

### Reshaping Objects

```jsl
; Pick specific fields
(transform users (pick "@name" "@email"))

; Add computed fields
(transform products 
  (assign "@discount" (* price 0.1)))

; Remove sensitive data
(transform users (omit "@password" "@ssn"))
```

### Working with Collections

```jsl
(def orders [@
  {"id": 1, "items": 3, "price": 25.00}
  {"id": 2, "items": 1, "price": 15.00}
  {"id": 3, "items": 5, "price": 45.00}
])

; Add total to each order
(transform orders 
  (assign "@total" (* items price)))

; Add shipping cost based on total
(transform orders
  (assign "@shipping" 
    (if (> (* items price) 30) 0 5)))
```

## Combining Query and Transform

### Filter then Transform Pipeline

```jsl
(def products [@
  {"name": "Laptop", "price": 999, "category": "electronics"}
  {"name": "Shirt", "price": 29, "category": "clothing"}
  {"name": "Phone", "price": 599, "category": "electronics"}
  {"name": "Jeans", "price": 59, "category": "clothing"}
])

; Get names and prices of expensive electronics
(transform
  (where products 
    (and (= category "@electronics") 
         (> price 500)))
  (pick "@name" "@price"))
; Result: [{"name": "Laptop", "price": 999}, 
;          {"name": "Phone", "price": 599}]
```

### Multi-Step Pipeline

```jsl
; 1. Filter active users
; 2. Add full name field
; 3. Pick relevant fields
; 4. Sort by name

(def pipeline
  (lambda (users)
    (sort-by
      (transform
        (transform
          (where users (= active true))
          (assign "@fullName" 
            (str-concat firstName " " lastName)))
        (pick "@fullName" "@email" "@role"))
      "@fullName")))

(pipeline all-users)
```

## Real-World Examples

### User Management System

```jsl
; Get admin emails for notifications
(pluck
  (where users (and (= role "@admin") (= active true)))
  "@email")

; Prepare user data for API response
(transform users
  (do
    (pick "@id" "@username" "@email" "@created")
    (assign "@type" "@user")
    (omit "@internal_id")))
```

### E-Commerce Product Catalog

```jsl
(def products [@
  {"sku": "LAP001", "name": "Laptop Pro", "price": 1299, 
   "stock": 5, "category": "computers"}
  {"sku": "PHN001", "name": "SmartPhone X", "price": 899,
   "stock": 0, "category": "phones"}
  {"sku": "TAB001", "name": "Tablet Plus", "price": 599,
   "stock": 12, "category": "tablets"}
])

; Get available products with discount
(transform
  (where products (> stock 0))
  (do
    (assign "@available" true)
    (assign "@salePrice" (* price 0.9))
    (pick "@sku" "@name" "@price" "@salePrice" "@available")))

; Group products by category with count
(map
  (group-by products "@category")
  (lambda (group)
    {"@category": (get (first group) "@category"),
     "@count": (length group),
     "@totalValue": (sum (pluck group "@price"))}))
```

### Log Analysis

```jsl
(def logs [@
  {"timestamp": "2024-01-15T10:00:00", "level": "ERROR", 
   "service": "auth", "message": "Login failed"}
  {"timestamp": "2024-01-15T10:01:00", "level": "INFO",
   "service": "api", "message": "Request processed"}
  {"timestamp": "2024-01-15T10:02:00", "level": "ERROR",
   "service": "db", "message": "Connection timeout"}
])

; Get error logs from specific services
(where logs 
  (and (= level "@ERROR")
       (or (= service "@auth") 
           (= service "@db"))))

; Create error summary
(transform
  (where logs (= level "@ERROR"))
  (pick "@timestamp" "@service" "@message"))
```

### Data Migration

```jsl
; Transform old format to new format
(def migrate-user
  (lambda (old-user)
    (transform old-user
      (do
        ; Rename fields
        (rename "@username" "@login")
        (rename "@full_name" "@displayName")
        ; Add new required fields
        (assign "@version" 2)
        (assign "@migrated" true)
        (assign "@migratedAt" (now))
        ; Remove deprecated fields
        (omit "@legacy_id" "@old_status")))))

; Migrate all users
(map users migrate-user)
```

## Performance Tips

1. **Filter Early**: Apply `where` before `transform` to reduce data size
2. **Combine Operations**: Use `do` to batch multiple transformations
3. **Use Specific Picks**: `pick` is faster than `omit` for selecting few fields
4. **Leverage Indexes**: When available, filter on indexed fields first

## Common Patterns

### Pagination

```jsl
(def paginate
  (lambda (data page size)
    (let (start (* page size)
          end (+ start size))
      (slice data start end))))

; Get page 2 with 10 items per page
(paginate 
  (where products (= category "@electronics"))
  2 10)
```

### Search

```jsl
(def search-products
  (lambda (products query)
    (where products
      (or (str-contains (str-lower name) (str-lower query))
          (str-contains (str-lower description) (str-lower query))))))

(search-products all-products "@laptop")
```

### Validation

```jsl
(def valid-users
  (where users
    (and (not (null email))
         (str-matches email "@^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$")
         (>= age 18)
         (in role ["@admin" "@user" "@guest"]))))
```

## See Also

- [Query Operations](../language/query-operations.md) - Detailed `where` documentation
- [Transform Operations](../language/transform-operations.md) - Detailed `transform` documentation
- [Path Navigation](../language/path-navigation.md) - Deep JSON access
- [Group By Examples](group-by.md) - Grouping and aggregation