#!/usr/bin/env python3
"""Test that resumption now works with user environment."""

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
print()

# Now execute a call to my-func partially
expr = ["my-func", 50]  # Should be 50 * 42 = 2100
jpn2 = compile_to_postfix(expr)

print("Expression:", expr)
print("Expected result: 50 * 42 = 2100")
print()

# Execute partially (1 step)
result, state = evaluator1.eval_partial(jpn2, max_steps=1)

print("After 1 step:")
print("  Result:", result)
print("  State saved:", state is not None)

if state:
    # Check state contents
    state_dict = state.to_dict()
    print("  User env in state:", state_dict.get('user_env', {}).keys())
    
    # Save state as JSON
    json_state = json.dumps(state_dict)
    print("\nState serialized to JSON successfully!")
    
    # Create a fresh evaluator with only prelude
    evaluator2 = StackEvaluator(env=make_prelude().to_dict())
    
    print("\nFresh evaluator created")
    print("  'my-func' in fresh evaluator before restore?", 'my-func' in evaluator2.env)
    
    # Restore state
    restored_state = StackState.from_dict(json.loads(json_state))
    
    # Resume execution
    print("\nResuming execution on fresh evaluator...")
    final_result, _ = evaluator2.eval_partial(jpn2, max_steps=100, state=restored_state)
    
    print("  'my-func' in evaluator after restore?", 'my-func' in evaluator2.env)
    print("  'x' in evaluator after restore?", 'x' in evaluator2.env)
    print("\nFinal result:", final_result)
    
    if final_result == 2100:
        print("✅ SUCCESS! Resumption with user environment works!")
    else:
        print("❌ FAILED: Got", final_result, "expected 2100")