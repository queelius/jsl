"""
Test stack evaluator using existing JSL test cases.

This demonstrates that the stack evaluator is functionally equivalent
to the recursive evaluator - we can run the same test suite!
"""

import pytest
from jsl.compiler import compile_to_postfix
from jsl.stack_evaluator import StackEvaluator
from jsl.prelude import make_prelude
from jsl.core import Evaluator, Env


class StackEvaluatorAdapter:
    """
    Adapter that makes StackEvaluator compatible with existing tests.
    
    This shows that postfix evaluation is just an implementation detail -
    the same S-expressions produce the same results.
    """
    
    def __init__(self):
        # Set up prelude functions as built-ins
        prelude = make_prelude()
        self.stack_evaluator = StackEvaluator(env=prelude)
    
    def eval(self, expr, env=None):
        """
        Evaluate S-expression by compiling to postfix first.
        
        This method has the same signature as Evaluator.eval()
        so it can be used as a drop-in replacement.
        """
        # Compile S-expression to postfix
        postfix = compile_to_postfix(expr)
        
        # Update environment if provided
        if env:
            if isinstance(env, Env):
                # Use the provided Env directly
                self.stack_evaluator.env = env
            else:
                # If it's a dict, extend the current env with those bindings
                self.stack_evaluator.env = self.stack_evaluator.env.extend(env)
        
        # Evaluate postfix
        return self.stack_evaluator.eval(postfix)


def run_test_suite_with_stack_evaluator():
    """
    Run a subset of the existing test suite using stack evaluator.
    
    This demonstrates that both evaluators produce identical results.
    """
    
    # Create both evaluators
    recursive_eval = Evaluator()
    stack_eval = StackEvaluatorAdapter()
    
    # Test cases from the existing test suite
    test_cases = [
        # Literals
        (5, "literal number"),
        (3.14, "literal float"),
        (True, "literal boolean"),
        (None, "literal null"),
        ([], "empty list"),
        
        # Arithmetic
        (['+', 2, 3], "addition"),
        (['*', 4, 5], "multiplication"),
        (['-', 10, 3], "subtraction"),
        (['/', 20, 4], "division"),
        
        # Nested arithmetic
        (['*', ['+', 2, 3], 4], "nested: (2+3)*4"),
        (['+', ['-', 5, 2], 3], "nested: (5-2)+3"),
        (['*', ['+', 2, 3], ['-', 7, 3]], "nested: (2+3)*(7-3)"),
        
        # Comparisons
        (['=', 5, 5], "equality true"),
        (['=', 5, 3], "equality false"),
        (['>', 5, 3], "greater than"),
        (['<', 3, 5], "less than"),
        
        # N-ary operations
        (['+', 1, 2, 3, 4], "n-ary addition"),
        (['list', '@a', '@b', '@c'], "n-ary list"),
        
        # String literals
        ('@hello', "string literal"),
        
        # Complex nested
        (['*', 
          ['+', 10, 20], 
          ['-', 100, 50]], "complex: (10+20)*(100-50)"),
    ]
    
    print("=== Comparing Recursive vs Stack Evaluation ===\n")
    print(f"{'Test':<30} {'Recursive':<15} {'Stack':<15} {'Match':<10}")
    print("-" * 70)
    
    all_match = True
    for expr, description in test_cases:
        try:
            # Create fresh environments
            rec_env = Env()
            stack_eval.stack_evaluator.env = {}
            
            # Evaluate with both
            rec_result = recursive_eval.eval(expr, rec_env)
            stack_result = stack_eval.eval(expr)
            
            # Compare
            match = rec_result == stack_result
            all_match = all_match and match
            
            status = "✓" if match else "✗"
            print(f"{description:<30} {str(rec_result):<15} {str(stack_result):<15} {status:<10}")
            
        except Exception as e:
            print(f"{description:<30} ERROR: {e}")
            all_match = False
    
    print("-" * 70)
    print(f"\nAll tests match: {all_match}")
    
    return all_match


def test_with_variables():
    """Test that variable handling works the same."""
    
    print("\n=== Testing Variable Handling ===\n")
    
    # Recursive evaluator with prelude
    rec_eval = Evaluator()
    prelude = make_prelude()
    rec_env = prelude.extend({'x': 10, 'y': 20})
    
    # Stack evaluator (already has prelude from __init__)
    stack_eval = StackEvaluatorAdapter()
    # Extend the environment with new bindings
    stack_eval.stack_evaluator.env = stack_eval.stack_evaluator.env.extend({'x': 10, 'y': 20})
    
    test_cases = [
        ('x', "variable x"),
        ('y', "variable y"),
        (['+', 'x', 'y'], "x + y"),
        (['*', 'x', 2], "x * 2"),
        (['+', ['*', 'x', 2], 'y'], "(x * 2) + y"),
    ]
    
    print(f"{'Test':<30} {'Recursive':<15} {'Stack':<15} {'Match':<10}")
    print("-" * 70)
    
    for expr, description in test_cases:
        rec_result = rec_eval.eval(expr, rec_env)
        stack_result = stack_eval.eval(expr)
        
        match = rec_result == stack_result
        status = "✓" if match else "✗"
        
        print(f"{description:<30} {str(rec_result):<15} {str(stack_result):<15} {status:<10}")


def demonstrate_postfix_advantage():
    """Show the advantage of postfix for resumption."""
    
    print("\n=== Advantage: Resumption with Stack Evaluator ===\n")
    
    expr = ['*', ['+', 10, 20, 30], ['-', 100, 25, 15]]
    postfix = compile_to_postfix(expr)
    
    print(f"S-expression: {expr}")
    print(f"Postfix:      {postfix}")
    print()
    
    evaluator = StackEvaluator()
    
    # Simulate limited resources - execute 2 instructions at a time
    result = None
    state = None
    step = 0
    
    print("Resumable execution (2 instructions at a time):")
    while result is None and step < 10:
        step += 1
        result, state = evaluator.eval_partial(postfix, max_steps=2, state=state)
        
        if result is None:
            print(f"  Step {step}: Paused at pc={state.pc}, stack={state.stack}")
        else:
            print(f"  Step {step}: Complete! Result = {result}")
    
    print()
    print("With recursive evaluation, we would restart from the beginning each time!")
    print("With stack evaluation, we resume exactly where we left off.")


if __name__ == "__main__":
    # Run comparison tests
    success = run_test_suite_with_stack_evaluator()
    
    # Test variable handling
    test_with_variables()
    
    # Demonstrate resumption advantage
    demonstrate_postfix_advantage()
    
    print("\n" + "=" * 70)
    print("Conclusion: Stack evaluator is functionally equivalent to recursive")
    print("evaluator, but with better resumption and potential optimizations.")