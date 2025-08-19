"""
Tests for compiler/decompiler roundtrip and JPN format validation.

These tests ensure that:
1. The compiler produces correct JPN format
2. The decompiler correctly reconstructs S-expressions
3. Roundtrip compilation preserves semantics
"""

import json
import pytest
from jsl.compiler import compile_to_postfix, decompile_from_postfix
from jsl.stack_evaluator import StackEvaluator


class TestJPNFormat:
    """Test the JSL Postfix Notation format."""
    
    def test_arity_encoding(self):
        """Test that arity is always encoded before operator."""
        # Binary operations
        assert compile_to_postfix(['+', 2, 3]) == [2, 3, 2, '+']
        assert compile_to_postfix(['*', 4, 5]) == [4, 5, 2, '*']
        
        # 0-arity
        assert compile_to_postfix(['+']) == [0, '+']
        assert compile_to_postfix(['*']) == [0, '*']
        assert compile_to_postfix(['list']) == [0, 'list']
        
        # 1-arity
        assert compile_to_postfix(['+', 5]) == [5, 1, '+']
        assert compile_to_postfix(['not', True]) == [True, 1, 'not']
        
        # N-ary (n > 2)
        assert compile_to_postfix(['+', 1, 2, 3, 4]) == [1, 2, 3, 4, 4, '+']
        assert compile_to_postfix(['list', '@a', '@b', '@c']) == ['@a', '@b', '@c', 3, 'list']
    
    def test_empty_list_encoding(self):
        """Test that empty list uses special marker."""
        assert compile_to_postfix([]) == [0, '__empty_list__']
    
    def test_nested_operations(self):
        """Test nested operations compile correctly."""
        # (2 + 3) * 4
        assert compile_to_postfix(['*', ['+', 2, 3], 4]) == [2, 3, 2, '+', 4, 2, '*']
        
        # ((a + b) * (c - d))
        assert compile_to_postfix(
            ['*', ['+', 'a', 'b'], ['-', 'c', 'd']]
        ) == ['a', 'b', 2, '+', 'c', 'd', 2, '-', 2, '*']
    
    def test_json_compatibility(self):
        """Test that JPN format is valid JSON."""
        test_cases = [
            ['+', 2, 3],
            ['*', ['+', 1, 2], ['-', 5, 3]],
            ['list', '@a', '@b', '@c'],
            [],
        ]
        
        for expr in test_cases:
            postfix = compile_to_postfix(expr)
            # Should be JSON serializable
            json_str = json.dumps(postfix)
            # And deserializable
            restored = json.loads(json_str)
            assert restored == postfix


class TestDecompiler:
    """Test decompilation from JPN back to S-expressions."""
    
    def test_simple_decompilation(self):
        """Test decompiling simple expressions."""
        test_cases = [
            ([2, 3, 2, '+'], ['+', 2, 3]),
            ([4, 5, 2, '*'], ['*', 4, 5]),
            ([0, '+'], ['+']),
            ([5, 1, '+'], ['+', 5]),
        ]
        
        for postfix, expected in test_cases:
            result = decompile_from_postfix(postfix)
            assert result == expected
    
    def test_nested_decompilation(self):
        """Test decompiling nested expressions."""
        postfix = [2, 3, 2, '+', 4, 2, '*']  # (2 + 3) * 4
        expected = ['*', ['+', 2, 3], 4]
        assert decompile_from_postfix(postfix) == expected
    
    def test_nary_decompilation(self):
        """Test decompiling n-ary operations."""
        test_cases = [
            ([1, 2, 3, 4, 4, '+'], ['+', 1, 2, 3, 4]),
            (['@a', '@b', '@c', 3, 'list'], ['list', '@a', '@b', '@c']),
            ([0, 'list'], ['list']),
        ]
        
        for postfix, expected in test_cases:
            result = decompile_from_postfix(postfix)
            assert result == expected
    
    def test_empty_list_decompilation(self):
        """Test empty list decompilation."""
        assert decompile_from_postfix([0, '__empty_list__']) == []


class TestRoundtrip:
    """Test compile -> decompile -> compile roundtrip."""
    
    def normalize_postfix(self, postfix):
        """Normalize postfix for comparison."""
        # Convert to JSON and back to normalize representation
        json_str = json.dumps(postfix, sort_keys=True)
        return json.loads(json_str)
    
    def test_double_roundtrip(self):
        """Test: compile → decompile → compile."""
        test_expressions = [
            5,
            3.14,
            True,
            None,
            "x",
            "@hello",
            [],
            ['+', 2, 3],
            ['*', 4, 5],
            ['not', True],
            ['+'],
            ['+', 5],
            ['+', 1, 2, 3, 4, 5],
            ['list', '@a', '@b', '@c'],
            ['*', ['+', 2, 3], 4],
            ['+', ['-', 5, 2], 3],
        ]
        
        for expr in test_expressions:
            # First compilation
            postfix1 = compile_to_postfix(expr)
            
            # Decompile back to S-expression
            sexpr = decompile_from_postfix(postfix1)
            
            # Compile again
            postfix2 = compile_to_postfix(sexpr)
            
            # Should get same postfix
            assert self.normalize_postfix(postfix1) == self.normalize_postfix(postfix2), \
                f"Roundtrip failed for {expr}"
    
    def test_evaluation_equivalence(self):
        """Test that original and roundtripped expressions evaluate the same."""
        evaluator = StackEvaluator()
        
        test_cases = [
            (['+', 2, 3], 5),
            (['*', 4, 5], 20),
            (['+'], 0),
            (['*'], 1),
            (['+', 1, 2, 3, 4], 10),
            (['*', ['+', 2, 3], 4], 20),
        ]
        
        for expr, expected in test_cases:
            # Compile original
            postfix1 = compile_to_postfix(expr)
            result1 = evaluator.eval(postfix1)
            
            # Roundtrip
            sexpr = decompile_from_postfix(postfix1)
            postfix2 = compile_to_postfix(sexpr)
            result2 = evaluator.eval(postfix2)
            
            # Both should evaluate to expected value
            assert result1 == expected
            assert result2 == expected


class TestIdentityElements:
    """Test that operators return correct identity elements for 0-arity."""
    
    def test_arithmetic_identities(self):
        """Test arithmetic identity elements."""
        evaluator = StackEvaluator()
        
        # Addition identity is 0
        assert evaluator.eval(compile_to_postfix(['+'])) == 0
        
        # Multiplication identity is 1
        assert evaluator.eval(compile_to_postfix(['*'])) == 1
        
        # Min identity is +infinity
        assert evaluator.eval(compile_to_postfix(['min'])) == float('inf')
        
        # Max identity is -infinity
        assert evaluator.eval(compile_to_postfix(['max'])) == float('-inf')
    
    def test_logical_identities(self):
        """Test logical identity elements."""
        evaluator = StackEvaluator()
        
        # AND of nothing is true (all of empty set)
        assert evaluator.eval(compile_to_postfix(['and'])) == True
        
        # OR of nothing is false (any of empty set)
        assert evaluator.eval(compile_to_postfix(['or'])) == False
    
    def test_collection_identities(self):
        """Test collection identity elements."""
        evaluator = StackEvaluator()
        
        # Empty list
        assert evaluator.eval(compile_to_postfix(['list'])) == []