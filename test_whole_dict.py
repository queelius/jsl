#!/usr/bin/env python3
"""Test with the whole flow."""

from jsl.stack_evaluator import StackEvaluator
from jsl.compiler import compile_to_postfix
from jsl.prelude import make_prelude

# Create evaluator 
prelude = make_prelude()
evaluator = StackEvaluator(env=prelude.to_dict())

# Define my-func using def
program = ["def", "my-func", ["lambda", ["n"], ["*", "n", 42]]]
jpn = compile_to_postfix(program)
print("Define program:", program)
print("Define JPN:", jpn)
result = evaluator.eval(jpn)
print("Define result:", result)
print()

# Check what's in env
print("my-func in env?", "my-func" in evaluator.env)
func = evaluator.env.get("my-func")
print("my-func value:", func)
print()

# Now call it
call_expr = ["my-func", 50]
call_jpn = compile_to_postfix(call_expr)
print("Call expression:", call_expr)
print("Call JPN:", call_jpn)

result = evaluator.eval(call_jpn)
print("Call result:", result)
