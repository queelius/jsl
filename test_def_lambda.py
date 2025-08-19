#!/usr/bin/env python3
"""Test what def does with a lambda."""

from jsl.stack_evaluator import StackEvaluator
from jsl.compiler import compile_to_postfix
from jsl.prelude import make_prelude

# Create evaluator
prelude = make_prelude()
evaluator = StackEvaluator(env=prelude.to_dict())

# Define a function
program = [
    "def", "my-func", ["lambda", ["n"], ["*", "n", 42]]
]

jpn = compile_to_postfix(program)
print("Program:", program)
print("JPN:", jpn)

# Execute
result = evaluator.eval(jpn)
print("Result:", result)

# Check what's in the environment
print("\nmy-func in env:", 'my-func' in evaluator.env)
func = evaluator.env.get('my-func')
print("my-func value:", func)
print("my-func type:", type(func))
print("my-func callable?", callable(func))

# Is it JSON serializable?
import json
try:
    json.dumps(func)
    print("✓ JSON serializable")
except TypeError as e:
    print(f"✗ Not JSON serializable: {e}")
