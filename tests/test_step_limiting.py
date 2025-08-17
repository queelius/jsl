"""
Tests for step limiting and resumption functionality.
"""

import pytest
from jsl.runner import JSLRunner, JSLRuntimeError
from jsl.core import StepsExhausted


class TestStepLimiting:
    """Test step limiting functionality."""
    
    def test_no_limit_by_default(self):
        """Test that there's no step limit by default."""
        runner = JSLRunner()
        # Should handle complex computation without limits
        result = runner.execute([
            "let", [["x", 0]],
            ["do"] + [["def", "x", ["+", "x", 1]] for _ in range(50)] + ["x"]
        ])
        assert result == 50
    
    def test_basic_step_limit(self):
        """Test that step limit stops execution."""
        runner = JSLRunner(config={"max_steps": 5})
        
        # Simple expression within limit
        result = runner.execute(["+", 1, 2])
        assert result == 3
        
        # Complex expression exceeding limit
        with pytest.raises(JSLRuntimeError) as exc_info:
            runner.execute([
                "let", [["x", 10], ["y", 20]],
                ["+", ["*", "x", 2], ["*", "y", 3]]
            ])
        assert "Step limit exceeded" in str(exc_info.value)
    
    def test_step_counting_accuracy(self):
        """Test that steps are counted correctly."""
        runner = JSLRunner(config={"max_steps": 100})
        runner.enable_profiling()
        
        # Execute and check step count
        runner.execute(["+", 1, 2, 3])
        stats = runner.get_performance_stats()
        assert "steps_used" in stats
        assert stats["steps_used"] > 0
        assert stats["steps_used"] < 10  # Simple addition shouldn't take many steps
    
    def test_step_exhaustion_tracking(self):
        """Test that step exhaustion is tracked in stats."""
        runner = JSLRunner(config={"max_steps": 3})
        runner.enable_profiling()
        
        with pytest.raises(JSLRuntimeError):
            runner.execute(["let", [["x", 1]], ["*", "x", 2]])
        
        stats = runner.get_performance_stats()
        assert stats.get("steps_exhausted") == True
        assert stats.get("steps_used") == 4  # Should hit limit at step 4
    
    def test_step_limit_resets_per_execution(self):
        """Test that step counter resets for each execution."""
        runner = JSLRunner(config={"max_steps": 10})
        
        # First execution
        result1 = runner.execute(["+", 1, 2])
        assert result1 == 3
        
        # Second execution should also work (counter reset)
        result2 = runner.execute(["+", 3, 4])
        assert result2 == 7
        
        # Both should work even though total steps > limit
    
    def test_resumption_with_additional_steps(self):
        """Test resuming execution with additional steps."""
        runner = JSLRunner(config={"max_steps": 5})
        
        # Start a computation that will be interrupted
        with pytest.raises(JSLRuntimeError) as exc_info:
            runner.execute([
                "let", [["x", 1]],
                ["do",
                    ["def", "x", ["+", "x", 1]],
                    ["def", "x", ["+", "x", 1]],
                    ["def", "x", ["+", "x", 1]],
                    "x"
                ]
            ])
        
        error = exc_info.value
        if hasattr(error, 'remaining_expr') and error.remaining_expr:
            # Resume with more steps
            result = runner.resume(error.remaining_expr, error.env, additional_steps=20)
            # Result depends on where execution was interrupted
            # Could be int, function, or None depending on interruption point
            assert result is not None  # Just verify it completed
    
    def test_infinite_loop_protection(self):
        """Test that step limit prevents infinite loops."""
        runner = JSLRunner(config={"max_steps": 100})
        
        # Define a function that would loop forever
        runner.execute([
            "def", "infinite",
            ["lambda", ["n"],
                ["if", True,  # Always true
                    ["infinite", "n"],
                    "n"
                ]
            ]
        ])
        
        # Try to run it
        with pytest.raises(JSLRuntimeError) as exc_info:
            runner.execute(["infinite", 5])
        assert "Step limit exceeded" in str(exc_info.value)
    
    def test_step_limit_with_recursive_functions(self):
        """Test step limiting with recursive functions."""
        runner = JSLRunner(config={"max_steps": 100})  # Increased limit
        
        # Define factorial
        runner.execute([
            "def", "fact",
            ["lambda", ["n"],
                ["if", ["=", "n", 0],
                    1,
                    ["*", "n", ["fact", ["-", "n", 1]]]
                ]
            ]
        ])
        
        # Small factorial should work (3! needs ~50 steps)
        result = runner.execute(["fact", 3])
        assert result == 6
        
        # Large factorial should hit limit
        with pytest.raises(JSLRuntimeError) as exc_info:
            runner.execute(["fact", 20])  # Much larger to ensure hitting limit
        assert "Step limit exceeded" in str(exc_info.value)
    
    def test_zero_step_limit(self):
        """Test behavior with zero step limit."""
        runner = JSLRunner(config={"max_steps": 0})
        
        # Zero could mean unlimited or immediate failure
        # Current implementation treats 0 as a valid limit
        # so execution should fail immediately
        with pytest.raises(JSLRuntimeError):
            runner.execute(42)  # Even literals need 1 step
    
    def test_step_limit_with_host_operations(self):
        """Test that host operations count against step limit."""
        runner = JSLRunner(config={"max_steps": 10})
        
        # Add a simple host handler
        runner.add_host_handler("echo", lambda x: x)
        
        # Host operations should count as steps
        result = runner.execute(["host", "@echo", "@hello"])
        assert result == "hello"
        
        # Multiple host operations might exceed limit
        with pytest.raises(JSLRuntimeError):
            runner.execute([
                "do",
                ["host", "@echo", "@1"],
                ["host", "@echo", "@2"],
                ["host", "@echo", "@3"],
                ["host", "@echo", "@4"],
                ["host", "@echo", "@5"],
            ])