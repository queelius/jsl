# Working with Data in JSL

## Introduction

JSL uses JSON for all data structures, making it easy to work with familiar formats. This tutorial teaches you to manipulate data step by step.

## Basic Data Types

JSL supports all JSON data types:

```json
["do",
  ["def", "number", 42],
  ["def", "string", "hello"],
  ["def", "boolean", true],
  ["def", "null_value", null],
  ["def", "array", [1, 2, 3]],
  ["def", "object", {"name": "Alice", "age": 30}]]
```

## Working with Objects

### Accessing Object Properties

```json
["def", "person", {"name": "Alice", "age": 30, "city": "New York"}]

["get", "person", "name"]     // Result: "Alice"
["get", "person", "age"]      // Result: 30
```

### Modifying Objects

```json
["def", "updated_person", 
  ["assoc", "person", "age", 31]]
// Result: {"name": "Alice", "age": 31, "city": "New York"}
```

### Adding New Properties

```json
["def", "person_with_email",
  ["assoc", "person", "email", "alice@example.com"]]
```

## Working with Arrays

### Basic Array Operations

```json
["def", "numbers", [1, 2, 3, 4, 5]]

["length", "numbers"]              // Result: 5
["first", "numbers"]               // Result: 1
["last", "numbers"]                // Result: 5
["nth", "numbers", 2]              // Result: 3 (0-indexed)
```

### Adding Elements

```json
["conj", "numbers", 6]             // Result: [1, 2, 3, 4, 5, 6]
["concat", "numbers", [6, 7, 8]]   // Result: [1, 2, 3, 4, 5, 6, 7, 8]
```

## Step-by-Step: Building a Contact Manager

### Step 1: Create Contact Data

```json
["def", "contacts", [
  {"name": "Alice", "email": "alice@example.com", "phone": "555-0101"},
  {"name": "Bob", "email": "bob@example.com", "phone": "555-0102"},
  {"name": "Charlie", "email": "charlie@example.com", "phone": "555-0103"}
]]
```

### Step 2: Find a Contact by Name

```json
["def", "find_contact",
  ["lambda", ["name"],
    ["first", 
      ["filter", 
        ["lambda", ["contact"], ["=", ["get", "contact", "name"], "name"]], 
        "contacts"]]]]

["find_contact", "Alice"]
// Result: {"name": "Alice", "email": "alice@example.com", "phone": "555-0101"}
```

### Step 3: Get All Email Addresses

```json
["def", "get_all_emails",
  ["lambda", [], 
    ["map", ["lambda", ["contact"], ["get", "contact", "email"]], "contacts"]]]

["get_all_emails"]
// Result: ["alice@example.com", "bob@example.com", "charlie@example.com"]
```

### Step 4: Add a New Contact

```json
["def", "add_contact",
  ["lambda", ["name", "email", "phone"],
    ["conj", "contacts", {"name": "name", "email": "email", "phone": "phone"}]]]

["def", "updated_contacts", 
  ["add_contact", "Diana", "diana@example.com", "555-0104"]]
```

## Data Transformation Patterns

### Filtering Data

```json
// Find contacts with Gmail addresses
["def", "gmail_contacts",
  ["filter", 
    ["lambda", ["contact"], 
      ["includes?", ["get", "contact", "email"], "gmail.com"]], 
    "contacts"]]
```

### Grouping Data

```json
// Group contacts by email domain
["def", "group_by_domain",
  ["group_by", 
    ["lambda", ["contact"], 
      ["last", ["split", ["get", "contact", "email"], "@"]]], 
    "contacts"]]
```

### Sorting Data

```json
// Sort contacts by name
["def", "sorted_contacts",
  ["sort_by", ["lambda", ["contact"], ["get", "contact", "name"]], "contacts"]]
```

## Working with Nested Data

### Step 1: Complex Data Structure

```json
["def", "company", {
  "name": "Tech Corp",
  "departments": [
    {
      "name": "Engineering", 
      "employees": [
        {"name": "Alice", "salary": 100000},
        {"name": "Bob", "salary": 95000}
      ]
    },
    {
      "name": "Sales",
      "employees": [
        {"name": "Charlie", "salary": 80000},
        {"name": "Diana", "salary": 85000}
      ]
    }
  ]
}]
```

### Step 2: Extract All Employee Names

```json
["def", "all_employee_names",
  ["flatten", 
    ["map", 
      ["lambda", ["dept"], 
        ["map", 
          ["lambda", ["emp"], ["get", "emp", "name"]], 
          ["get", "dept", "employees"]]], 
      ["get", "company", "departments"]]]]

["all_employee_names"]
// Result: ["Alice", "Bob", "Charlie", "Diana"]
```

### Step 3: Calculate Total Payroll

```json
["def", "total_payroll",
  ["sum", 
    ["flatten", 
      ["map", 
        ["lambda", ["dept"], 
          ["map", 
            ["lambda", ["emp"], ["get", "emp", "salary"]], 
            ["get", "dept", "employees"]]], 
        ["get", "company", "departments"]]]]]

["total_payroll"]
// Result: 360000
```

## Data Validation

### Step 1: Validation Functions

```json
["def", "valid_email?",
  ["lambda", ["email"], 
    ["and", 
      ["includes?", "email", "@"],
      [">", ["length", "email"], 5]]]]

["def", "valid_phone?",
  ["lambda", ["phone"],
    ["=", ["length", "phone"], 12]]]  // Assuming XXX-XXXX format
```

### Step 2: Validate Contact

```json
["def", "valid_contact?",
  ["lambda", ["contact"],
    ["and",
      ["valid_email?", ["get", "contact", "email"]],
      ["valid_phone?", ["get", "contact", "phone"]],
      [">", ["length", ["get", "contact", "name"]], 0]]]]
```

### Step 3: Filter Valid Contacts

```json
["def", "valid_contacts",
  ["filter", "valid_contact?", "contacts"]]
```

## Dynamic Object Construction with Data

### Step 1: Email Object Structure

```json
["def", "create_email", 
  ["lambda", ["recipient_email", "recipient_name"],
    {
      "@to": "recipient_email",
      "@subject": ["str-concat", "@Welcome ", "recipient_name", "@!"],
      "@body": ["str-concat", "@Hello ", "recipient_name", "@, welcome to our service!"]
    }
  ]
]
```

### Step 2: Generate Emails for All Contacts

```json
["def", "generate_welcome_emails",
  ["map", 
    ["lambda", ["contact"],
      ["create_email",
        ["get", "contact", "@email"],
        ["get", "contact", "@name"]
      ]], 
    "contacts"]]
```

## Practice Exercises

### Exercise 1: Inventory Management

Create functions to manage a product inventory:

```json
["def", "inventory", [
  {"id": 1, "name": "Laptop", "price": 999, "stock": 5},
  {"id": 2, "name": "Mouse", "price": 25, "stock": 50},
  {"id": 3, "name": "Keyboard", "price": 75, "stock": 20}
]]

// Find products under $100
// Calculate total inventory value
// Find products with low stock (< 10)
```

### Exercise 2: Student Grades

Work with student grade data:

```json
["def", "students", [
  {"name": "Alice", "grades": [85, 92, 78, 96]},
  {"name": "Bob", "grades": [76, 84, 91, 88]},
  {"name": "Charlie", "grades": [92, 95, 89, 94]}
]]

// Calculate average grade for each student
// Find the student with the highest average
// List all grades above 90
```

## Next Steps

- Learn about [JSON Objects](../language/objects.md) as first-class data structures
- Explore [functions](functions.md) for data processing
- Try [distributed computing](../architecture/distributed.md) with data

Working with data in JSL is straightforward because everything is JSON. The functional approach with `map`, `filter`, and `reduce` makes data transformation both powerful and readable.
