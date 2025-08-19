"""
Evaluation modes for JSL - recursive vs stack-based.

This module provides a unified interface to both evaluation strategies:
1. Recursive: Simple, elegant, but limited resumption
2. Stack-based: Compiled to postfix, efficient resumption

The stack-based approach treats postfix arrays as the "bytecode" of JSL,
with S-expressions serving as the human-friendly source language.
"""

from typing import Any, Optional, Union
from enum import Enum

from .core import Evaluator, Env
from .compiler import compile_to_postfix
from .stack_evaluator import StackEvaluator, StackState
from .resources import ResourceLimits, ResourceExhausted
from .host import HostDispatcher


class EvalMode(Enum):
    """Available evaluation modes."""
    RECURSIVE = "recursive"
    STACK = "stack"


class JSLEvaluator:
    """
    Unified evaluator supporting multiple evaluation strategies.
    
    This class provides a consistent interface regardless of whether
    you're using recursive or stack-based evaluation.
    """
    
    def __init__(self, 
                 mode: EvalMode = EvalMode.RECURSIVE,
                 host_dispatcher: Optional[HostDispatcher] = None,
                 resource_limits: Optional[ResourceLimits] = None):
        """
        Initialize evaluator with specified mode.
        
        Args:
            mode: Evaluation strategy to use
            host_dispatcher: Host interaction handler
            resource_limits: Resource constraints
        """
        self.mode = mode
        self.host = host_dispatcher or HostDispatcher()
        self.resource_limits = resource_limits
        
        if mode == EvalMode.RECURSIVE:
            self.evaluator = Evaluator(host_dispatcher=self.host, 
                                      resource_limits=resource_limits)
        else:
            # Stack mode - we'll compile expressions to postfix
            self.stack_evaluator = StackEvaluator()
            self.saved_state: Optional[StackState] = None
    
    def eval(self, expr: Any, env: Optional[Union[Env, dict]] = None) -> Any:
        """
        Evaluate expression using the configured mode.
        
        Args:
            expr: JSL expression (S-expression format)
            env: Environment (Env for recursive, dict for stack)
            
        Returns:
            Result of evaluation
        """
        if self.mode == EvalMode.RECURSIVE:
            # Use traditional recursive evaluator
            if env is None:
                env = Env()
            elif isinstance(env, dict):
                env = Env(env)
            return self.evaluator.eval(expr, env)
        
        else:
            # Stack mode: compile to postfix first
            if isinstance(expr, list) and len(expr) > 0 and expr[0] == '__postfix__':
                # Already compiled - use directly
                postfix = expr[1:]
            else:
                # Compile S-expression to postfix
                postfix = compile_to_postfix(expr)
            
            # Convert Env to dict if needed
            if isinstance(env, Env):
                env_dict = env.to_dict()
            else:
                env_dict = env or {}
            
            # Create stack evaluator with environment
            self.stack_evaluator.env = env_dict
            
            # Use saved state if resuming
            if self.saved_state:
                result = self.stack_evaluator.eval(postfix, state=self.saved_state)
                self.saved_state = None
            else:
                result = self.stack_evaluator.eval(postfix)
            
            return result
    
    def eval_with_resumption(self, expr: Any, env: Optional[Union[Env, dict]] = None,
                            max_steps: Optional[int] = None) -> tuple[Optional[Any], bool]:
        """
        Evaluate with support for resumption.
        
        Args:
            expr: JSL expression
            env: Environment
            max_steps: Maximum steps (stack mode only)
            
        Returns:
            Tuple of (result, is_complete)
            - result is None if not complete
            - is_complete is True if evaluation finished
        """
        if self.mode == EvalMode.RECURSIVE:
            # Recursive mode: limited resumption support
            try:
                result = self.eval(expr, env)
                return result, True
            except ResourceExhausted as e:
                # Can only save top-level expression
                self.saved_expr = e.remaining_expr
                self.saved_env = e.env
                return None, False
        
        else:
            # Stack mode: full resumption support
            if isinstance(expr, list) and len(expr) > 0 and expr[0] == '__postfix__':
                postfix = expr[1:]
            else:
                postfix = compile_to_postfix(expr)
            
            if isinstance(env, Env):
                env_dict = env.to_dict()
            else:
                env_dict = env or {}
            
            self.stack_evaluator.env = env_dict
            
            if max_steps:
                result, state = self.stack_evaluator.eval_partial(
                    postfix, max_steps, state=self.saved_state
                )
                self.saved_state = state
                return result, (state is None)
            else:
                result = self.stack_evaluator.eval(postfix, state=self.saved_state)
                self.saved_state = None
                return result, True
    
    def resume(self) -> tuple[Optional[Any], bool]:
        """
        Resume a paused evaluation.
        
        Returns:
            Tuple of (result, is_complete)
        """
        if self.mode == EvalMode.RECURSIVE:
            if hasattr(self, 'saved_expr'):
                return self.eval_with_resumption(self.saved_expr, self.saved_env)
            else:
                raise ValueError("No saved state to resume")
        
        else:
            if self.saved_state:
                result, state = self.stack_evaluator.eval_partial(
                    self.saved_state.instructions, 
                    max_steps=100,  # Default step limit
                    state=self.saved_state
                )
                self.saved_state = state
                return result, (state is None)
            else:
                raise ValueError("No saved state to resume")


# Demonstration
if __name__ == "__main__":
    print("=== Evaluation Mode Comparison ===\n")
    
    expr = ['*', ['+', 10, 20], ['-', 100, 50]]
    
    # Test recursive mode
    print("1. Recursive Evaluation:")
    rec_eval = JSLEvaluator(mode=EvalMode.RECURSIVE)
    result = rec_eval.eval(expr)
    print(f"   {expr} = {result}\n")
    
    # Test stack mode
    print("2. Stack-Based Evaluation:")
    stack_eval = JSLEvaluator(mode=EvalMode.STACK)
    result = stack_eval.eval(expr)
    print(f"   {expr} = {result}\n")
    
    # Test resumption in stack mode
    print("3. Stack-Based with Resumption (2 steps at a time):")
    stack_eval2 = JSLEvaluator(mode=EvalMode.STACK)
    complete = False
    attempts = 0
    
    while not complete and attempts < 10:
        attempts += 1
        result, complete = stack_eval2.eval_with_resumption(
            expr, max_steps=2
        )
        if complete:
            print(f"   Attempt {attempts}: Complete! Result = {result}")
        else:
            print(f"   Attempt {attempts}: Partial (saved state)")
    
    print("\n=== Postfix as Primary Representation ===\n")
    
    # Show how postfix can be the primary format
    from .compiler import compile_to_postfix
    
    # Compile once
    postfix = compile_to_postfix(expr)
    print(f"Original S-expr: {expr}")
    print(f"Compiled postfix: {postfix}")
    print()
    
    # Share postfix directly (more efficient)
    postfix_expr = ['__postfix__'] + postfix
    
    stack_eval3 = JSLEvaluator(mode=EvalMode.STACK)
    result = stack_eval3.eval(postfix_expr)
    print(f"Direct postfix evaluation: {result}")
    print()
    
    print("Benefits of postfix as primary:")
    print("1. More compact representation")
    print("2. No parsing ambiguity") 
    print("3. Direct execution without tree traversal")
    print("4. Easy serialization for network transmission")
    print("5. Trivial resumption (just save stack + pc)")