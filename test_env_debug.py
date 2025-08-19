#!/usr/bin/env python3
"""Debug environment saving."""

import json
from jsl.stack_evaluator import StackEvaluator, StackState
from jsl.compiler import compile_to_postfix
from jsl.prelude import make_prelude

# Create evaluator with prelude
prelude = make_prelude()
evaluator = StackEvaluator(env=prelude.to_dict())

# Check what's in the prelude initially
print("Prelude functions (first 10):", list(evaluator.env.keys())[:10])
print("All prelude are callable?", all(callable(v) for v in evaluator.env.values()))
print()

# Define user variables
evaluator.env["x"] = 42
evaluator.env["my-func"] = {
    "type": "closure",
    "params": ["n"],
    "body": ["*", "n", "x"],
    "env": {"x": 42}
}

print("After adding user definitions:")
print("  'x' in env:", 'x' in evaluator.env)
print("  'x' value:", evaluator.env.get('x'))
print("  'my-func' in env:", 'my-func' in evaluator.env)
print("  'my-func' value:", evaluator.env.get('my-func'))
print()

# Try partial execution to trigger state save
expr = ["my-func", 50]
jpn = compile_to_postfix(expr)
print("Expression:", expr)
print("JPN:", jpn)

result, state = evaluator.eval_partial(jpn, max_steps=1)

if state:
    state_dict = state.to_dict()
    print("\nState dict keys:", state_dict.keys())
    print("user_env in state:", state_dict.get('user_env'))
    
    # Check what the filter logic does
    print("\nDebugging filter logic:")
    for key, value in evaluator.env.items():
        if key in ['x', 'my-func', '+', 'map']:  # Sample of user and prelude
            is_callable = callable(value)
            is_dict = isinstance(value, dict)
            included = not callable(value) or isinstance(value, dict)
            print(f"  {key}: callable={is_callable}, dict={is_dict}, included={included}")