# Simple JSL Examples

## Basic Arithmetic

```json
// Addition
["+", 5, 3]
// Result: 8

// Multiplication  
["*", 4, 6]
// Result: 24

// Nested operations
["+", ["*", 2, 3], ["*", 4, 5]]
// Result: 26
```

## Variables and Functions

```json
// Define and use variables with let
["let", [
  ["x", 10],
  ["y", 20]
],
  ["+", "x", "y"]
]
// Result: 30

// Define and use a function
["let", [
  ["double", ["lambda", ["n"], ["*", "n", 2]]]
],
  ["double", 5]
]
// Result: 10
```

## Working with Lists

```json
// Creating lists with quote
["let", [
  ["numbers", ["@", [1, 2, 3, 4, 5]]],
  ["double", ["lambda", ["x"], ["*", "x", 2]]]
],
  ["map", "double", "numbers"]
]
// Result: [2, 4, 6, 8, 10]

// Creating lists with the list function
["let", [
  ["numbers", ["list", 1, 2, 3, 4, 5]],
  ["is-even", ["lambda", ["x"], ["=", ["mod", "x", 2], 0]]]
],
  ["filter", "is-even", "numbers"]
]
// Result: [2, 4]
```

## Conditional Logic

```json
// Simple if expression
["if", [">", 10, 5], "@yes", "@no"]
// Result: "yes"

// Function with conditional logic
["let", [
  ["check-age", 
    ["lambda", ["age"],
      ["if", [">=", "age", 18], "@adult", "@minor"]]]
],
  ["list",
    ["check-age", 25],  // Result: "adult"
    ["check-age", 15]   // Result: "minor"
  ]
]
```

## Working with Objects

```json
// Create an object with computed values
["let", [
  ["name", "@Alice"],
  ["age", 30]
],
  {"@user": "name", 
   "@adult": [">=", "age", 18]}
]
// Result: {"user": "Alice", "adult": true}

// Access object properties
["let", [
  ["person", {"@name": "@Bob", "@age": 25}]
],
  ["get", "person", "@name"]
]
// Result: "Bob"
```