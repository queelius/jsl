# Group By Examples

This page demonstrates how to use JSL's `group-by` function for data aggregation and analysis.

## Basic Grouping

### Group by Single Field

```jsl
(def sales [@
  {"product": "Laptop", "category": "Electronics", "amount": 1200}
  {"product": "Phone", "category": "Electronics", "amount": 800}
  {"product": "Shirt", "category": "Clothing", "amount": 50}
  {"product": "Jeans", "category": "Clothing", "amount": 80}
])

; Group by category
(group-by sales "@category")
; Result: [
;   [{"product": "Laptop", "category": "Electronics", "amount": 1200},
;    {"product": "Phone", "category": "Electronics", "amount": 800}],
;   [{"product": "Shirt", "category": "Clothing", "amount": 50},
;    {"product": "Jeans", "category": "Clothing", "amount": 80}]
; ]
```

### Group with Custom Key Function

```jsl
(def orders [@
  {"id": 1, "date": "2024-01-15", "total": 150}
  {"id": 2, "date": "2024-01-15", "total": 200}
  {"id": 3, "date": "2024-01-16", "total": 100}
])

; Group by date
(group-by orders "@date")

; Group by price range
(group-by orders 
  (lambda (order)
    (if (< (get order "@total") 150) "@low" "@high")))
```

## Aggregation After Grouping

### Calculate Group Statistics

```jsl
(def employees [@
  {"name": "Alice", "department": "Engineering", "salary": 120000}
  {"name": "Bob", "department": "Engineering", "salary": 110000}
  {"name": "Charlie", "department": "Sales", "salary": 90000}
  {"name": "Diana", "department": "Sales", "salary": 95000}
])

; Calculate average salary by department
(map
  (group-by employees "@department")
  (lambda (group)
    {"@department": (get (first group) "@department"),
     "@count": (length group),
     "@avgSalary": (/ (sum (pluck group "@salary")) (length group)),
     "@totalSalary": (sum (pluck group "@salary"))}))

; Result: [
;   {"department": "Engineering", "count": 2, "avgSalary": 115000, "totalSalary": 230000},
;   {"department": "Sales", "count": 2, "avgSalary": 92500, "totalSalary": 185000}
; ]
```

### Find Group Extremes

```jsl
(def products [@
  {"name": "Product A", "category": "tools", "price": 25, "rating": 4.5}
  {"name": "Product B", "category": "tools", "price": 35, "rating": 4.8}
  {"name": "Product C", "category": "books", "price": 15, "rating": 4.2}
  {"name": "Product D", "category": "books", "price": 20, "rating": 4.9}
])

; Find best rated product in each category
(map
  (group-by products "@category")
  (lambda (group)
    (let (best (reduce 
                 (lambda (acc item)
                   (if (> (get item "@rating") (get acc "@rating"))
                       item acc))
                 (first group)
                 (rest group)))
      {"@category": (get best "@category"),
       "@bestProduct": (get best "@name"),
       "@rating": (get best "@rating")})))
```

## Complex Grouping Scenarios

### Multi-Level Grouping

```jsl
(def transactions [@
  {"date": "2024-01", "type": "income", "category": "salary", "amount": 5000}
  {"date": "2024-01", "type": "expense", "category": "rent", "amount": 1500}
  {"date": "2024-01", "type": "expense", "category": "food", "amount": 500}
  {"date": "2024-02", "type": "income", "category": "salary", "amount": 5000}
  {"date": "2024-02", "type": "expense", "category": "rent", "amount": 1500}
])

; Group by month, then by type
(map
  (group-by transactions "@date")
  (lambda (month-group)
    {"@month": (get (first month-group) "@date"),
     "@types": (map
                 (group-by month-group "@type")
                 (lambda (type-group)
                   {"@type": (get (first type-group) "@type"),
                    "@total": (sum (pluck type-group "@amount")),
                    "@count": (length type-group)}))}))
```

### Grouping with Filtering

```jsl
(def orders [@
  {"customer": "Alice", "status": "completed", "total": 150}
  {"customer": "Bob", "status": "pending", "total": 200}
  {"customer": "Alice", "status": "completed", "total": 100}
  {"customer": "Charlie", "status": "cancelled", "total": 75}
  {"customer": "Bob", "status": "completed", "total": 300}
])

; Group completed orders by customer
(map
  (group-by 
    (where orders (= status "@completed"))
    "@customer")
  (lambda (group)
    {"@customer": (get (first group) "@customer"),
     "@orderCount": (length group),
     "@totalSpent": (sum (pluck group "@total"))}))
```

## Real-World Examples

### Sales Report

```jsl
(def sales-data [@
  {"date": "2024-01-15", "product": "Widget", "quantity": 5, "price": 20}
  {"date": "2024-01-15", "product": "Gadget", "quantity": 3, "price": 50}
  {"date": "2024-01-16", "product": "Widget", "quantity": 8, "price": 20}
  {"date": "2024-01-16", "product": "Gadget", "quantity": 2, "price": 50}
])

; Daily sales summary
(def daily-summary
  (map
    (group-by sales-data "@date")
    (lambda (day-sales)
      {"@date": (get (first day-sales) "@date"),
       "@totalRevenue": (sum 
                          (map day-sales 
                            (lambda (s) (* (get s "@quantity") 
                                          (get s "@price")))))
       "@totalUnits": (sum (pluck day-sales "@quantity")),
       "@uniqueProducts": (length (unique (pluck day-sales "@product")))})))

; Product performance
(def product-summary
  (map
    (group-by sales-data "@product")
    (lambda (product-sales)
      {"@product": (get (first product-sales) "@product"),
       "@totalQuantity": (sum (pluck product-sales "@quantity")),
       "@totalRevenue": (sum 
                          (map product-sales
                            (lambda (s) (* (get s "@quantity")
                                          (get s "@price")))))
       "@avgQuantityPerSale": (/ (sum (pluck product-sales "@quantity"))
                                 (length product-sales))})))
```

### User Activity Analysis

```jsl
(def activities [@
  {"user": "alice", "action": "login", "timestamp": "2024-01-15T09:00:00"}
  {"user": "bob", "action": "login", "timestamp": "2024-01-15T09:30:00"}
  {"user": "alice", "action": "purchase", "timestamp": "2024-01-15T10:00:00"}
  {"user": "alice", "action": "logout", "timestamp": "2024-01-15T11:00:00"}
  {"user": "bob", "action": "browse", "timestamp": "2024-01-15T10:00:00"}
])

; User activity summary
(map
  (group-by activities "@user")
  (lambda (user-activities)
    {"@user": (get (first user-activities) "@user"),
     "@totalActions": (length user-activities),
     "@actionTypes": (unique (pluck user-activities "@action")),
     "@hasPurchased": (any 
                        (map user-activities
                          (lambda (a) (= (get a "@action") "@purchase"))))}))
```

### Error Log Analysis

```jsl
(def error-logs [@
  {"service": "api", "level": "ERROR", "code": 500, "message": "Internal error"}
  {"service": "api", "level": "WARN", "code": 429, "message": "Rate limited"}
  {"service": "db", "level": "ERROR", "code": 1205, "message": "Deadlock"}
  {"service": "api", "level": "ERROR", "code": 500, "message": "Internal error"}
  {"service": "auth", "level": "WARN", "code": 401, "message": "Invalid token"}
])

; Error summary by service
(map
  (group-by 
    (where error-logs (= level "@ERROR"))
    "@service")
  (lambda (service-errors)
    {"@service": (get (first service-errors) "@service"),
     "@errorCount": (length service-errors),
     "@uniqueErrors": (length (unique (pluck service-errors "@code"))),
     "@errorCodes": (unique (pluck service-errors "@code"))}))
```

## Aggregation Functions

Common aggregation patterns with grouped data:

```jsl
; Sum
(sum (pluck group "@amount"))

; Average
(/ (sum (pluck group "@value")) (length group))

; Min/Max
(reduce min (first (pluck group "@price")) (rest (pluck group "@price")))
(reduce max (first (pluck group "@score")) (rest (pluck group "@score")))

; Count distinct
(length (unique (pluck group "@category")))

; Concatenate strings
(str-join ", " (pluck group "@name"))
```

## Performance Considerations

1. **Group Early**: Group before complex transformations when possible
2. **Use Indexes**: If available, group by indexed fields
3. **Aggregate Incrementally**: For large groups, use `reduce` instead of collecting all values
4. **Memory Usage**: Be aware that grouping creates sublists in memory

## Advanced Patterns

### Pivot Table

```jsl
(def pivot-table
  (lambda (data row-key col-key value-key)
    (let (rows (unique (pluck data row-key))
          cols (unique (pluck data col-key)))
      (map rows
        (lambda (row)
          (merge
            {row-key: row}
            (reduce
              (lambda (acc col)
                (assoc acc col
                  (sum (pluck
                    (where data
                      (and (= (get it row-key) row)
                           (= (get it col-key) col)))
                    value-key))))
              {}
              cols)))))))

; Example: Sales by product and month
(pivot-table sales-data "@product" "@month" "@revenue")
```

## See Also

- [Query Operations](../language/query-operations.md) - Filtering with `where`
- [Transform Operations](../language/transform-operations.md) - Data transformation
- [Prelude Functions](../language/prelude.md) - Built-in aggregation functions