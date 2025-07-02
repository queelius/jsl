# Getting Started with JSL

This guide provides a concise introduction to JSL to get you up and running in minutes. JSL is a lightweight, functional programming language that uses JSON for its syntax, making it ideal for data manipulation, configuration, and network-native applications.

## Installation

JSL requires Python 3.8 or later.

### From Source

Clone the repository and install JSL using pip:

```bash
git clone https://github.com/queelius/jsl.git
cd jsl
pip install -e .
```

### Verify Installation

You can verify the installation by running a simple program or by starting the interactive REPL:

```bash
# Run a simple JSL program from the command line
echo '["print", "@Hello, JSL!"]' | jsl

# Start the interactive REPL
jsl --repl
```

## Your First JSL Program

JSL programs are simply JSON data structures. Create a file named `hello.jsl` with the following content:

```json
["print", "@Hello, World!"]
```

Execute it from your terminal:

```bash
jsl hello.jsl
```

You should see the output: `Hello, World!`

> **Note on File Extensions**
> We recommend using the `.jsl` extension for your JSL program files. This helps distinguish them from regular JSON data files and allows for better editor integration. However, the `jsl` interpreter will happily run files with a `.json` extension, preserving the principle that all JSL code is valid JSON.

## Core Concepts

### Literals and Variables

Standard JSON literals like numbers, booleans, and `null` evaluate to themselves. Strings are used for both literal text and variable references. A string with an `@` prefix is a literal, while a string without it is treated as a variable.

```json
42          // A number
"@hello"    // A string literal
"my_variable" // A reference to a variable
```

### Basic Operations

JSL uses prefix notation (like Lisp) for function calls. The first element of an array is the function to be called, and the rest are its arguments.

```json
["+", 1, 2, 3]
```

This expression evaluates to `6`.

### Defining Variables and Functions

You can define variables with `def` and functions with `lambda`. The `do` special form lets you execute a sequence of expressions.

```json
[
  "do",
  ["def", "x", 10],
  ["def", "square", ["lambda", ["n"], ["*", "n", "n"]]],
  ["square", "x"]
]
```

This evaluates to `100`.

### Conditional Logic

The `if` special form provides conditional evaluation:

```json
["if", [">", 5, 3], "@Greater", "@Less"]
```

This evaluates to `"Greater"`.

## A Quick Example: Fibonacci

Here is a more complete example that defines a recursive function to compute Fibonacci numbers and then applies it to a list of numbers:

```json
[
  "do",
  ["def", "fib",
   ["lambda", ["n"],
    ["if", ["<=", "n", 1],
     "n",
     ["+", ["fib", ["-", "n", 1]], ["fib", ["-", "n", 2]]]]]],
  ["map", "fib", ["list", 0, 1, 2, 3, 4, 5, 6, 7, 8, 9]]
]
```

## Running JSL Code

You can run JSL programs in several ways:

- **From a file:** `jsl your_program.jsl`
- **From standard input:** `echo '["+", 1, 2]' | jsl`
- **Using the REPL:** `jsl --repl`
- **As a web service:** `jsl --service`

## Next Steps

Now that you have a basic understanding of JSL, you can explore the following sections for more in-depth information:

- **[Language Guide](language/overview.md)**: For a comprehensive overview of JSL's syntax and semantics.
- **[Tutorials](tutorials/first-program.md)**: For guided, step-by-step lessons.
- **[Examples](examples/simple.md)**: For a collection of practical, real-world examples.