# Query Operations

JSL provides powerful declarative operations for querying and filtering data, inspired by [dotsuite](https://github.com/queelius/dotsuite)'s pedagogical approach to JSON manipulation.

## The `where` Special Form

The `where` is a special form (not a function) that provides SQL-like declarative filtering. As a special form, it has special evaluation semantics that automatically bind item fields to the environment before evaluating the condition.

### Basic Syntax

```jsl
(where collection condition)
```

The condition is evaluated with each item's fields automatically bound to the environment.

### Examples

#### Simple Filtering

```jsl
; Filter users by role
(where users (= role "admin"))

; Filter products by price
(where products (> price 100))
```

#### Complex Conditions

```jsl
; AND conditions
(where users 
  (and (= role "admin") 
       active))

; OR conditions  
(where products
  (or (= category "electronics")
      (< price 50)))

; Nested conditions
(where orders
  (and (>= total 100)
       (or (= status "pending")
           (= status "processing"))))
```

### Field Binding

The `where` special form automatically extends the environment with each item's fields. For objects, all key-value pairs become available as variables. For non-objects, the item is bound to `it`:


```jsl
(def users [@
  {"name": "Alice", "age": 30, "role": "admin"}
  {"name": "Bob", "age": 25, "role": "user"}
])

; 'role' and 'age' are automatically bound from each user
(where users (and (= role "admin") (> age 25)))
; Returns: [{"name": "Alice", "age": 30, "role": "admin"}]
```

### String Literals vs Field References

- Field names are symbols that get looked up: `role`, `age`, `name`
- String literals use the @ prefix: `"@admin"`, `"@user"`

```jsl
(where users (= role "@admin"))  ; role field equals string "admin"
(where users (= "@role" role))   ; string "role" equals role field (unusual)
```

## Query Composition

Query operations compose naturally with other JSL operations:

### Filter then Transform

```jsl
(transform
  (where products (> price 50))
  (pick "@name" "@price"))
```

### Filter then Pluck

```jsl
(pluck
  (where users (= role "@admin"))
  "@email")
```

### Multiple Filters

```jsl
(where
  (where products (= category "@electronics"))
  (> price 100))
```

## Implementation Details

As a special form, `where` is implemented directly in the evaluator (`_eval_where` in `core.py`), not as a prelude function. This allows it to:
- Control evaluation order
- Automatically bind fields without explicit lambda expressions
- Integrate seamlessly with the JSL evaluation model
- Work identically in both recursive and stack evaluators

## Performance Considerations

The `where` operator:
- Uses the standard JSL evaluator for conditions
- Extends the environment once per item
- Short-circuits on false conditions
- Maintains original collection order

## Comparison with Traditional Approaches

### Traditional Lambda Approach

```jsl
(filter 
  (lambda (user) 
    (and (= (get user "@role") "@admin")
         (get user "@active")))
  users)
```

### Declarative Where Approach

```jsl
(where users (and (= role "@admin") active))
```

The declarative approach is:
- More concise and readable
- Automatically handles field binding
- Consistent with SQL-like query languages
- Easier to compose with other operations

## Integration with Transform

`where` and `transform` work together for powerful data pipelines:

```jsl
; Get names of active admins
(pluck
  (where users (and (= role "@admin") active))
  "@name")

; Add discount to expensive products
(transform
  (where products (> price 100))
  (assign "@discounted" (* price 0.9)))
```

## See Also

- [Transform Operations](transform-operations.md) - Data transformation operations
- [Path Navigation](path-navigation.md) - Deep JSON path access
- [Prelude Functions](prelude.md) - Built-in collection functions