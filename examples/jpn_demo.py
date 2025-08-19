#!/usr/bin/env python3
"""
Demonstration of JSL's JPN (JSL Postfix Notation) and stack-based evaluation.

This example shows:
1. Compilation from S-expressions to JPN
2. Stack-based evaluation with resumption
3. Comparison with recursive evaluation
"""

import json
from jsl.compiler import compile_to_postfix, decompile_from_postfix
from jsl.stack_evaluator import StackEvaluator
from jsl.core import Evaluator, Env
from jsl.prelude import make_prelude


def demonstrate_jpn_compilation():
    """Show how S-expressions compile to JPN."""
    print("=" * 60)
    print("JPN COMPILATION EXAMPLES")
    print("=" * 60)
    
    examples = [
        # Simple arithmetic
        (['+', 2, 3], "Addition"),
        (['-', 10, 4], "Subtraction"),
        (['*', 5, 6], "Multiplication"),
        
        # N-ary operations
        (['+'], "0-arity addition (identity)"),
        (['+', 1], "1-arity addition"),
        (['+', 1, 2, 3, 4], "N-ary addition"),
        (['*'], "0-arity multiplication (identity)"),
        
        # Nested expressions
        (['*', ['+', 2, 3], 4], "Nested: (2 + 3) * 4"),
        (['+', ['*', 2, 3], ['*', 4, 5]], "Complex: (2 * 3) + (4 * 5)"),
        
        # List operations
        (['list'], "Empty list"),
        (['list', '@a', '@b', '@c'], "List creation"),
    ]
    
    for expr, description in examples:
        jpn = compile_to_postfix(expr)
        print(f"\n{description}:")
        print(f"  S-expr: {json.dumps(expr)}")
        print(f"  JPN:    {json.dumps(jpn)}")
        
        # Show decompilation
        back = decompile_from_postfix(jpn)
        print(f"  Back:   {json.dumps(back)}")
        assert back == expr, "Roundtrip failed!"


def demonstrate_evaluation():
    """Compare recursive and stack evaluation."""
    print("\n" + "=" * 60)
    print("EVALUATION COMPARISON")
    print("=" * 60)
    
    # Setup evaluators
    recursive_eval = Evaluator()
    stack_eval = StackEvaluator()
    env = make_prelude()
    
    test_cases = [
        ['+', 2, 3],
        ['*', ['+', 2, 3], 4],
        ['+', 1, 2, 3, 4, 5],
        ['list', '@x', '@y', '@z'],
    ]
    
    print("\n{:<40} {:>10} {:>10}".format("Expression", "Recursive", "Stack"))
    print("-" * 62)
    
    for expr in test_cases:
        # Recursive evaluation
        rec_result = recursive_eval.eval(expr, env)
        
        # Stack evaluation
        jpn = compile_to_postfix(expr)
        stack_result = stack_eval.eval(jpn)
        
        # Display results
        expr_str = json.dumps(expr)
        if len(expr_str) > 38:
            expr_str = expr_str[:35] + "..."
        
        print("{:<40} {:>10} {:>10}".format(
            expr_str,
            str(rec_result)[:10],
            str(stack_result)[:10]
        ))
        
        assert rec_result == stack_result, "Results don't match!"


def demonstrate_resumption():
    """Show resumable execution with the stack evaluator."""
    print("\n" + "=" * 60)
    print("RESUMABLE EXECUTION")
    print("=" * 60)
    
    evaluator = StackEvaluator()
    
    # Create a complex expression that would take many steps
    expr = ['*', 
            ['+', 10, 20, 30],
            ['-', 100, 25, 15]]
    
    print(f"\nExpression: {json.dumps(expr)}")
    
    # Compile to JPN
    jpn = compile_to_postfix(expr)
    print(f"JPN: {json.dumps(jpn)}")
    print(f"Total instructions: {len(jpn)}")
    
    # Execute with limited steps (simulating resource constraints)
    print("\nStep-by-step execution (2 instructions at a time):")
    print("-" * 40)
    
    state = None
    step = 0
    max_steps_per_iteration = 2
    
    while True:
        step += 1
        result, state = evaluator.eval_partial(
            jpn, 
            max_steps=max_steps_per_iteration, 
            state=state
        )
        
        if result is not None:
            print(f"Step {step}: COMPLETE! Result = {result}")
            break
        else:
            print(f"Step {step}: Paused at pc={state.pc}/{len(jpn)}, stack={state.stack}")
            
            # Serialize state (for network transmission or storage)
            state_dict = state.to_dict()
            print(f"         State size: {len(json.dumps(state_dict))} bytes")
    
    print("\nWith recursive evaluation, we couldn't pause mid-computation!")
    print("With JPN and stack evaluation, we can pause and resume anywhere.")


def demonstrate_identity_elements():
    """Show identity elements for n-ary operations."""
    print("\n" + "=" * 60)
    print("IDENTITY ELEMENTS")
    print("=" * 60)
    
    evaluator = StackEvaluator()
    
    identities = [
        (['+'], 0, "Addition identity"),
        (['*'], 1, "Multiplication identity"),
        (['and'], True, "AND identity (all of empty)"),
        (['or'], False, "OR identity (any of empty)"),
        (['list'], [], "Empty list"),
        (['max'], float('-inf'), "Max identity"),
        (['min'], float('inf'), "Min identity"),
    ]
    
    print("\n{:<30} {:<15} {:<20}".format("Expression", "Result", "Description"))
    print("-" * 65)
    
    for expr, expected, description in identities:
        jpn = compile_to_postfix(expr)
        result = evaluator.eval(jpn)
        
        # Format result for display
        result_str = str(result)
        if result == float('-inf'):
            result_str = '-infinity'
        elif result == float('inf'):
            result_str = '+infinity'
        
        print("{:<30} {:<15} {:<20}".format(
            json.dumps(expr),
            result_str,
            description
        ))
        
        assert result == expected, f"Expected {expected}, got {result}"


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("JSL POSTFIX NOTATION (JPN) DEMONSTRATION")
    print("=" * 60)
    
    demonstrate_jpn_compilation()
    demonstrate_evaluation()
    demonstrate_resumption()
    demonstrate_identity_elements()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("""
The JPN format provides:
1. JSON-compatible representation (no tuples, only arrays)
2. Consistent arity encoding (always before operator)
3. Support for identity elements (0-arity operations)
4. Efficient stack-based evaluation
5. True resumption capability for distributed computing

This makes JSL ideal for network-native applications where
computations may need to be paused, transmitted, and resumed
on different machines.
""")


if __name__ == "__main__":
    main()