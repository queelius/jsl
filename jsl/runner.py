import argparse
import json
import sys

from .evaluator import eval_expr as evaluate
from .prelude import make_prelude


def run_program(program, prelude=None):
    """
    Runs a JSL program.
    
    The program can be:
    - A single JSL expression  
    - A list of expressions (returns result of last one)
    - A dict with 'forms' and optional 'entrypoint'
    """
    if prelude is None:
        prelude = make_prelude()
        
    # Handle different program formats
    if isinstance(program, dict):
        if 'forms' in program:
            # Execute all forms first
            for form in program['forms']:
                evaluate(form, prelude)
            # Then execute entrypoint if provided
            if 'entrypoint' in program:
                return evaluate(program['entrypoint'], prelude)
            else:
                # If no entrypoint, return result of last form
                if program['forms']:
                    return evaluate(program['forms'][-1], prelude)
                return None
        else:
            # Dict without 'forms' is treated as a single expression
            return evaluate(program, prelude)
    elif isinstance(program, list) and len(program) > 0 and isinstance(program[0], list):
        # List of expressions - execute all, return result of last
        result = None
        for expr in program:
            result = evaluate(expr, prelude)
        return result
    else:
        # Single expression
        return evaluate(program, prelude)

def main():
    """
    The main entry point for the JSL runner.
    """
    parser = argparse.ArgumentParser(description="A JSL runner.")
    parser.add_argument("program", help="The JSL program to run.")
    parser.add_argument("-p", "--prelude", help="A JSON file containing the prelude.")
    args = parser.parse_args()

    with open(args.program, "r") as f:
        program = json.load(f)

    if args.prelude:
        with open(args.prelude, "r") as f:
            prelude = json.load(f)
    else:
        prelude = make_prelude()

    result = run_program(program, prelude)
    print(json.dumps(result, indent=4))

if __name__ == "__main__":
    main()
