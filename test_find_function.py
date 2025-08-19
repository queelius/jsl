#!/usr/bin/env python3
"""Debug why my-func isn't recognized as operator."""

from jsl.stack_evaluator import StackEvaluator
from jsl.prelude import make_prelude

# Create evaluator
prelude = make_prelude()
evaluator = StackEvaluator(env=prelude.to_dict())

# Add my-func to environment
evaluator.env["my-func"] = {
    'type': 'closure',
    'params': ['n'],
    'body': ['*', 'n', 42],
    'env': {}
}

instructions = [50, 1, 'my-func']
pc = 1  # About to process the arity

# Check the condition
instr = instructions[pc]
next_instr = instructions[pc + 1] if pc + 1 < len(instructions) else None

print(f"Current instruction: {instr}")
print(f"Next instruction: {next_instr}")
print(f"Is current instr int? {isinstance(instr, int)}")
print(f"Is next instr str? {isinstance(next_instr, str)}")
print(f"Next instr in builtins? {next_instr in evaluator.builtins}")
print(f"Next instr in env? {next_instr in evaluator.env}")
print(f"Should be arity-operator pair? {isinstance(instr, int) and pc + 1 < len(instructions) and isinstance(instructions[pc + 1], str) and (instructions[pc + 1] in evaluator.builtins or instructions[pc + 1] in evaluator.env)}")
