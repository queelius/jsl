# Learning Functions in JSL

## Introduction

Functions are the building blocks of JSL programs. In this tutorial, you'll learn to create, use, and combine functions through hands-on examples.

## Your First Function

Let's start with the simplest possible function:

```json
["lambda", ["x"], "x"]
```

This is the **identity function** - it returns whatever you give it. Try it:

```json
[["lambda", ["x"], "x"], "hello"]
// Result: "hello"
```

## Naming Functions

Usually, you'll want to give functions names:

```json
["def", "identity", ["lambda", ["x"], "x"]]
```

Now you can use it by name:

```json
["identity", "hello"]
// Result: "hello"
```

## Functions with Multiple Parameters

```json
["def", "add", ["lambda", ["a", "b"], ["+", "a", "b"]]]
["add", 3, 7]
// Result: 10
```

## Step-by-Step: Building a Math Library

### Step 1: Basic Operations

```json
["do",
  ["def", "square", ["lambda", ["x"], ["*", "x", "x"]]],
  ["def", "double", ["lambda", ["x"], ["*", "x", 2]]],
  ["def", "half", ["lambda", ["x"], ["/", "x", 2]]]]
```

### Step 2: Test Your Functions

```json
["square", 5]    // Result: 25
["double", 5]    // Result: 10  
["half", 10]     // Result: 5
```

### Step 3: Combining Functions

```json
["def", "square_and_double", 
  ["lambda", ["x"], ["double", ["square", "x"]]]]

["square_and_double", 3]
// 3 → square → 9 → double → 18
```

## Higher-Order Functions

Functions that work with other functions:

### Step 1: A Function That Applies Another Function Twice

```json
["def", "twice", 
  ["lambda", ["f", "x"], ["f", ["f", "x"]]]]
```

### Step 2: Use It

```json
["twice", "double", 5]
// 5 → double → 10 → double → 20
```

## Working with Lists

### Step 1: Processing Each Item

```json
["def", "numbers", [1, 2, 3, 4, 5]]
["map", "square", "numbers"]
// Result: [1, 4, 9, 16, 25]
```

### Step 2: Filtering Lists

```json
["def", "is_even", ["lambda", ["x"], ["=", ["mod", "x", 2], 0]]]
["filter", "is_even", "numbers"]
// Result: [2, 4]
```

### Step 3: Combining Operations

```json
["def", "sum_of_squares_of_evens",
  ["lambda", ["numbers"],
    ["sum", ["map", "square", ["filter", "is_even", "numbers"]]]]]

["sum_of_squares_of_evens", [1, 2, 3, 4, 5]]
// [1,2,3,4,5] → filter evens → [2,4] → square → [4,16] → sum → 20
```

## Closures: Functions That Remember

```json
["def", "make_adder", 
  ["lambda", ["n"], 
    ["lambda", ["x"], ["+", "x", "n"]]]]

["def", "add_10", ["make_adder", 10]]
["add_10", 5]
// Result: 15
```

The inner function "remembers" the value of `n` (10) even after `make_adder` finishes.

## Practice Exercises

### Exercise 1: Temperature Converter

Create functions to convert between Celsius and Fahrenheit:

```json
// Your solution here
["def", "celsius_to_fahrenheit", ["lambda", ["c"], ...]]
["def", "fahrenheit_to_celsius", ["lambda", ["f"], ...]]
```

<details>
<summary>Solution</summary>

```json
["do",
  ["def", "celsius_to_fahrenheit", 
    ["lambda", ["c"], ["+", ["*", "c", 9/5], 32]]],
  ["def", "fahrenheit_to_celsius", 
    ["lambda", ["f"], ["*", ["-", "f", 32], 5/9]]]]
```
</details>

### Exercise 2: List Statistics

Create a function that returns statistics about a list of numbers:

```json
// Should return: {"min": 1, "max": 5, "avg": 3, "count": 5}
["stats", [1, 2, 3, 4, 5]]
```

<details>
<summary>Solution</summary>

```json
["def", "stats",
  ["lambda", ["numbers"],
    {
      "min": ["min", "numbers"],
      "max": ["max", "numbers"], 
      "avg": ["/", ["sum", "numbers"], ["length", "numbers"]],
      "count": ["length", "numbers"]
    }]]
```
</details>

## Next Steps

- Learn about [working with data](data.md)
- Explore [JSON templates](../language/templates.md)
- Try [distributed computing](../architecture/distributed.md)

Functions in JSL are powerful and flexible. With closures and higher-order functions, you can build complex programs from simple, composable pieces.
