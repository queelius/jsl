#!/usr/bin/env python3
"""Step-by-step execution."""

import json
from jsl.stack_evaluator import StackEvaluator, StackState
from jsl.compiler import compile_to_postfix
from jsl.prelude import make_prelude

# Create evaluator and define user functions
prelude = make_prelude()
evaluator = StackEvaluator(env=prelude.to_dict())

# Define user variables and functions
evaluator.env["x"] = 42
evaluator.env["my-func"] = {
    'type': 'closure',
    'params': ['n'],
    'body': ['*', 'n', 'x'],
    'env': {'x': 42}  # Only user env
}

# Now execute a call to my-func
expr = ["my-func", 50]  # Should be 50 * 42 = 2100
jpn = compile_to_postfix(expr)

print("Expression:", expr)
print("JPN:", jpn)
print()

# Step through execution
state = None
for step in range(10):
    result, state = evaluator.eval_partial(jpn, max_steps=1, state=state)
    if state:
        print(f"Step {step + 1}:")
        print(f"  Stack: {state.stack}")
        print(f"  PC: {state.pc}/{len(state.instructions)}")
        print(f"  Next instr: {state.instructions[state.pc] if state.pc < len(state.instructions) else 'END'}")
    else:
        print(f"Step {step + 1}: DONE - Result = {result}")
        break
