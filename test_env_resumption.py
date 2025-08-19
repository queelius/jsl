#!/usr/bin/env python3
"""Debug environment during resumption."""

import json
from jsl.stack_evaluator import StackEvaluator, StackState
from jsl.compiler import compile_to_postfix
from jsl.prelude import make_prelude

# Create evaluator and define function
prelude = make_prelude()
evaluator1 = StackEvaluator(env=prelude.to_dict())

# Define function
evaluator1.env['my-func'] = {
    'type': 'closure',
    'params': ['n'],
    'body': ['*', 'n', 42],
    'env': {'pi': 3.141592653589793, 'e': 2.718281828459045}
}

# Instructions
instructions = [50, 1, 'my-func']

# Create initial state at PC=1
state = StackState(
    stack=[50],
    pc=1,
    instructions=instructions,
    user_env={'my-func': evaluator1.env['my-func']}
)

print("Initial state:")
print(f"  PC: {state.pc}")
print(f"  Stack: {state.stack}")
print(f"  Instructions: {state.instructions}")
print(f"  User env keys: {list(state.user_env.keys())}")
print()

# Create fresh evaluator
evaluator2 = StackEvaluator(env=prelude.to_dict())
print("Fresh evaluator before resume:")
print(f"  'my-func' in env? {'my-func' in evaluator2.env}")
print()

# Resume execution
print("Resuming execution...")
result, final_state = evaluator2.eval_partial(instructions, max_steps=5, state=state)

print(f"\nAfter resume:")
print(f"  Result: {result}")
if final_state:
    print(f"  Final PC: {final_state.pc}")
    print(f"  Final stack: {final_state.stack}")
    print(f"  'my-func' in env after? {'my-func' in evaluator2.env}")
