#!/usr/bin/env python3
"""Debug with modified evaluator."""

import os
os.environ['DEBUG_EVAL'] = '1'

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
    'env': {}
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

# Create fresh evaluator
evaluator2 = StackEvaluator(env=prelude.to_dict())

# Resume execution
result, final_state = evaluator2.eval_partial(instructions, max_steps=5, state=state)

print(f"Result: {result}")
if final_state:
    print(f"Final PC: {final_state.pc}")
    print(f"Final stack: {final_state.stack}")
