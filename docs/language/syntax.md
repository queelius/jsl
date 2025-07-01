# JSL Syntax Guide

## Overview

JSL uses JSON as its native syntax, making it both human-readable and machine-parseable. Every JSL program is valid JSON, and every JSON value can be interpreted as a JSL expression.

## Basic Syntax Rules

### Literals

All JSON primitives are self-evaluating:

```json
42          // Number
"@hello"    // String literal (@ prefix indicates literal)
true        // Boolean
false       // Boolean  
null        // Null value
```

### Variables

Strings without the `@` prefix are variable references:

```json
"variable_name"  // References variable named 'variable_name'
```

### Function Calls

Arrays represent function calls in prefix notation:

```json
["+", 1, 2, 3]           // Addition: (+ 1 2 3)
["map", "fn", "list"]    // Map function over list
```

### Special Forms

Special forms handle control flow and definitions:

```json
["def", "x", 42]                    // Variable definition
["lambda", ["x"], ["*", "x", 2]]    // Function definition
["if", "condition", "then", "else"] // Conditional
["do", "expr1", "expr2", "expr3"]   // Sequential execution
```

## Data Structures

### Lists

```json
[1, 2, 3, 4]                    // List of numbers
["@apple", "@banana", "@cherry"] // List of string literals
["first", "second", "variable"]  // Mixed list with variable reference
```

### Objects

```json
{
  "name": "@John Doe",
  "age": 30,
  "email": "user_email"  // Variable reference
}
```

For more details, see the [AST specification](ast.md).