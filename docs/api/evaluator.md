# Evaluator API Reference

The evaluator module (`jsl.evaluator`) contains the core evaluation engine for JSL expressions.

## Functions

### `eval_expr`

The main evaluation function for JSL expressions.

::: jsl.evaluator.eval_expr
    handler: python
    options:
      show_root_heading: yes
      show_source: yes

### `eval_template`

Evaluates JSON templates with dynamic value substitution.

::: jsl.evaluator.eval_template
    handler: python
    options:
      show_root_heading: yes
      show_source: yes

### `find_free_variables`

Analyzes expressions to find unbound variables.

::: jsl.evaluator.find_free_variables
    handler: python
    options:
      show_root_heading: yes
      show_source: yes

## Special Forms

The evaluator handles several special forms that control evaluation:

### `do` - Sequential Execution
```json
["do", expr1, expr2, expr3]
```
Evaluates expressions in order, returns the result of the last expression.

### `def` - Variable Definition
```json
["def", "variable-name", value-expression]
```
Evaluates the value expression and binds it to the variable name in the current environment.

### `lambda` - Function Definition  
```json
["lambda", ["param1", "param2"], body-expression]
```
Creates a closure that captures the current environment.

### `if` - Conditional Expression
```json
["if", condition-expr, then-expr, else-expr]
```
Evaluates condition; if truthy, evaluates then-expr, otherwise else-expr.

### `quote` - Literal Expression
```json
["quote", expression]
```
Returns the expression without evaluating it.

### `template` - JSON Template
```json
["template", json-template]
```
Processes a JSON template, evaluating `{"$": expression}` substitutions.

## Evaluation Rules

### Variable References
Strings are treated as variable references and looked up in the environment:

```python
# In environment with x=10
eval_expr("x", env)  # Returns 10
```

### Function Calls
Lists with the first element being a function are treated as function calls:

```python
# Built-in function call
eval_expr(["+", 1, 2, 3], env)  # Returns 6

# User function call  
eval_expr(["my-func", "arg1", "arg2"], env)
```

### Literals
Non-string atomic values are returned as-is:

```python
eval_expr(42, env)     # Returns 42
eval_expr(true, env)   # Returns True
eval_expr(null, env)   # Returns None
```

## Template Processing

Templates allow dynamic JSON generation:

```python
template = {
    "user": {"$": "username"},
    "posts": [
        {"title": {"$": "post-title"}},
        {"content": {"$": "post-content"}}
    ],
    "metadata": {
        "timestamp": {"$": ["now"]},
        "version": "1.0"
    }
}

result = eval_template(template, env)
```

### Template Rules

1. **Substitution Objects**: `{"$": expression}` evaluates expression
2. **Nested Processing**: Templates are processed recursively  
3. **Mixed Content**: Static and dynamic content can be mixed
4. **Type Preservation**: Substituted values maintain their JSON types

## Error Handling

The evaluator provides meaningful error messages:

```python
try:
    result = eval_expr(["undefined-function"], env)
except NameError as e:
    print(f"Function not found: {e}")

try:
    result = eval_expr(["if", "condition"], env)  # Missing branches
except TypeError as e:
    print(f"Invalid expression: {e}")
```

## Implementation Notes

### Tail Call Optimization
The evaluator does not currently implement tail call optimization. Deeply recursive functions may exceed Python's recursion limit.

### Performance Considerations
- Variable lookup is O(depth) where depth is environment chain length
- Function calls create new environment frames
- Template processing is recursive and may be expensive for large templates

### Security
- Evaluation is deterministic with no hidden side effects
- Only built-in functions from the prelude can perform I/O or system operations  
- User code cannot access arbitrary Python objects or modules
