#!/usr/bin/env python3
"""Debug resumption issue."""

import json
from jsl.stack_evaluator import StackEvaluator, StackState
from jsl.compiler import compile_to_postfix
from jsl.prelude import make_prelude

# Create evaluator and define user functions
prelude = make_prelude()
evaluator1 = StackEvaluator(env=prelude.to_dict())

# Define user variables and functions
program = [
    "do",
    ["def", "x", 42],
    ["def", "my-func", ["lambda", ["n"], ["*", "n", "x"]]],
]

jpn = compile_to_postfix(program)
evaluator1.eval(jpn)

print("Defined user function 'my-func' that multiplies by x=42")

# Now execute a call to my-func partially
expr = ["my-func", 50]  # Should be 50 * 42 = 2100
jpn2 = compile_to_postfix(expr)

print("\nExpression:", expr)
print("JPN:", jpn2)
print("Expected result: 50 * 42 = 2100")
print()

# First, let's run it to completion to verify it works
full_result = evaluator1.eval(jpn2)
print("Full evaluation result:", full_result)
print()

# Now test partial execution
result, state = evaluator1.eval_partial(jpn2, max_steps=2)
print(f"After 2 steps: result={result}, state saved={state is not None}")

if state:
    state_dict = state.to_dict()
    print(f"  Stack: {state_dict['stack']}")
    print(f"  PC: {state_dict['pc']}")
    print(f"  Instructions: {state_dict['instructions']}")
    
    # Continue execution 
    result2, state2 = evaluator1.eval_partial(jpn2, max_steps=10, state=state)
    print(f"\nAfter continuing: result={result2}, state={state2}")
