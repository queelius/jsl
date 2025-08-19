# Your First JSL Program

Welcome to JSL! This tutorial will walk you through creating your first JSL program step by step. By the end, you'll understand JSL's core concepts and be ready to build more complex applications.

## What Makes JSL Different

JSL is unlike most programming languages you may have used before. The key insight is that **code and data are the same thing** - both are represented as JSON. This means:

- Your program is valid JSON that can be transmitted over networks
- Functions can be serialized and reconstructed anywhere  
- Dual evaluation modes - direct interpretation or JIT compilation to stack bytecode
- Pauseable/resumable execution - programs can be suspended and continued later
- Universal compatibility - any system that handles JSON can work with JSL

## Hello, World!

Let's start with the classic first program. JSL supports two syntax styles - JSON arrays and Lisp-style parentheses. Create a file called `hello.jsl`:

### JSON Array Syntax
```json
["host", "@print", "@Hello, JSL!"]
```

### Lisp-Style Syntax (Human-Friendly)
```lisp
(host @print "Hello, JSL!")
```

Both are exactly equivalent! The Lisp-style is often easier to read and write, while JSON is universal for network transmission.

Now, run it from your terminal:

```bash
jsl hello.jsl
```

You should see the output:

```
Hello, JSL!
```

**What happened?**

1. `(host @print "Hello, JSL!")` is a **host interaction** 
2. `host` is a special form for side effects
3. `@print` is the host command (@ prefix in JSON, quoted in Lisp-style)
4. `"Hello, JSL!"` is the argument to print
5. JSL sends the print request to the host environment

## How JSL Executes Your Code

JSL offers two execution strategies:

### 1. Recursive Evaluation (Default)
The S-expression is directly evaluated by walking the tree structure. This is the default mode and works well for most programs.

### 2. Stack Machine Compilation (Available on Request)
JSL can compile your program Just-In-Time to JPN (JSL Postfix Notation) bytecode when you need advanced features:

```json
// Your code: ["+", 1, 2, 3]
// Compiles to JPN: [1, 2, 3, 3, "+"]
// Executes on stack machine with resumable state
```

The stack machine enables:
- **Pauseable execution** - Stop after N steps and resume later
- **Resource limits** - Control CPU/memory usage with gas metering
- **Distributed execution** - Pause on one machine, resume on another
- **Debugging** - Step through execution instruction by instruction

Even the paused execution state is pure JSON - maintaining JSL's core principle that everything (code, data, and even execution state) can be serialized and transmitted!

You don't need to worry about this initially - JSL handles it automatically. But it's there when you need advanced features!

## Understanding Prefix Notation

JSL uses **prefix notation** - the operator comes first. Here's the same code in both syntaxes:

### JSON Array Syntax
```json
// Traditional: 2 + 3
["+", 2, 3]

// Traditional: 2 + 3 + 4  
["+", 2, 3, 4]

// Traditional: 2 * (3 + 4)
["*", 2, ["+", 3, 4]]
```

### Lisp-Style Syntax
```lisp
; Traditional: 2 + 3
(+ 2 3)

; Traditional: 2 + 3 + 4
(+ 2 3 4)

; Traditional: 2 * (3 + 4)
(* 2 (+ 3 4))
```

The Lisp-style is often more readable, especially for complex expressions!

## Variables with `def`

Use `def` to create variables:

```json
[
  "do",
  ["def", "name", "Alice"],
  ["def", "age", 30],
  ["print", "Hello,", "name", "! You are", "age", "years old."]
]
```

**Breaking it down:**

1. `"do"` executes multiple expressions in sequence
2. `["def", "name", "Alice"]` creates a variable called `name`
3. `["def", "age", 30]` creates a variable called `age`  
4. The print statement uses the variables by referencing their names

## Your First Function

Let's create a function to calculate the area of a circle:

```json
[
  "do",
  ["def", "pi", 3.14159],
  ["def", "circle-area", 
   ["lambda", ["radius"], 
    ["*", "pi", "radius", "radius"]]],
  ["def", "my-radius", 5],
  ["def", "area", ["circle-area", "my-radius"]],
  ["print", "Circle with radius", "my-radius", "has area", "area"]
]
```

**Understanding `lambda`:**

- `["lambda", ["radius"], ...]` creates a function
- `["radius"]` is the parameter list (the function takes one argument)
- `["*", "pi", "radius", "radius"]` is the function body
- The function calculates π × radius²

## Working with Lists

Lists are fundamental in JSL. Let's explore list operations:

```json
[
  "do",
  ["def", "numbers", ["list", 1, 2, 3, 4, 5]],
  ["def", "first-number", ["first", "numbers"]],
  ["def", "rest-numbers", ["rest", "numbers"]],
  ["def", "list-length", ["length", "numbers"]],
  
  ["print", "Original list:", "numbers"],
  ["print", "First element:", "first-number"], 
  ["print", "Rest of list:", "rest-numbers"],
  ["print", "List length:", "list-length"]
]
```

## Higher-Order Functions

Now for something powerful - functions that work with other functions:

```json
[
  "do",
  ["def", "numbers", ["list", 1, 2, 3, 4, 5]],
  
  // Double each number
  ["def", "double", ["lambda", ["x"], ["*", "x", 2]]],
  ["def", "doubled", ["map", "double", "numbers"]],
  
  // Filter even numbers
  ["def", "is-even", ["lambda", ["n"], ["=", ["mod", "n", 2], 0]]],
  ["def", "evens", ["filter", "is-even", "numbers"]],
  
  // Sum all numbers
  ["def", "total", ["reduce", "+", "numbers", 0]],
  
  ["print", "Original:", "numbers"],
  ["print", "Doubled:", "doubled"],
  ["print", "Evens only:", "evens"], 
  ["print", "Sum:", "total"]
]
```

**Key concepts:**

- `map` applies a function to each element of a list
- `filter` keeps only elements that match a condition
- `reduce` combines all elements into a single value

## Conditional Logic

Use `if` for decisions:

```json
[
  "do",
  ["def", "temperature", 75],
  ["def", "weather", 
   ["if", [">", "temperature", 80],
    "hot",
    ["if", [">", "temperature", 60], 
     "warm", 
     "cool"]]],
  ["print", "It's", "weather", "today at", "temperature", "degrees"]
]
```

## Data Structures

Work with dictionaries (objects) to structure data:

```json
[
  "do",
  ["def", "person", {
    "@name": "@Bob",
    "@age": 25,
    "@city": "@San Francisco"
  }],
  
  ["def", "name", ["get", "person", "@name"]],
  ["def", "age", ["get", "person", "@age"]],
  
  // Create a new person with updated age
  ["def", "older-person", ["set", "person", "@age", ["+", "age", 1]]],
  
  ["host", "@print", "@Original person:", "person"],
  ["host", "@print", "@Person next year:", "older-person"]
]
```

## Modern Data Operations

JSL provides powerful special forms for working with collections:

### Filtering with `where`

Instead of verbose lambda expressions, use the declarative `where` form. The fields from each item are automatically available as variables!

#### JSON Syntax
```json
["where", "users", ["and", "active", [">", "age", 30]]]
```

#### Lisp-Style Syntax
```lisp
(where users (and active (> age 30)))
```

Complete example in Lisp-style:
```lisp
(do
  (def users [@
    {"name": "Alice", "age": 30, "active": true}
    {"name": "Bob", "age": 25, "active": false}
    {"name": "Charlie", "age": 35, "active": true}])
  
  ; Filter active users - fields are automatically available!
  (def active-users (where users active))
  
  ; Complex conditions
  (def active-adults (where users 
    (and active (> age 30))))
  
  (host @print "Active adults:" active-adults))
```

### Transforming with `transform`

Reshape data declaratively:

```json
[
  "do",
  ["def", "products", [
    {"@name": "@Widget", "@price": 29.99, "@stock": 100}
  ]],
  
  // Add discount field
  ["def", "discounted", ["transform", "products",
    ["assign", "@discount", ["*", "price", 0.1]]]],
  
  // Pick only certain fields
  ["def", "summary", ["transform", "products",
    ["pick", "@name", "@price"]]],
  
  ["host", "@print", "@Products with discount:", "discounted"]
]
```

## Putting It Together: A Complete Example

Let's build a program that processes a list of people:

```json
[
  "do",
  
  // Sample data
  ["def", "people", [
    {"name": "Alice", "age": 30, "city": "NYC"},
    {"name": "Bob", "age": 25, "city": "SF"}, 
    {"name": "Charlie", "age": 35, "city": "NYC"},
    {"name": "Diana", "age": 28, "city": "LA"}
  ]],
  
  // Helper functions
  ["def", "get-name", ["lambda", ["person"], ["get", "person", "name"]]],
  ["def", "get-age", ["lambda", ["person"], ["get", "person", "age"]]],
  ["def", "is-adult", ["lambda", ["person"], [">=", ["get-age", "person"], 18]]],
  ["def", "lives-in-nyc", ["lambda", ["person"], ["=", ["get", "person", "city"], "NYC"]]],
  
  // Process the data
  ["def", "adults", ["filter", "is-adult", "people"]],
  ["def", "nyc-adults", ["filter", "lives-in-nyc", "adults"]],
  ["def", "nyc-names", ["map", "get-name", "nyc-adults"]],
  ["def", "average-age", 
   ["/", ["reduce", "+", ["map", "get-age", "adults"], 0], ["length", "adults"]]],
  
  // Output results
  ["print", "All people:", ["map", "get-name", "people"]],
  ["print", "Adults in NYC:", "nyc-names"],
  ["print", "Average age of adults:", "average-age"]
]
```

This program demonstrates:

- Working with structured data (lists and dictionaries)
- Creating helper functions for common operations
- Chaining operations together (filter, then map)
- Computing aggregates (average age)

## What You've Learned

Congratulations! You now understand:

1. **Prefix notation** - operators come first
2. **Variables** - using `def` to bind values to names
3. **Functions** - creating them with `lambda`
4. **Lists and dictionaries** - fundamental data structures
5. **Higher-order functions** - `map`, `filter`, `reduce`
6. **Conditional logic** - making decisions with `if`
7. **JSON structure** - how code and data are the same

## Next Steps

Ready to learn more? Try these tutorials:

- **[Working with Functions](functions.md)** - Advanced function concepts
- **[Data Manipulation](data.md)** - Complex data processing patterns
- **[Code Serialization](../architecture/serialization.md)** - Sending code over networks
- **[Distributed Computing](../architecture/distributed.md)** - Building distributed applications

## Practice Exercises

Try building these programs yourself:

1. **FizzBuzz**: Print numbers 1-100, but "Fizz" for multiples of 3, "Buzz" for multiples of 5, and "FizzBuzz" for multiples of both.

2. **Word Counter**: Given a list of words, count how many times each word appears.

3. **Temperature Converter**: Create functions to convert between Celsius and Fahrenheit.

4. **Shopping Cart**: Calculate the total price of items in a shopping cart, including tax.

Ready to tackle these? You have all the tools you need!
