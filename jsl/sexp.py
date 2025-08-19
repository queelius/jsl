"""
S-expression notation converter for JSL.

This module provides conversion between JSL's JSON array notation and
traditional Lisp-style S-expressions, making JSL a pedagogical tool for
understanding the full space of program representations:

1. Human-readable: (+ 1 2) - Traditional S-expressions
2. JSON source: ["+", 1, 2] - Network-serializable source
3. Stack bytecode: [1, 2, "+"] - Resumable execution format

The key insight: Code mobility isn't just about moving source code,
but about moving computation state - pausing execution here, resuming there.
"""

import re
from typing import Any, List, Union, Dict


# Unicode symbol mappings for elegant mathematical notation
UNICODE_SYMBOLS = {
    # Lambda and function-related
    "lambda": "λ",      # Greek lambda
    "fn": "ƒ",          # Function symbol
    
    # Definition and binding
    "def": "≝",         # Definition (equal by definition)
    "define": "≜",      # Alternative definition
    "let": "∷",         # Type annotation / binding
    
    # Arithmetic operators
    "+": "+",           # Keep standard (or could use ⊕)
    "-": "−",           # Minus sign (not hyphen)
    "*": "×",           # Multiplication sign
    "/": "÷",           # Division sign
    "%": "mod",         # Modulo
    
    # Comparison operators
    "=": "≡",           # Equivalence
    "!=": "≠",          # Not equal
    "<": "<",           # Keep standard
    ">": ">",           # Keep standard
    "<=": "≤",          # Less than or equal
    ">=": "≥",          # Greater than or equal
    
    # Logical operators
    "not": "¬",         # Logical NOT
    "and": "∧",         # Logical AND
    "or": "∨",          # Logical OR
    
    # List operations
    "cons": "∷",        # Cons (list construction)
    "append": "⊕",      # Append/concatenation
    "first": "↑",       # Head/first
    "rest": "↓",        # Tail/rest
    "nil": "∅",         # Empty/nil
    
    # Special forms
    "if": "⇒",          # Implication/conditional
    "quote": "′",       # Prime for quotation
    "@": "′",           # Alternative quote
    "do": "⟦⟧",         # Block/sequence markers
    
    # Type-related (future)
    "int": "ℤ",         # Integers
    "float": "ℝ",       # Reals
    "bool": "𝔹",        # Booleans
    "string": "Σ",      # Strings
    
    # Set operations (future)
    "union": "∪",       # Set union
    "intersect": "∩",   # Set intersection
    "member": "∈",      # Set membership
    
    # Arrow notations
    "->": "→",          # Function arrow
    "=>": "⇒",          # Implication
    "<-": "←",          # Reverse arrow
    
    # Other mathematical symbols
    "infinity": "∞",    # Infinity
    "sum": "Σ",         # Summation
    "product": "Π",     # Product
    "forall": "∀",      # Universal quantifier
    "exists": "∃",      # Existential quantifier
}

# Reverse mapping for parsing
UNICODE_TO_JSL = {v: k for k, v in UNICODE_SYMBOLS.items() if v != k}


def to_canonical_sexp(expr: Any, use_unicode: bool = False) -> str:
    """
    Convert JSL expression to canonical S-expression notation.
    
    Examples:
        Standard:
        ["+", 1, 2] → "(+ 1 2)"
        ["lambda", ["x", "y"], ["+", "x", "y"]] → "(lambda (x y) (+ x y))"
        
        With Unicode:
        ["+", 1, 2] → "(+ 1 2)"
        ["*", 2, 3] → "(× 2 3)"
        ["lambda", ["x", "y"], ["*", "x", "y"]] → "(λ (x y) (× x y))"
        ["def", "x", 5] → "(≝ x 5)"
        
    Args:
        expr: JSL expression (JSON array format)
        use_unicode: Whether to use Unicode symbols
        
    Returns:
        String in canonical S-expression notation
    """
    if expr is None:
        return "nil"
    elif isinstance(expr, bool):
        return "#t" if expr else "#f"
    elif isinstance(expr, (int, float)):
        return str(expr)
    elif isinstance(expr, str):
        # Quote strings that need it
        if expr.startswith("@"):
            # String literal
            return f'"{expr[1:]}"'
        elif needs_quoting(expr):
            # Symbol with special chars
            return f"|{expr}|"
        else:
            # Regular symbol - possibly convert to Unicode
            if use_unicode and expr in UNICODE_SYMBOLS:
                return UNICODE_SYMBOLS[expr]
            return expr
    elif isinstance(expr, list):
        if len(expr) == 0:
            return "()"
        
        # Special handling for certain forms
        op = expr[0] if expr else None
        
        # Get the operator symbol (Unicode or standard)
        op_symbol = op
        if use_unicode and isinstance(op, str) and op in UNICODE_SYMBOLS:
            op_symbol = UNICODE_SYMBOLS[op]
        
        if op == "lambda" and len(expr) == 3:
            # (lambda (params...) body) or (λ (params...) body)
            params = to_canonical_sexp(expr[1], use_unicode)
            # Remove outer parens if params is already a list
            if params.startswith("(") and params.endswith(")"):
                params_str = params
            else:
                params_str = f"({params})"
            body = to_canonical_sexp(expr[2], use_unicode)
            return f"({op_symbol} {params_str} {body})"
        
        elif op == "let" and len(expr) == 3:
            # (let ((var val)) body)
            binding = expr[1]
            if isinstance(binding, list) and len(binding) == 2:
                var = to_canonical_sexp(binding[0], use_unicode)
                val = to_canonical_sexp(binding[1], use_unicode)
                body = to_canonical_sexp(expr[2], use_unicode)
                return f"({op_symbol} (({var} {val})) {body})"
            else:
                # Fallback to regular list handling
                parts = [to_canonical_sexp(e, use_unicode) for e in expr]
                return f"({' '.join(parts)})"
        
        elif op == "def" and len(expr) == 3:
            # (define var val) or (≝ var val)
            var = to_canonical_sexp(expr[1], use_unicode)
            val = to_canonical_sexp(expr[2], use_unicode)
            if use_unicode:
                return f"({op_symbol} {var} {val})"
            else:
                return f"(define {var} {val})"
        
        elif op == "quote" or op == "@":
            # (quote expr) or 'expr or ′expr
            if len(expr) == 2:
                quoted = to_canonical_sexp(expr[1], use_unicode)
                if use_unicode:
                    return f"′{quoted}"  # Unicode prime
                else:
                    return f"'{quoted}"
        
        # Default list handling
        parts = [to_canonical_sexp(e, use_unicode) for e in expr]
        return f"({' '.join(parts)})"
    
    elif isinstance(expr, dict):
        # Dictionary as association list
        pairs = []
        for k, v in expr.items():
            pairs.append(f"({to_canonical_sexp(k)} . {to_canonical_sexp(v)})")
        return f"({' '.join(pairs)})"
    
    else:
        # Unknown type - convert to string
        return str(expr)


def from_canonical_sexp(sexp: str) -> Any:
    """
    Parse canonical S-expression notation to JSL expression.
    
    Examples:
        "(+ 1 2)" → ["+", 1, 2]
        "(* (+ 2 3) 4)" → ["*", ["+", 2, 3], 4]
        "(lambda (x y) (+ x y))" → ["lambda", ["x", "y"], ["+", "x", "y"]]
        
    Args:
        sexp: String in S-expression notation
        
    Returns:
        JSL expression (JSON-serializable)
    """
    tokens = tokenize_sexp(sexp)
    result, remaining = parse_expr(tokens)
    
    if remaining:
        raise ValueError(f"Unexpected tokens after expression: {remaining}")
    
    return result


def tokenize_sexp(sexp: str) -> List[str]:
    """
    Tokenize S-expression string.
    
    Args:
        sexp: S-expression string
        
    Returns:
        List of tokens
    """
    # Token patterns
    patterns = [
        r'\(',                    # Open paren
        r'\)',                    # Close paren
        r"'",                     # Quote
        r'"[^"]*"',              # String literal
        r'\|[^|]*\|',            # Quoted symbol
        r'#[tf]',                # Boolean
        r'[+-]?\d+\.\d+',        # Float
        r'[+-]?\d+',             # Integer
        r'[^\s()]+',             # Symbol
    ]
    
    pattern = '|'.join(f'({p})' for p in patterns)
    tokens = []
    
    for match in re.finditer(pattern, sexp):
        token = match.group()
        if token and not token.isspace():
            tokens.append(token)
    
    return tokens


def parse_expr(tokens: List[str]) -> tuple[Any, List[str]]:
    """
    Parse tokens into JSL expression.
    
    Args:
        tokens: List of tokens
        
    Returns:
        Tuple of (expression, remaining_tokens)
    """
    if not tokens:
        raise ValueError("Empty token list")
    
    token = tokens[0]
    rest = tokens[1:]
    
    # Handle different token types
    if token == '(':
        # Parse list
        elements = []
        rest = rest
        
        while rest and rest[0] != ')':
            elem, rest = parse_expr(rest)
            elements.append(elem)
        
        if not rest or rest[0] != ')':
            raise ValueError("Missing closing parenthesis")
        
        rest = rest[1:]  # Skip closing paren
        
        # Handle special forms
        if elements and elements[0] == "define":
            # Convert define to def
            elements[0] = "def"
        elif elements and elements[0] == "lambda" and len(elements) == 3:
            # Lambda is already in correct format
            pass
        
        return elements, rest
    
    elif token == "'":
        # Quote
        if not rest:
            raise ValueError("Quote without expression")
        quoted, rest = parse_expr(rest)
        return ["quote", quoted], rest
    
    elif token.startswith('"') and token.endswith('"'):
        # String literal
        content = token[1:-1]
        return f"@{content}", rest
    
    elif token.startswith('|') and token.endswith('|'):
        # Quoted symbol
        content = token[1:-1]
        return content, rest
    
    elif token == '#t':
        return True, rest
    
    elif token == '#f':
        return False, rest
    
    elif token == 'nil':
        return None, rest
    
    else:
        # Try to parse as number
        try:
            if '.' in token:
                return float(token), rest
            else:
                return int(token), rest
        except ValueError:
            # It's a symbol
            return token, rest


def needs_quoting(symbol: str) -> bool:
    """Check if a symbol needs quoting in S-expression notation."""
    special_chars = set('()[]{}"|\\;,`\'')
    return any(c in special_chars for c in symbol) or ' ' in symbol


def format_sexp(sexp: str, indent: int = 2) -> str:
    """
    Pretty-print S-expression with indentation.
    
    Args:
        sexp: S-expression string
        indent: Spaces per indent level
        
    Returns:
        Formatted S-expression
    """
    # This is a simple formatter - could be enhanced
    level = 0
    result = []
    i = 0
    
    while i < len(sexp):
        char = sexp[i]
        
        if char == '(':
            if i > 0 and sexp[i-1] not in ' \n(':
                result.append(' ')
            result.append('(')
            level += 1
            
        elif char == ')':
            level -= 1
            result.append(')')
            
        else:
            result.append(char)
        
        i += 1
    
    return ''.join(result)


# Comparison table generator
def generate_representation_table():
    """
    Generate a comparison table of different representations.
    
    This shows the pedagogical value of JSL in understanding
    the full space of program representations.
    """
    examples = [
        # (Description, JSL, Canonical, Postfix)
        ("Addition", ["+", 2, 3], "(+ 2 3)", [2, 3, "+"]),
        ("Nested", ["*", ["+", 2, 3], 4], "(* (+ 2 3) 4)", [2, 3, "+", 4, "*"]),
        ("Lambda", ["lambda", ["x"], ["*", "x", 2]], "(lambda (x) (* x 2))", "N/A"),
        ("Let", ["let", ["x", 5], ["*", "x", 2]], "(let ((x 5)) (* x 2))", "N/A"),
        ("List", ["list", 1, 2, 3], "(list 1 2 3)", [1, 2, 3, ("list", 3)]),
        ("Empty", [], "()", [("__empty_list__", 0)]),
        ("Variable", ["+", "x", "y"], "(+ x y)", ["x", "y", "+"]),
    ]
    
    print("="*80)
    print("JSL: A Rosetta Stone for Program Representations")
    print("="*80)
    print()
    print("JSL serves as a pedagogical bridge between different program representations,")
    print("from human-readable S-expressions to network-mobile JSON to resumable bytecode.")
    print()
    print(f"{'Description':<15} {'JSON (JSL)':<25} {'S-Expression':<20} {'Postfix':<25}")
    print("-"*85)
    
    for desc, jsl, canonical, postfix in examples:
        jsl_str = str(jsl)[:23]
        canonical_str = canonical[:18]
        postfix_str = str(postfix)[:23] if isinstance(postfix, list) else postfix
        
        print(f"{desc:<15} {jsl_str:<25} {canonical_str:<20} {postfix_str:<25}")
    
    print()
    print("Key Insights:")
    print("1. JSON (JSL): Network-serializable, universal data format")
    print("2. S-Expression: Human-readable, minimal syntax")
    print("3. Postfix: Machine-executable, resumable computation")
    print()
    print("The progression from S-expr → JSON → Postfix represents increasing")
    print("machine-friendliness and decreasing human-readability, while maintaining")
    print("semantic equivalence.")


# Demo functions
def demonstrate_conversions():
    """Demonstrate conversions between representations."""
    
    print("\n=== Representation Conversions ===\n")
    
    test_cases = [
        ["+", 1, 2],
        ["*", ["+", 2, 3], ["-", 10, 6]],
        ["lambda", ["x", "y"], ["+", "x", "y"]],
        ["let", ["x", 10], ["*", "x", "x"]],
        ["if", ["=", "x", 0], "@zero", "@nonzero"],
        ["list", 1, 2, 3, 4, 5],
        ["def", "factorial", ["lambda", ["n"], 
            ["if", ["=", "n", 0], 1, ["*", "n", ["factorial", ["-", "n", 1]]]]]],
    ]
    
    print("Standard S-expressions:")
    print("-" * 60)
    for jsl_expr in test_cases[:3]:
        canonical = to_canonical_sexp(jsl_expr, use_unicode=False)
        print(f"  {str(jsl_expr)[:30]:<32} → {canonical}")
    
    print("\nUnicode S-expressions:")
    print("-" * 60)
    for jsl_expr in test_cases[:3]:
        unicode_sexp = to_canonical_sexp(jsl_expr, use_unicode=True)
        print(f"  {str(jsl_expr)[:30]:<32} → {unicode_sexp}")
    
    print("\nMore Unicode examples:")
    print("-" * 60)
    
    examples = [
        (["*", 2, 3], "(× 2 3)"),
        (["<=", "x", 10], "(≤ x 10)"),
        (["!=", "a", "b"], "(≠ a b)"),
        (["not", ["=", "x", "y"]], "(¬ (≡ x y))"),
        (["and", "p", "q"], "(∧ p q)"),
        (["or", "p", "q"], "(∨ p q)"),
        (["def", "x", 42], "(≝ x 42)"),
        (["lambda", ["x"], ["*", "x", "x"]], "(λ (x) (× x x))"),
    ]
    
    for jsl_expr, expected in examples:
        result = to_canonical_sexp(jsl_expr, use_unicode=True)
        match = "✓" if result == expected else "✗"
        print(f"  {str(jsl_expr)[:30]:<32} → {result:<20} {match}")
    print()


def demonstrate_mobility():
    """
    Demonstrate the concept of computation mobility.
    
    Shows how postfix representation enables moving not just code,
    but computation state across network boundaries.
    """
    print("\n=== Computation Mobility ===\n")
    print("Traditional: Move code, restart execution")
    print("JSL Vision: Move computation state, resume execution\n")
    
    from jsl.compiler import compile_to_postfix
    
    # Example computation
    expr = ["*", ["+", 10, 20], ["-", 100, 50]]
    postfix = compile_to_postfix(expr)
    
    print(f"Original: {to_canonical_sexp(expr)}")
    print(f"Postfix:  {postfix}")
    print()
    
    # Simulate partial execution
    print("Machine A: Execute partially...")
    partial_stack = [30, 100]  # After computing (+ 10 20)
    remaining = [50, "-", "*"]
    
    print(f"  Stack: {partial_stack}")
    print(f"  Remaining: {remaining}")
    print()
    
    print("--- Network Transfer ---")
    state = {
        "stack": partial_stack,
        "code": remaining,
        "pc": 0
    }
    print(f"  Serialized state: {state}")
    print()
    
    print("Machine B: Resume execution...")
    print(f"  Continue from: {partial_stack + remaining}")
    print(f"  Final result: 1500")
    print()
    
    print("This is the key insight: We're not just moving code (data),")
    print("we're moving suspended computation (code + state).")
    print("The stack-based representation makes this natural and efficient.")


def demonstrate_unicode_beauty():
    """Show the elegance of Unicode mathematical notation."""
    
    print("\n=== The Beauty of Unicode Mathematical Notation ===\n")
    
    print("Traditional Lisp vs Unicode S-expressions:\n")
    
    examples = [
        ("Simple arithmetic",
         ["*", ["+", 2, 3], ["-", 10, 6]],
         "(* (+ 2 3) (- 10 6))",
         "(× (+ 2 3) (− 10 6))"),
        
        ("Lambda calculus",
         ["lambda", ["x", "y"], ["*", "x", "y"]],
         "(lambda (x y) (* x y))",
         "(λ (x y) (× x y))"),
        
        ("Definition",
         ["def", "square", ["lambda", ["x"], ["*", "x", "x"]]],
         "(define square (lambda (x) (* x x)))",
         "(≝ square (λ (x) (× x x)))"),
        
        ("Logical expression",
         ["and", ["not", "p"], ["or", "q", "r"]],
         "(and (not p) (or q r))",
         "(∧ (¬ p) (∨ q r))"),
        
        ("Comparison",
         ["if", ["<=", "x", 10], ["=", "x", 10], ["!=", "x", 10]],
         "(if (<= x 10) (= x 10) (!= x 10))",
         "(⇒ (≤ x 10) (≡ x 10) (≠ x 10))"),
    ]
    
    for desc, jsl, traditional, unicode in examples:
        print(f"{desc}:")
        print(f"  JSL:         {jsl}")
        print(f"  Traditional: {traditional}")
        print(f"  Unicode:     {unicode}")
        print()
    
    print("Mathematical Symbols Available:")
    print("-" * 60)
    
    categories = [
        ("Functions", ["λ (lambda)", "ƒ (function)", "→ (arrow)"]),
        ("Logic", ["¬ (not)", "∧ (and)", "∨ (or)", "⇒ (implies)"]),
        ("Arithmetic", ["× (multiply)", "÷ (divide)", "− (minus)"]),
        ("Comparison", ["≡ (equal)", "≠ (not equal)", "≤ (less-equal)", "≥ (greater-equal)"]),
        ("Quantifiers", ["∀ (forall)", "∃ (exists)", "∈ (member)"]),
        ("Sets", ["∪ (union)", "∩ (intersect)", "∅ (empty)"]),
    ]
    
    for category, symbols in categories:
        print(f"  {category:12} {', '.join(symbols)}")
    
    print("\nThe Unicode notation brings JSL closer to mathematical notation,")
    print("making programs look like the equations they represent.")


if __name__ == "__main__":
    # Generate comparison table
    generate_representation_table()
    
    # Demonstrate conversions
    demonstrate_conversions()
    
    # Show Unicode beauty
    demonstrate_unicode_beauty()
    
    # Demonstrate computation mobility
    demonstrate_mobility()
    
    print("\n✨ JSL: Where code is data, data is code, and computation is mobile.")