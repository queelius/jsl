# Transform Operations

JSL provides powerful declarative operations for transforming and reshaping data structures.

## The `transform` Special Form

The `transform` is a special form (not a function) that applies transformation operations to data. As a special form, it automatically binds item fields to the environment, allowing direct field references in transformation expressions.

### Basic Syntax

```jsl
(transform data operation)
```

The operation can be one of several transformation functions that reshape the data.

## Transformation Operations

The transform operations are functions in the prelude that return operation descriptors. These descriptors are then interpreted by the `transform` special form.

### `assign` - Add or Update Fields

Returns an operation descriptor that adds new fields or updates existing ones:

```jsl
; Add a single field
(transform user (assign "@verified" true))

; Add computed field
(transform product (assign "@discounted" (* price 0.9)))

; Update existing field
(transform user (assign "@age" (+ age 1)))
```

### `pick` - Select Specific Fields

Creates new objects with only specified fields:

```jsl
; Pick specific fields
(transform user (pick "@name" "@email"))

; From collection
(transform users (pick "@id" "@name" "@role"))
```

### `omit` - Remove Fields

Creates new objects without specified fields:

```jsl
; Remove sensitive fields
(transform user (omit "@password" "@ssn"))

; Remove multiple fields
(transform response (omit "@internal_id" "@debug_info"))
```

### `rename` - Rename Fields

Renames fields in objects:

```jsl
; Rename single field
(transform user (rename "@username" "@login"))

; Multiple renames
(transform data (rename {"@old_name": "@new_name", "@id": "@identifier"}))
```

### `update` - Update Specific Fields

Updates fields with computed values:

```jsl
; Update with function
(transform product (update "@price" (lambda (p) (* p 1.1))))

; Update multiple fields
(transform user 
  (update {"@age": (lambda (a) (+ a 1)), 
           "@score": (lambda (s) (* s 2))}))
```

## Field Binding

Within transform operations, fields are automatically bound:

```jsl
(def product {"name": "Widget", "price": 100, "tax_rate": 0.08})

; Fields 'price' and 'tax_rate' are automatically available
(transform product 
  (assign "@total" (* price (+ 1 tax_rate))))
; Returns: {"name": "Widget", "price": 100, "tax_rate": 0.08, "total": 108}
```

## Working with Collections

Transform operations work on both single objects and collections:

```jsl
(def products [@
  {"name": "A", "price": 100}
  {"name": "B", "price": 200}
])

; Applied to each item
(transform products (assign "@on_sale" true))
; Returns: [{"name": "A", "price": 100, "on_sale": true},
;           {"name": "B", "price": 200, "on_sale": true}]
```

## Composition Patterns

### Sequential Transformations

```jsl
(transform
  (transform user (pick "@name" "@email" "@age"))
  (assign "@adult" (>= age 18)))
```

### Filter and Transform

```jsl
(transform
  (where products (> price 50))
  (assign "@premium" true))
```

### Transform and Aggregate

```jsl
(sum
  (pluck
    (transform orders (assign "@total" (* quantity price)))
    "@total"))
```

## Advanced Examples

### Data Normalization

```jsl
; Normalize user data
(transform users
  (do
    (pick "@id" "@username" "@email")
    (rename "@username" "@name")
    (assign "@created_at" (now))))
```

### Computed Fields

```jsl
; Add multiple computed fields
(def order {"items": 5, "price_per_item": 20, "tax_rate": 0.08})

(transform order
  (do
    (assign "@subtotal" (* items price_per_item))
    (assign "@tax" (* subtotal tax_rate))
    (assign "@total" (+ subtotal tax))))
```

### Nested Transformations

```jsl
; Transform nested structures
(transform user
  (update "@address" 
    (lambda (addr) 
      (transform addr (pick "@city" "@country")))))
```

## String Literals vs Field References

- Field references (symbols): `price`, `name`, `active`
- String literals (@ prefix): `"@price"`, `"@name"`

```jsl
; Assign literal string "pending" to status field
(transform order (assign "@status" "@pending"))

; Assign value of status variable to new_status field  
(transform order (assign "@new_status" status))
```

## Implementation Details

The `transform` special form is implemented in `_eval_transform` in `core.py`. The transformation operators (`pick`, `omit`, `assign`, etc.) are prelude functions that return operation descriptors like `["pick", "@field1", "@field2"]`. The special form then:
1. Evaluates the data expression
2. For each operation, evaluates it with item fields in scope
3. Interprets the operation descriptor to perform the transformation
4. Returns the transformed data

This design separates the operation definition (in prelude) from the execution logic (in the evaluator).

## Performance Considerations

Transform operations:
- Create new objects (immutable)
- Extend environment once per transformation
- Process collections item by item
- Can be optimized by the compiler

## Comparison with Manual Approach

### Manual Construction

```jsl
(lambda (user)
  {"@name": (get user "@name"),
   "@email": (get user "@email"),
   "@verified": true})
```

### Transform Approach

```jsl
(transform user 
  (do
    (pick "@name" "@email")
    (assign "@verified" true)))
```

The transform approach is:
- More declarative and readable
- Automatically handles field access
- Composable with other operations
- Less error-prone

## See Also

- [Query Operations](query-operations.md) - Filtering with `where`
- [Path Navigation](path-navigation.md) - Deep JSON path access
- [Group By](../examples/group-by.md) - Grouping and aggregation