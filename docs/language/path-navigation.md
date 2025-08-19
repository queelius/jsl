# Path Navigation

JSL provides powerful path navigation operations for accessing and manipulating deeply nested JSON structures. These operations are inspired by [dotsuite](https://github.com/queelius/dotsuite)'s dotpath approach.

## Overview

Path navigation allows you to access nested values using simple path strings instead of chaining multiple `get` operations.

## Path Navigation Functions

### `get-path` - Navigate to a Value

Retrieves a value at a deep path:

```jsl
(def user {
  "@name": "@John",
  "@address": {
    "@city": "@Boston",
    "@zip": "@02134"
  }
})

; Instead of nested gets:
(get (get user "@address") "@city")  ; "@Boston"

; Use path navigation:
(get-path user "@address.city")      ; "@Boston"
```

### `set-path` - Set a Value at Path

Creates a new object with a value set at the specified path:

```jsl
; Set a nested value
(set-path user "@address.country" "@USA")

; Creates intermediate objects if needed
(set-path {} "@user.profile.name" "@Alice")
; Returns: {"user": {"profile": {"name": "Alice"}}}
```

### `has-path` - Check Path Existence

Tests whether a path exists in an object:

```jsl
(has-path user "@address.city")     ; true
(has-path user "@address.country")  ; false
(has-path user "@phone.mobile")     ; false
```

### `update-path` - Update Value at Path

Updates a value at a path using a function:

```jsl
; Increment a nested counter
(update-path stats "@views.total" inc)

; Transform a nested value
(update-path user "@address.zip" 
  (lambda (z) (str-concat z "-0000")))
```

### `get-safe` - Safe Navigation

Returns a default value if the path doesn't exist:

```jsl
; Returns null if path missing
(get-safe user "@phone.mobile")  ; null

; With custom default
(get-safe user "@phone.mobile" "@unknown")  ; "@unknown"
```

## Path Syntax

### Basic Paths

Paths use dot notation to navigate through objects:

```jsl
"@field"           ; Top-level field
"@field.subfield"  ; Nested field
"@a.b.c.d"        ; Deep nesting
```

### Array Indexing

Access array elements by index:

```jsl
(def data {
  "@items": [@
    {"@id": 1, "@name": "@First"}
    {"@id": 2, "@name": "@Second"}
  ]
})

(get-path data "@items.0")       ; {"id": 1, "name": "First"}
(get-path data "@items.0.name")  ; "@First"
(get-path data "@items.1.id")    ; 2
```

### Alternative Array Syntax

Arrays can also use bracket notation:

```jsl
(get-path data "@items[0]")       ; {"id": 1, "name": "First"}
(get-path data "@items[0].name")  ; "@First"
(get-path data "@items[1].id")    ; 2
```

### Wildcards

Use `*` to match all elements:

```jsl
(def users [@
  {"@name": "@Alice", "@age": 30}
  {"@name": "@Bob", "@age": 25}
])

; Get all names
(get-path {"@users": users} "@users.*.name")
; Returns: ["Alice", "Bob"]

; Get all ages
(get-path {"@users": users} "@users.*.age")  
; Returns: [30, 25]
```

## Complex Examples

### Working with Nested Data

```jsl
(def company {
  "@name": "@TechCorp",
  "@departments": [@
    {
      "@name": "@Engineering",
      "@employees": [@
        {"@name": "@Alice", "@role": "@Lead"}
        {"@name": "@Bob", "@role": "@Developer"}
      ]
    }
    {
      "@name": "@Sales",
      "@employees": [@
        {"@name": "@Charlie", "@role": "@Manager"}
      ]
    }
  ]
})

; Access specific employee
(get-path company "@departments.0.employees.1.name")  ; "@Bob"

; Get all department names
(get-path company "@departments.*.name")  ; ["Engineering", "Sales"]

; Get all employee names across departments
(get-path company "@departments.*.employees.*.name")
; Returns: ["Alice", "Bob", "Charlie"]
```

### Building Complex Structures

```jsl
; Start with empty object
(def config {})

; Build configuration progressively
(def config
  (set-path config "@database.host" "@localhost"))
(def config  
  (set-path config "@database.port" 5432))
(def config
  (set-path config "@database.credentials.user" "@admin"))
(def config
  (set-path config "@database.credentials.password" "@secret"))

; Result:
; {
;   "database": {
;     "host": "localhost",
;     "port": 5432,
;     "credentials": {
;       "user": "admin",
;       "password": "secret"
;     }
;   }
; }
```

### Safe Data Extraction

```jsl
(def response {
  "@data": {
    "@user": {
      "@profile": {
        "@email": "@user@example.com"
      }
    }
  }
})

; Safe extraction with defaults
(get-safe response "@data.user.profile.email" "@no-email")  ; "@user@example.com"
(get-safe response "@data.user.profile.phone" "@no-phone")  ; "@no-phone"
(get-safe response "@data.user.address.city" "@unknown")    ; "@unknown"
```

## Integration with Query Operations

Path navigation works seamlessly with `where` and `transform`:

```jsl
; Filter by nested field
(where users (= (get-path it "@address.city") "@Boston"))

; Transform nested fields
(transform users 
  (assign "@full_address" 
    (str-concat 
      (get-path it "@address.street") ", "
      (get-path it "@address.city"))))

; Update nested fields
(transform orders
  (update-path "@shipping.status" 
    (lambda (s) (if (= s "@pending") "@processing" s))))
```

## Performance Considerations

- Path parsing is done once per operation
- Wildcards may traverse entire structures
- `set-path` creates new objects (immutable)
- `has-path` short-circuits on missing segments

## Error Handling

Path operations handle missing paths gracefully:

```jsl
(get-path {} "@a.b.c")       ; null (not an error)
(has-path {} "@a.b.c")       ; false
(set-path {} "@a.b.c" 123)   ; Creates full path
(update-path {} "@a.b.c" inc) ; null (can't update non-existent)
```

## See Also

- [Query Operations](query-operations.md) - Filtering with `where`
- [Transform Operations](transform-operations.md) - Data transformation
- [Objects](objects.md) - Working with JSL objects