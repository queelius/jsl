#!/usr/bin/env python3
"""
Example of step accounting system for network-native execution.

This demonstrates how JSL's step limiting can be used to implement
fair resource allocation in a distributed system.
"""

import time
from typing import Dict, Optional
from jsl.runner import JSLRunner, JSLRuntimeError
from jsl.fluent import E, V

class StepAccount:
    """
    Simple account system for tracking step allocations.
    
    In a real system, this might be backed by a database and
    include authentication, rate limiting, etc.
    """
    
    def __init__(self, initial_allocation: int = 1000, refill_rate: int = 100):
        self.balance = initial_allocation
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self.total_used = 0
    
    def refill(self):
        """Refill account based on time elapsed."""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Refill 'refill_rate' steps per second
        refill_amount = int(elapsed * self.refill_rate)
        if refill_amount > 0:
            self.balance += refill_amount
            self.last_refill = now
            print(f"  [Account] Refilled {refill_amount} steps (balance: {self.balance})")
    
    def withdraw(self, amount: int) -> bool:
        """Try to withdraw steps from account."""
        self.refill()  # Check for refills first
        
        if self.balance >= amount:
            self.balance -= amount
            self.total_used += amount
            return True
        return False
    
    def get_balance(self) -> int:
        """Get current balance after refill."""
        self.refill()
        return self.balance


class NetworkJSLExecutor:
    """
    Network-aware JSL executor with step accounting.
    
    This simulates how JSL might work in a distributed environment
    where computation resources need to be fairly allocated.
    """
    
    def __init__(self):
        self.accounts: Dict[str, StepAccount] = {}
        self.pending_computations: Dict[str, tuple] = {}
    
    def get_account(self, user_id: str) -> StepAccount:
        """Get or create account for user."""
        if user_id not in self.accounts:
            print(f"[System] Creating new account for {user_id}")
            self.accounts[user_id] = StepAccount()
        return self.accounts[user_id]
    
    def execute_for_user(self, user_id: str, expression, max_steps: Optional[int] = None):
        """
        Execute JSL expression for a user with step accounting.
        
        Returns result or saves partial state if steps exhausted.
        """
        account = self.get_account(user_id)
        
        # Determine step allocation
        if max_steps is None:
            max_steps = min(account.get_balance(), 100)  # Default chunk size
        
        if not account.withdraw(max_steps):
            return {"error": "Insufficient step balance", "balance": account.get_balance()}
        
        print(f"[Executor] Running for {user_id} with {max_steps} steps")
        print(f"  [Account] Balance after withdrawal: {account.balance}")
        
        # Create runner with step limit
        runner = JSLRunner(config={"max_steps": max_steps})
        runner.enable_profiling()
        
        try:
            # Check if we're resuming a computation
            if user_id in self.pending_computations:
                print(f"  [Executor] Resuming pending computation for {user_id}")
                remaining_expr, env = self.pending_computations[user_id]
                result = runner.resume(remaining_expr, env, additional_steps=max_steps)
                del self.pending_computations[user_id]
            else:
                result = runner.execute(expression)
            
            stats = runner.get_performance_stats()
            steps_used = stats.get('steps_used', 0)
            
            # Refund unused steps
            refund = max_steps - steps_used
            if refund > 0:
                account.balance += refund
                print(f"  [Account] Refunded {refund} unused steps")
            
            return {
                "result": result,
                "steps_used": steps_used,
                "balance_remaining": account.get_balance()
            }
            
        except JSLRuntimeError as e:
            if "Step limit exceeded" in str(e):
                # Save partial state for resumption
                if hasattr(e, 'remaining_expr'):
                    self.pending_computations[user_id] = (e.remaining_expr, e.env)
                    print(f"  [Executor] Computation paused, state saved for {user_id}")
                
                stats = runner.get_performance_stats()
                return {
                    "status": "paused",
                    "steps_used": stats.get('steps_used', 0),
                    "balance_remaining": account.get_balance(),
                    "message": "Computation paused - call again to resume"
                }
            else:
                raise


def demo():
    """Demonstrate the step accounting system."""
    print("="*60)
    print("JSL Network Execution with Step Accounting Demo")
    print("="*60)
    
    executor = NetworkJSLExecutor()
    
    # Simple computation for Alice
    print("\n1. Alice runs a simple computation:")
    result = executor.execute_for_user("alice", ["+", 1, 2, 3])
    print(f"   Result: {result}")
    
    # Complex computation for Bob that gets paused
    print("\n2. Bob runs a complex computation with limited steps:")
    complex_expr = E.let(
        {"sum": 0},
        E.do(
            *[E.def_("sum", E.add(V.sum, i)) for i in range(1, 21)],
            V.sum
        )
    ).to_jsl()
    
    result = executor.execute_for_user("bob", complex_expr, max_steps=10)
    print(f"   Result: {result}")
    
    # Bob resumes after a brief pause (simulating refill)
    print("\n3. Bob resumes after waiting (steps refilled):")
    time.sleep(0.1)  # Wait for refill
    result = executor.execute_for_user("bob", None)  # None means resume
    print(f"   Result: {result}")
    
    # Charlie with insufficient balance
    print("\n4. Charlie tries expensive computation with low balance:")
    charlie_account = executor.get_account("charlie")
    charlie_account.balance = 5  # Set low balance
    
    result = executor.execute_for_user("charlie", complex_expr)
    print(f"   Result: {result}")
    
    # Show account statistics
    print("\n5. Account Statistics:")
    for user_id, account in executor.accounts.items():
        print(f"   {user_id}: Used {account.total_used} steps total, "
              f"current balance: {account.get_balance()}")
    
    print("\n" + "="*60)
    print("Demo complete - step accounting enables fair resource sharing!")
    print("="*60)


if __name__ == "__main__":
    demo()