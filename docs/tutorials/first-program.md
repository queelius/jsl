# Your First JSL Program

Welcome to JSL! This tutorial will walk you through creating your first JSL program step by step. By the end, you'll understand JSL's core concepts and be ready to build more complex applications.

## What Makes JSL Different

JSL is unlike most programming languages you may have used before. The key insight is that **code and data are the same thing** - both are represented as JSON. This means:

- Your program is valid JSON that can be transmitted over networks
- Functions can be serialized and reconstructed anywhere  
- No compilation step - JSON is the native format
- Universal compatibility - any system that handles JSON can run JSL

## Hello, World!

Let's start with the classic first program. Create a file called `hello.json`:

```json
["print", "Hello, World!"]
```

Run it:

```bash
python -m jsl hello.json
```

**What happened?**

1. `["print", "Hello, World!"]` is a **function call** 
2. `"print"` is the function name (a built-in function)
3. `"Hello, World!"` is the argument
4. JSL evaluates the expression and calls the print function

## Understanding Prefix Notation

JSL uses **prefix notation** - the operator comes first:

```json
// Traditional: 2 + 3
["+", 2, 3]

// Traditional: 2 + 3 + 4  
["+", 2, 3, 4]

// Traditional: 2 * (3 + 4)
["*", 2, ["+", 3, 4]]
```

Try it:

```json
["print", "2 + 3 =", ["+", 2, 3]]
```

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
    "name": "Bob",
    "age": 25,
    "city": "San Francisco"
  }],
  
  ["def", "name", ["get", "person", "name"]],
  ["def", "age", ["get", "person", "age"]],
  
  // Create a new person with updated age
  ["def", "older-person", ["set", "person", "age", ["+", "age", 1]]],
  
  ["print", "Original person:", "person"],
  ["print", "Person next year:", "older-person"]
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
- **[Code Serialization](serialization.md)** - Sending code over networks
- **[Distributed Computing](distributed.md)** - Building distributed applications

## Practice Exercises

Try building these programs yourself:

1. **FizzBuzz**: Print numbers 1-100, but "Fizz" for multiples of 3, "Buzz" for multiples of 5, and "FizzBuzz" for multiples of both.

2. **Word Counter**: Given a list of words, count how many times each word appears.

3. **Temperature Converter**: Create functions to convert between Celsius and Fahrenheit.

4. **Shopping Cart**: Calculate the total price of items in a shopping cart, including tax.

Ready to tackle these? You have all the tools you need!
