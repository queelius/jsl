"""
Compiler from JSL S-expressions to JPN (JSL Postfix Notation).

This module converts JSL's S-expression format to JPN - a postfix notation
that serves as both human-readable documentation and machine-executable instructions.

JPN (JSL Postfix Notation) is:
- Still JSON (network-transmittable)
- Still readable (not raw bytecode)
- Stack-oriented (efficient execution)
- Resumable (can pause/restore state)

The progression: S-expressions → JPN → Stack Machine execution
"""

from typing import List, Any, Union
from .stack_special_forms import detect_special_form, Opcode


def compile_to_postfix(expr: Any) -> List[Any]:
    """
    Compile a JSL S-expression to JPN (JSL Postfix Notation).
    
    Examples:
        ['+', 2, 3]           → [2, 3, '+']        # Binary (no arity needed)
        ['*', 2, ['+', 1, 2]] → [2, 1, 2, '+', '*'] # Nested binary ops
        ['+', 1, 2, 3, 4]     → [1, 2, 3, 4, 4, '+'] # N-ary (arity before op)
        ['+']                 → [0, '+']           # 0-arity
        ['list', 'a', 'b']    → ['a', 'b', 2, 'list'] # List creation
        
    Args:
        expr: S-expression in JSL format
        
    Returns:
        JPN - list of instructions in postfix order (JSON-compatible)
    """
    result = []
    
    def compile_expr(e):
        """Recursively compile expression, appending to result."""
        if isinstance(e, (int, float, bool, type(None))):
            # Literals are pushed directly
            result.append(e)
        elif isinstance(e, str):
            # Strings could be variables or operators
            # For now, just push them
            result.append(e)
        elif isinstance(e, list) and len(e) > 0:
            # Check if this is a special form that needs special handling
            if detect_special_form(e):
                # Special forms can't be compiled to regular postfix
                # because they have special evaluation rules
                result.append(Opcode.SPECIAL_FORM)
                result.append(e)
            else:
                # Regular S-expression: [operator, arg1, arg2, ...]
                op = e[0]
                args = e[1:]
                
                # If operator is itself a list (like [["lambda", ...], arg]), compile it too
                if isinstance(op, list):
                    # Compile the operator expression
                    compile_expr(op)
                    # Compile all arguments
                    for arg in args:
                        compile_expr(arg)
                    # Use special APPLY marker
                    result.append(len(args))
                    result.append('__apply__')
                else:
                    # Regular operator - compile arguments first
                    for arg in args:
                        compile_expr(arg)
                    
                    # Always append arity before operator for consistency
                    result.append(len(args))
                    result.append(op)
        elif isinstance(e, list) and len(e) == 0:
            # Empty list - use special marker with arity format
            result.append(0)
            result.append('__empty_list__')
        elif isinstance(e, dict):
            # Dictionary literal - compile keys and values
            # Push each key-value pair, then use __dict__ operator
            for key, value in e.items():
                compile_expr(key)  # Compile key expression
                compile_expr(value)  # Compile value expression
            result.append(len(e) * 2)  # Total number of items (keys + values)
            result.append('__dict__')  # Dictionary creation operator
        else:
            # Other types - push as-is
            result.append(e)
    
    compile_expr(expr)
    return result


def decompile_from_postfix(postfix: List[Any]) -> Any:
    """
    Convert JPN back to S-expression (for debugging/display).
    
    This is the inverse of compile_to_postfix:
    compile_to_postfix(decompile_from_postfix(jpn)) == jpn
    
    Args:
        postfix: List of JPN instructions
        
    Returns:
        Equivalent S-expression
        
    Examples:
        [2, 3, 2, '+'] → ['+', 2, 3]
        [1, 2, 3, 3, '+'] → ['+', 1, 2, 3]
        ['x', 'y', 2, '+'] → ['+', 'x', 'y']
        [0, '+'] → ['+']  # 0-arity addition
    """
    stack = []
    i = 0
    
    # Set of known operators (anything that can be an operator)
    operators = {'+', '-', '*', '/', '%', '=', '!=', '<', '>', '<=', '>=',
                 'and', 'or', 'not', 'cons', 'append', 'first', 'rest', 
                 'length', 'str-length', 'list', 'if', 'lambda', 'let', 
                 'def', 'quote', '@', 'do', '__empty_list__'}
    
    while i < len(postfix):
        item = postfix[i]
        
        # Check if this could be an arity (number followed by operator)
        if isinstance(item, int) and i + 1 < len(postfix) and postfix[i + 1] in operators:
            # This is an arity-operator pair
            arity = item
            operator = postfix[i + 1]
            i += 2  # Skip both arity and operator
            
            # Pop arguments from stack
            if len(stack) < arity:
                raise ValueError(f"Stack underflow: {operator} needs {arity} args, have {len(stack)}")
            
            args = []
            for _ in range(arity):
                args.insert(0, stack.pop())
            
            # Create S-expression or handle special cases
            if operator == '__empty_list__' and arity == 0:
                # Special case: empty list
                stack.append([])
            elif arity == 0:
                stack.append([operator])
            else:
                stack.append([operator] + args)
        else:
            # It's a literal or variable - push to stack
            stack.append(item)
            i += 1
    
    if len(stack) != 1:
        raise ValueError(f"Invalid JPN: expected 1 item on stack, have {len(stack)}: {stack}")
    
    return stack[0]


def validate_roundtrip(expr: Any) -> bool:
    """
    Validate that an expression can be compiled and decompiled correctly.
    
    Args:
        expr: S-expression to validate
        
    Returns:
        True if expr == decompile(compile(expr))
    """
    try:
        postfix = compile_to_postfix(expr)
        back = decompile_from_postfix(postfix)
        return expr == back
    except Exception:
        return False


# Test the compiler
if __name__ == "__main__":
    test_cases = [
        # Simple binary operations
        (['+', 2, 3], [2, 3, '+']),
        (['*', 2, 3], [2, 3, '*']),
        
        # Nested operations
        (['*', 2, ['+', 1, 2]], [2, 1, 2, '+', '*']),
        (['+', ['-', 5, 2], 3], [5, 2, '-', 3, '+']),
        
        # N-ary operations
        (['+', 1, 2, 3, 4], [1, 2, 3, 4, ('+', 4)]),
        
        # Complex nesting
        (['*', ['+', 2, 3], ['-', 7, 3]], [2, 3, '+', 7, 3, '-', '*']),
        
        # Literals
        (5, [5]),
        ("x", ["x"]),
        ([], [[]]),
        
        # Boolean operations
        (['=', 5, 5], [5, 5, '=']),
        (['not', ['=', 1, 2]], [1, 2, '=', ('not', 1)]),
    ]
    
    print("=== S-Expression to Postfix Compiler ===\n")
    
    for sexpr, expected in test_cases:
        result = compile_to_postfix(sexpr)
        status = "✓" if result == expected else "✗"
        print(f"{status} {sexpr}")
        print(f"  → {result}")
        if result != expected:
            print(f"  Expected: {expected}")
        
        # Test round-trip
        try:
            back = decompile_from_postfix(result)
            if back != sexpr and not (isinstance(sexpr, (int, float, str)) and back == sexpr):
                print(f"  ⚠ Round-trip: {back}")
        except Exception as e:
            print(f"  ⚠ Decompile failed: {e}")
        print()