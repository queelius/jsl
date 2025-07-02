#!/usr/bin/env python3
"""
JSL Command Line Interface

Provides command-line tools for running JSL programs, starting a REPL,
and managing JSL code.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional

from . import run_program, eval_expression, make_prelude, serialize, deserialize
from .core import HostDispatcher


def create_basic_host_dispatcher() -> HostDispatcher:
    """Create a basic host dispatcher with common operations."""
    dispatcher = HostDispatcher()
    
    # Logging operations
    dispatcher.register("log", lambda *args: print("LOG:", *args))
    dispatcher.register("warn", lambda *args: print("WARN:", *args, file=sys.stderr))
    dispatcher.register("error", lambda *args: print("ERROR:", *args, file=sys.stderr))
    
    # File operations (basic, read-only for security)
    def read_file(path: str) -> str:
        try:
            return Path(path).read_text()
        except Exception as e:
            raise Exception(f"Failed to read file {path}: {e}")
    
    dispatcher.register("file/read", read_file)
    
    return dispatcher


def run_file(filepath: str, host_dispatcher: Optional[HostDispatcher] = None) -> None:
    """Run a JSL file."""
    try:
        content = Path(filepath).read_text()
        result = run_program(content, host_dispatcher)
        if result is not None:
            print(json.dumps(result, indent=2))
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def run_repl(host_dispatcher: Optional[HostDispatcher] = None) -> None:
    """Start an interactive JSL REPL."""
    print("JSL REPL v0.1.0")
    print("Type expressions in JSON format. Press Ctrl+C to exit.")
    print()
    
    env = make_prelude()
    
    while True:
        try:
            line = input("jsl> ")
            if not line.strip():
                continue

            if line.strip().lower() == "exit":
                print("Exiting REPL. Goodbye!")
                break

            if line.strip().startswith("#"):
                # Ignore comments
                continue

            if line.strip().lower() == "help":
                print("Available commands:")
                print("  - Type any JSL expression in JSON format")
                print("  - Type 'exit' to quit the REPL")
                print("  - Type 'help' for this message")
                continue

            
            result = eval_expression(line, env, host_dispatcher)
            if result is not None:
                print(json.dumps(result, indent=2))
        
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def eval_string(expression: str, host_dispatcher: Optional[HostDispatcher] = None) -> None:
    """Evaluate a JSL expression from command line."""
    try:
        result = eval_expression(expression, host_dispatcher=host_dispatcher)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="JSL - JSON Serializable Language",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  jsl --repl                    Start interactive REPL
  jsl --eval '["+", 1, 2, 3]'   Evaluate expression
  jsl program.jsl               Run JSL file
  jsl --help                    Show this help
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--repl", 
        action="store_true",
        help="Start interactive REPL"
    )
    group.add_argument(
        "--eval", "-e",
        metavar="EXPRESSION",
        help="Evaluate JSL expression"
    )
    group.add_argument(
        "file", 
        nargs="?",
        help="JSL file to execute"
    )
    
    parser.add_argument(
        "--no-host",
        action="store_true", 
        help="Disable host operations (pure evaluation only)"
    )
    
    args = parser.parse_args()
    
    # Set up host dispatcher
    host_dispatcher = None if args.no_host else create_basic_host_dispatcher()
    
    # Execute based on arguments
    if args.repl:
        run_repl(host_dispatcher)
    elif args.eval:
        eval_string(args.eval, host_dispatcher)
    elif args.file:
        run_file(args.file, host_dispatcher)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
