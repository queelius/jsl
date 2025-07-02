# JSON Objects as First-Class Citizens

## Overview

JSL treats JSON objects as **first-class data structures** with native support for dynamic construction. Unlike arrays (which are interpreted as S-expressions), JSON objects in JSL are always treated as data structures, making them perfect for constructing pure JSON output without ambiguity.

## Why Objects Are Special

In JSL, there's an important distinction between arrays and objects:

- **Arrays**: `["+", 1, 2]` are interpreted as function calls (S-expressions)
- **Objects**: `{"name": "Alice"}` are always treated as data structures

This means objects provide a "safe zone" for pure data construction where you don't have to worry about the first element being interpreted as an operator.

## Object Construction Syntax

JSL objects use **normal JSL evaluation rules** for both keys and values:

- **Keys** must evaluate to strings
- **Values** can be any JSL expression
- Use `@` prefix for literal strings in both keys and values

### Basic Examples

**Literal Object:**
```json
{"@name": "@Alice", "@age": 25}
```
**Result:** `{"name": "Alice", "age": 25}`

**Dynamic Values:**
```json
["do",
  ["def", "user_name", "@Bob"],
  ["def", "user_age", 30],
  {"@name": "user_name", "@age": "user_age"}
]
```
**Result:** `{"name": "Bob", "age": 30}`

**Dynamic Keys:**
```json
["do",
  ["def", "field_name", "@username"],
  {"field_name": "@Alice"}
]
```
**Result:** `{"username": "Alice"}`

## String Construction in Objects

For dynamic string construction, use JSL's string functions:

```json
["do",
  ["def", "name", "@Alice"],
  ["def", "age", 25],
  {
    "@greeting": ["str-concat", "@Hello ", "name"],
    "@info": ["str-concat", "@Age: ", "age"],
    "@status": ["if", [">", "age", 18], "@adult", "@minor"]
  }
]
```
**Result:**
```json
{
  "greeting": "Hello Alice",
  "info": "Age: 25", 
  "status": "adult"
}
```

## Nested Objects and Complex Structures

Objects can contain any JSL expressions, including nested objects and arrays:

```json
["do",
  ["def", "users", ["@", ["Alice", "Bob", "Carol"]]],
  {
    "@project": "@My Project",
    "@team": {
      "@lead": ["first", "users"],
      "@members": "users",
      "@size": ["length", "users"]
    },
    "@tags": ["@", ["web", "javascript", "api"]]
  }
]
```

## Advantages of Object-First Design

1. **No Operator Ambiguity**: Objects are always data, never function calls
2. **Pure JSON Output**: Objects naturally serialize to clean JSON
3. **Composable**: Works seamlessly with JSL functions and variables
4. **Consistent Syntax**: Uses the same `@` rules as the rest of JSL
5. **Type Safety**: Keys are validated to be strings at runtime

## Working with Object Functions

JSL provides built-in functions for object manipulation:

```json
["do",
  ["def", "user", {"@name": "@Alice", "@role": "@admin"}],
  
  ["get", "user", "@name"],        // → "Alice"
  ["has", "user", "@email"],       // → false
  ["keys", "user"],                // → ["name", "role"]
  
  ["set", "user", "@email", "@alice@example.com"]  // Add new field
]
```
