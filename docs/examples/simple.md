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
// Define a variable
["def", "x", 10]

// Define a function
["def", "double", ["lambda", ["n"], ["*", "n", 2]]]

// Use the function
["double", "x"]
// Result: 20
```

## Working with Lists

```json
// Define a list
["def", "numbers", [1, 2, 3, 4, 5]]

// Double all numbers
["map", ["lambda", ["x"], ["*", "x", 2]], "numbers"]
// Result: [2, 4, 6, 8, 10]

// Filter even numbers
["filter", ["lambda", ["x"], ["=", ["mod", "x", 2], 0]], "numbers"]
// Result: [2, 4]
```

## Conditional Logic

```json
["def", "check_age", 
  ["lambda", ["age"],
    ["if", [">=", "age", 18], "adult", "minor"]]]

["check_age", 25]  // Result: "adult"
["check_age", 15]  // Result: "minor"
```