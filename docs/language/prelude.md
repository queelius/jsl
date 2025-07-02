# Prelude Functions

## Overview

The JSL prelude provides the computational foundation for all JSL programs. These built-in functions are available in every JSL environment.

> For a guide to creating and managing execution contexts, see the [Environments](./environments.md) documentation.

## Special Forms (Core Syntax)

While the prelude contains a library of standard functions, the core language is defined by a small set of **special forms**. These are syntactic constructs that do not follow the standard evaluation rule (i.e., they don't necessarily evaluate all of their arguments).

The core special forms include `if`, `def`, `lambda`, `do`, `let`, and `try`. For a complete reference, please see the dedicated **[Special Forms](./special-forms.md)** documentation.

## Design Principles

- **Immutable Operations**: Functions return new values rather than modifying inputs
- **N-arity Support**: Mathematical and logical operations accept variable numbers of arguments
- **Type Safety**: Comprehensive type predicates and safe conversions
- **Functional Composition**: Higher-order functions that work seamlessly with JSL closures
- **JSON Compatibility**: All operations respect JSON's type system

## Data Constructors

### `list`
```json
["list", 1, 2, 3]  // → [1, 2, 3]
["list"]           // → []
```
Creates a list from the provided arguments.

## List Operations

JSL provides comprehensive list manipulation functions following functional programming principles.

### `append`
```json
["append", [1, 2, 3], 4]  // → [1, 2, 3, 4]
["append", [], 1]         // → [1]
```
Returns a new list with the item appended to the end.

### `prepend`
```json
["prepend", 0, [1, 2, 3]]  // → [0, 1, 2, 3]
["prepend", 1, []]         // → [1]
```
Returns a new list with the item prepended to the beginning.

### `concat`
```json
["concat", [1, 2], [3, 4], [5]]  // → [1, 2, 3, 4, 5]
["concat", [1], [2]]             // → [1, 2]
["concat"]                       // → []
```
Concatenates multiple lists into a single list.

### `first`
```json
["first", [1, 2, 3]]  // → 1
["first", []]         // → null
```
Returns the first element of a list, or null if empty.

### `rest`
```json
["rest", [1, 2, 3]]  // → [2, 3]
["rest", [1]]        // → []
["rest", []]         // → []
```
Returns all elements except the first, or empty list if insufficient elements.

### `nth`
```json
["nth", [10, 20, 30], 1]  // → 20
["nth", [10, 20], 5]      // → null
```
Returns the element at the specified index (0-based), or null if out of bounds.

### `length`
```json
["length", [1, 2, 3]]  // → 3
["length", []]         // → 0
["length", "hello"]    // → 5
```
Returns the length of a list or string.

### `empty?`
```json
["empty?", []]      // → true
["empty?", [1]]     // → false
["empty?", ""]      // → true
["empty?", "hi"]    // → false
```
Returns true if the collection is empty.

### `slice`
```json
["slice", [1, 2, 3, 4, 5], 1, 4]  // → [2, 3, 4]
["slice", [1, 2, 3], 1]           // → [2, 3]
["slice", "hello", 1, 4]          // → "ell"
```
Returns a slice of the list or string from start to end (exclusive).

### `reverse`
```json
["reverse", [1, 2, 3]]  // → [3, 2, 1]
["reverse", "hello"]    // → "olleh"
```
Returns a reversed copy of the list or string.

### `contains?`
```json
["contains?", [1, 2, 3], 2]      // → true
["contains?", [1, 2, 3], 4]      // → false
["contains?", "hello", "ell"]    // → true
```
Returns true if the collection contains the specified item.

### `index`
```json
["index", [10, 20, 30], 20]  // → 1
["index", [10, 20, 30], 40]  // → -1
```
Returns the index of the first occurrence of item, or -1 if not found.

## Dictionary Operations

Immutable dictionary operations supporting functional programming patterns.

### `get`
```json
["get", {"name": "Alice", "age": 30}, "name"]           // → "Alice"
["get", {"name": "Alice"}, "age", "unknown"]            // → "unknown"
```
Gets a value from a dictionary with optional default.

### `set`
```json
["set", {"name": "Alice"}, "age", 30]  // → {"name": "Alice", "age": 30}
["set", {}, "key", "value"]            // → {"key": "value"}
```
Returns a new dictionary with the key-value pair set.

### `keys`
```json
["keys", {"name": "Alice", "age": 30}]  // → ["name", "age"]
["keys", {}]                            // → []
```
Returns a list of all keys in the dictionary.

### `values`
```json
["values", {"name": "Alice", "age": 30}]  // → ["Alice", 30]
["values", {}]                            // → []
```
Returns a list of all values in the dictionary.

### `merge`
```json
["merge", {"a": 1}, {"b": 2}, {"c": 3}]  // → {"a": 1, "b": 2, "c": 3}
["merge", {"a": 1}, {"a": 2}]            // → {"a": 2}
```
Merges multiple dictionaries, with later values overriding earlier ones.

### `has-key?`
```json
["has-key?", {"name": "Alice"}, "name"]  // → true
["has-key?", {"name": "Alice"}, "age"]   // → false
```
Returns true if the dictionary contains the specified key.

## Arithmetic Operations

Mathematical operations with n-arity support for natural expression.

### `+` (Addition)
```json
["+", 1, 2, 3]    // → 6
["+", 5]          // → 5
["+"]             // → 0
```
Adds all arguments. With no arguments, returns 0.

### `-` (Subtraction)
```json
["-", 10, 3, 2]   // → 5 (10 - 3 - 2)
["-", 5]          // → -5 (negation)
["-"]             // → 0
```
Subtracts subsequent arguments from the first. With one argument, returns negation.

### `*` (Multiplication)
```json
["*", 2, 3, 4]    // → 24
["*", 5]          // → 5
["*"]             // → 1
```
Multiplies all arguments. With no arguments, returns 1.

### `/` (Division)
```json
["/", 12, 3, 2]   // → 2.0 (12 / 3 / 2)
["/", 5]          // → 0.2 (1 / 5)
```
Divides the first argument by all subsequent arguments. With one argument, returns reciprocal.

### `mod` (Modulo)
```json
["mod", 10, 3]    // → 1
["mod", 7, 0]     // → 0 (safe: returns 0 for division by zero)
```
Returns the remainder of division.

### `pow` (Exponentiation)
```json
["pow", 2, 3]     // → 8
["pow", 9, 0.5]   // → 3.0
```
Raises the first argument to the power of the second.

## Comparison Operations

Chained comparisons supporting mathematical notation.

### `=` (Equality)
```json
["=", 1, 1, 1]        // → true
["=", 1, 2]           // → false
["=", "a", "a", "a"]  // → true
```
Returns true if all arguments are equal.

### `<` (Less Than)
```json
["<", 1, 2, 3]    // → true (1 < 2 < 3)
["<", 1, 3, 2]    // → false
```
Returns true if arguments form an ascending sequence.

### `>` (Greater Than)
```json
[">", 3, 2, 1]    // → true (3 > 2 > 1)
[">", 3, 1, 2]    // → false
```
Returns true if arguments form a descending sequence.

### `<=` (Less Than or Equal)
```json
["<=", 1, 2, 2, 3]  // → true
["<=", 1, 3, 2]     // → false
```
Returns true if arguments form a non-decreasing sequence.

### `>=` (Greater Than or Equal)
```json
[">=", 3, 2, 2, 1]  // → true
[">=", 3, 1, 2]     // → false
```
Returns true if arguments form a non-increasing sequence.

## Logical Operations

Logical operations with n-arity support and short-circuiting.

### `and`
```json
["and", true, true, true]   // → true
["and", true, false, true]  // → false
["and"]                     // → true
```
Returns true if all arguments are truthy.

### `or`
```json
["or", false, false, true]  // → true
["or", false, false]        // → false
["or"]                      // → false
```
Returns true if any argument is truthy.

### `not`
```json
["not", true]    // → false
["not", false]   // → true
["not", 0]       // → true
["not", ""]      // → true
```
Returns the logical negation of the argument.

## Type Predicates

Essential for wire format validation and dynamic type checking.

### `null?`
```json
["null?", null]    // → true
["null?", 0]       // → false
["null?", false]   // → false
```
Returns true if the value is null.

### `bool?`
```json
["bool?", true]    // → true
["bool?", false]   // → true
["bool?", 0]       // → false
```
Returns true if the value is a boolean.

### `number?`
```json
["number?", 42]      // → true
["number?", 3.14]    // → true
["number?", "42"]    // → false
```
Returns true if the value is a number (integer or float).

### `string?`
```json
["string?", "hello"]  // → true
["string?", 42]       // → false
```
Returns true if the value is a string.

### `list?`
```json
["list?", [1, 2, 3]]  // → true
["list?", "hello"]    // → false
```
Returns true if the value is a list.

### `dict?`
```json
["dict?", {"a": 1}]   // → true
["dict?", [1, 2]]     // → false
```
Returns true if the value is a dictionary.

### `callable?`
```json
["callable?", ["lambda", ["x"], "x"]]  // → true (after evaluation)
["callable?", 42]                      // → false
```
Returns true if the value is callable (function or closure).

## String Operations

String manipulation functions for text processing.

### `str-concat`
```json
["str-concat", "Hello", " ", "World"]  // → "Hello World"
["str-concat", "Number: ", 42]         // → "Number: 42"
```
Concatenates all arguments after converting them to strings.

### `str-split`
```json
["str-split", "a,b,c", ","]     // → ["a", "b", "c"]
["str-split", "hello world"]    // → ["hello", "world"] (default: space)
```
Splits a string by the specified separator.

### `str-join`
```json
["str-join", ["a", "b", "c"], ","]    // → "a,b,c"
["str-join", [1, 2, 3], "-"]          // → "1-2-3"
["str-join", ["a", "b"]]              // → "ab" (default: empty string)
```
Joins a list of values into a string with the specified separator.

### `str-length`
```json
["str-length", "hello"]    // → 5
["str-length", ""]         // → 0
```
Returns the length of a string.

### `str-upper`
```json
["str-upper", "hello"]     // → "HELLO"
```
Converts a string to uppercase.

### `str-lower`
```json
["str-lower", "HELLO"]     // → "hello"
```
Converts a string to lowercase.

## Higher-Order Functions

The cornerstone of functional programming, enabling composition and abstraction.

### `map`
```json
["map", ["lambda", ["x"], ["*", "x", 2]], [1, 2, 3]]  // → [2, 4, 6]
["map", "+", [[1, 2], [3, 4]]]                        // → [3, 7]
```
Applies a function to each element of a list, returning a new list of results.

### `filter`
```json
["filter", ["lambda", ["x"], [">", "x", 5]], [1, 6, 3, 8, 2]]  // → [6, 8]
["filter", "even?", [1, 2, 3, 4, 5, 6]]                        // → [2, 4, 6]
```
Returns a new list containing only elements for which the predicate returns true.

### `reduce`
```json
["reduce", "+", [1, 2, 3, 4]]           // → 10
["reduce", "*", [1, 2, 3, 4], 1]        // → 24 (with initial value)
["reduce", "max", [3, 1, 4, 1, 5]]      // → 5
```
Reduces a list to a single value by repeatedly applying a binary function.

### `apply`
```json
["apply", "+", [1, 2, 3]]                    // → 6
["apply", ["lambda", ["x", "y"], ["*", "x", "y"]], [3, 4]]  // → 12
```
Applies a function to a list of arguments.

## Mathematical Functions

Extended mathematical operations for scientific computing.

### `min` / `max`
```json
["min", 3, 1, 4, 1, 5]  // → 1
["max", 3, 1, 4, 1, 5]  // → 5
```
Returns the minimum or maximum of the arguments.

### `abs`
```json
["abs", -5]    // → 5
["abs", 3.14]  // → 3.14
```
Returns the absolute value.

### `round`
```json
["round", 3.7]     // → 4
["round", 3.14159, 2]  // → 3.14
```
Rounds to the nearest integer or specified decimal places.

### Trigonometric Functions
```json
["sin", 1.5708]    // → ~1.0 (π/2)
["cos", 0]         // → 1.0
["tan", 0.7854]    // → ~1.0 (π/4)
```
Standard trigonometric functions (arguments in radians).

### `sqrt`
```json
["sqrt", 16]   // → 4.0
["sqrt", 2]    // → ~1.414
```
Returns the square root.

### `log` / `exp`
```json
["log", 2.718]   // → ~1.0 (natural log)
["exp", 1]       // → ~2.718 (e^1)
```
Natural logarithm and exponential functions.

## Type Conversion

Safe type conversion functions with reasonable defaults.

### `to-string`
```json
["to-string", 42]     // → "42"
["to-string", true]   // → "True"
["to-string", [1,2]]  // → "[1, 2]"
```
Converts any value to its string representation.

### `to-number`
```json
["to-number", "42"]      // → 42.0
["to-number", "3.14"]    // → 3.14
["to-number", "hello"]   // → 0 (safe default)
```
Attempts to convert a value to a number, returning 0 for invalid inputs.

### `type-of`
```json
["type-of", 42]        // → "int"
["type-of", "hello"]   // → "str"
["type-of", [1, 2]]    // → "list"
```
Returns the type name of a value.

## I/O Operations

Basic I/O functions (can be customized in sandboxed environments).

### `print`
```json
["print", "Hello, World!"]  // Outputs: Hello, World!
["print", 42, "is the answer"]  // Outputs: 42 is the answer
```
Prints values to standard output.

### `error`
```json
["error", "Something went wrong!"]  // Raises RuntimeError
```
Raises a runtime error with the specified message.

## Integration with JSL Closures

All higher-order functions in the prelude work seamlessly with JSL closures through the `eval_closure_or_builtin` integration layer. This ensures that:

1. **Lexical scoping is preserved** - Closures maintain access to their captured environments
2. **Built-in access is guaranteed** - All closures can access prelude functions
3. **Performance is optimized** - Environment chains are linked efficiently at call time
4. **Serialization is safe** - Only user bindings are serialized with closures

This design enables powerful functional programming patterns while maintaining JSL's core promise of safe, network-transmissible code.
