#!/usr/bin/env python3
"""Test full state save/restore."""

import json
from jsl.stack_evaluator import StackEvaluator, StackState
from jsl.compiler import compile_to_postfix
from jsl.prelude import make_prelude

# First evaluator - define function
prelude1 = make_prelude()
evaluator1 = StackEvaluator(env=prelude1.to_dict())

# Define my-func
program = ["def", "my-func", ["lambda", ["n"], ["*", "n", 42]]]
jpn = compile_to_postfix(program)
evaluator1.eval(jpn)

print("Function defined in evaluator1")
print()

# Call function with limited steps
call_expr = ["my-func", 50]
call_jpn = compile_to_postfix(call_expr)

result, state = evaluator1.eval_partial(call_jpn, max_steps=1)
print(f"After 1 step: result={result}")
if state:
    state_dict = state.to_dict()
    print(f"  State: PC={state_dict['pc']}, stack={state_dict['stack']}")
    print(f"  User env keys: {list(state_dict.get('user_env', {}).keys())}")
    
    # Serialize state
    json_str = json.dumps(state_dict)
    print(f"  Serialized OK: {len(json_str)} bytes")
    
    # Create new evaluator
    prelude2 = make_prelude()
    evaluator2 = StackEvaluator(env=prelude2.to_dict())
    
    print("\nNew evaluator created")
    print(f"  'my-func' in evaluator2 before restore? {'my-func' in evaluator2.env}")
    
    # Restore state
    state2 = StackState.from_dict(json.loads(json_str))
    
    # Continue execution
    result2, final_state = evaluator2.eval_partial(call_jpn, max_steps=100, state=state2)
    print(f"\nAfter resuming:")
    print(f"  'my-func' in evaluator2 after resume? {'my-func' in evaluator2.env}")
    print(f"  Result: {result2}")
    print(f"  Final state: {final_state}")
