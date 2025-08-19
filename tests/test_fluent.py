"""
Unit tests for jsl.fluent module
"""

import pytest
import json

from jsl.fluent import (
    E, V, FluentExpression, ExpressionBuilder, VariableBuilder,
    literal, var, expr, pipeline, Pipeline, _unwrap
)


class TestFluentExpression:
    """Test cases for FluentExpression class."""
    
    def test_initialization(self):
        """Test FluentExpression initialization."""
        fe = FluentExpression(["+", 1, 2])
        assert fe.to_jsl() == ["+", 1, 2]
    
    def test_repr(self):
        """Test FluentExpression string representation."""
        fe = FluentExpression(["+", 1, 2])
        repr_str = repr(fe)
        assert "FluentExpression" in repr_str
        assert "[" in repr_str  # Should contain JSON representation
    
    def test_arithmetic_operators(self):
        """Test arithmetic operator overloading."""
        x = FluentExpression("x")
        y = FluentExpression("y")
        
        # Addition
        add_expr = x + y
        assert add_expr.to_jsl() == ["+", "x", "y"]
        
        # Right addition
        add_expr = 1 + x
        assert add_expr.to_jsl() == ["+", 1, "x"]
        
        # Subtraction
        sub_expr = x - y
        assert sub_expr.to_jsl() == ["-", "x", "y"]
        
        # Multiplication
        mul_expr = x * 2
        assert mul_expr.to_jsl() == ["*", "x", 2]
        
        # Division
        div_expr = x / y
        assert div_expr.to_jsl() == ["/", "x", "y"]
        
        # Modulo
        mod_expr = x % y
        assert mod_expr.to_jsl() == ["mod", "x", "y"]
    
    def test_comparison_operators(self):
        """Test comparison operator overloading."""
        x = FluentExpression("x")
        y = FluentExpression("y")
        
        # Equality
        eq_expr = x == y
        assert eq_expr.to_jsl() == ["=", "x", "y"]
        
        # Inequality  
        ne_expr = x != y
        assert ne_expr.to_jsl() == ["not", ["=", "x", "y"]]
        
        # Less than
        lt_expr = x < y
        assert lt_expr.to_jsl() == ["<", "x", "y"]
        
        # Greater than
        gt_expr = x > y
        assert gt_expr.to_jsl() == [">", "x", "y"]
        
        # Less than or equal
        le_expr = x <= y
        assert le_expr.to_jsl() == ["<=", "x", "y"]
        
        # Greater than or equal
        ge_expr = x >= y
        assert ge_expr.to_jsl() == [">=", "x", "y"]
    
    def test_logical_operators(self):
        """Test logical operator overloading."""
        x = FluentExpression("x")
        y = FluentExpression("y")
        
        # Logical AND
        and_expr = x & y
        assert and_expr.to_jsl() == ["and", "x", "y"]
        
        # Logical OR
        or_expr = x | y
        assert or_expr.to_jsl() == ["or", "x", "y"]
        
        # Logical NOT
        not_expr = ~x
        assert not_expr.to_jsl() == ["not", "x"]
    
    def test_collection_methods(self):
        """Test collection method chaining."""
        arr = FluentExpression("arr")
        func = FluentExpression("func")
        
        # Map
        map_expr = arr.map(func)
        assert map_expr.to_jsl() == ["map", "func", "arr"]
        
        # Filter
        filter_expr = arr.filter(func)
        assert filter_expr.to_jsl() == ["filter", "func", "arr"]
        
        # Reduce with initial value
        reduce_expr = arr.reduce(func, 0)
        assert reduce_expr.to_jsl() == ["reduce", "func", 0, "arr"]
        
        # Reduce without initial value
        reduce_expr = arr.reduce(func)
        assert reduce_expr.to_jsl() == ["reduce", "func", "arr"]
        
        # Get with default
        get_expr = arr.get("key", "default")
        assert get_expr.to_jsl() == ["get", "arr", "key", "default"]
        
        # Get without default
        get_expr = arr.get("key")
        assert get_expr.to_jsl() == ["get", "arr", "key"]
        
        # Has
        has_expr = arr.has("key")
        assert has_expr.to_jsl() == ["has", "arr", "key"]
        
        # Length
        len_expr = arr.length()
        assert len_expr.to_jsl() == ["length", "arr"]
        
        # First and rest
        first_expr = arr.first()
        assert first_expr.to_jsl() == ["first", "arr"]
        
        rest_expr = arr.rest()
        assert rest_expr.to_jsl() == ["rest", "arr"]
        
        # Concat
        concat_expr = arr.concat("other1", "other2")
        assert concat_expr.to_jsl() == ["concat", "arr", "other1", "other2"]
    
    def test_string_methods(self):
        """Test string method chaining."""
        s = FluentExpression("s")
        
        # String concatenation
        concat_expr = s.str_concat(" ", "world")
        assert concat_expr.to_jsl() == ["str-concat", "s", " ", "world"]
        
        # String split
        split_expr = s.str_split(" ")
        assert split_expr.to_jsl() == ["str-split", "s", " "]
        
        # String contains
        contains_expr = s.str_contains("substring")
        assert contains_expr.to_jsl() == ["str-contains", "s", "substring"]
        
        # String case conversion
        upper_expr = s.str_upper()
        assert upper_expr.to_jsl() == ["str-upper", "s"]
        
        lower_expr = s.str_lower()
        assert lower_expr.to_jsl() == ["str-lower", "s"]


class TestExpressionBuilder:
    """Test cases for ExpressionBuilder (E) class."""
    
    def test_dynamic_method_creation(self):
        """Test dynamic method creation via __getattr__."""
        # Test dynamic function calls
        expr = E.some_function(1, 2, 3)
        assert expr.to_jsl() == ["some-function", 1, 2, 3]
        
        # Test with keyword arguments
        expr = E.create_user("alice", age=30, active=True)
        assert expr.to_jsl() == ["create-user", "alice", {"@age": 30, "@active": True}]
    
    def test_core_arithmetic_functions(self):
        """Test explicit arithmetic function implementations."""
        # Addition
        add_expr = E.add(1, 2, 3)
        assert add_expr.to_jsl() == ["+", 1, 2, 3]
        
        # Subtraction
        sub_expr = E.subtract(10, 3)
        assert sub_expr.to_jsl() == ["-", 10, 3]
        
        # Multiplication
        mul_expr = E.multiply(4, 5, 6)
        assert mul_expr.to_jsl() == ["*", 4, 5, 6]
        
        # Division
        div_expr = E.divide(20, 4)
        assert div_expr.to_jsl() == ["/", 20, 4]
        
        # Equality
        eq_expr = E.equals(1, 1)
        assert eq_expr.to_jsl() == ["=", 1, 1]
    
    def test_comparison_functions(self):
        """Test comparison function implementations."""
        lt_expr = E.less_than(5, 10)
        assert lt_expr.to_jsl() == ["<", 5, 10]
        
        gt_expr = E.greater_than(10, 5)
        assert gt_expr.to_jsl() == [">", 10, 5]
    
    def test_conditional_function(self):
        """Test if_ function implementation."""
        # With else clause
        if_expr = E.if_(True, "yes", "no")
        assert if_expr.to_jsl() == ["if", True, "yes", "no"]
        
        # Without else clause
        if_expr = E.if_(True, "yes")
        assert if_expr.to_jsl() == ["if", True, "yes"]
    
    def test_let_function(self):
        """Test let function implementation."""
        # With dictionary bindings
        let_expr = E.let({"x": 10, "y": 20}, V.x + V.y)
        expected = ["let", [["x", 10], ["y", 20]], ["+", "x", "y"]]
        assert let_expr.to_jsl() == expected
        
        # With list bindings
        bindings = [["x", 10], ["y", 20]]
        let_expr = E.let(bindings, V.x + V.y)
        expected = ["let", bindings, ["+", "x", "y"]]
        assert let_expr.to_jsl() == expected
    
    def test_do_function(self):
        """Test do function implementation."""
        do_expr = E.do("expr1", "expr2", "expr3")
        assert do_expr.to_jsl() == ["do", "expr1", "expr2", "expr3"]
    
    def test_lambda_function(self):
        """Test lambda_ function implementation."""
        # Single parameter as string
        lambda_expr = E.lambda_("x", V.x * 2)
        assert lambda_expr.to_jsl() == ["lambda", ["x"], ["*", "x", 2]]
        
        # Multiple parameters as list
        lambda_expr = E.lambda_(["x", "y"], V.x + V.y)
        assert lambda_expr.to_jsl() == ["lambda", ["x", "y"], ["+", "x", "y"]]
    
    def test_def_function(self):
        """Test def_ function implementation."""
        def_expr = E.def_("x", 42)
        assert def_expr.to_jsl() == ["def", "x", 42]
    
    def test_quote_function(self):
        """Test quote function implementation."""
        quote_expr = E.quote(["+", 1, 2])
        assert quote_expr.to_jsl() == ["@", ["+", 1, 2]]
    
    def test_list_function(self):
        """Test list function implementation."""
        list_expr = E.list(1, 2, 3, 4)
        assert list_expr.to_jsl() == ["@", [1, 2, 3, 4]]
    
    def test_object_function(self):
        """Test object function implementation."""
        obj_expr = E.object(name="Alice", age=30, active=True)
        expected = {"@name": "Alice", "@age": 30, "@active": True}
        assert obj_expr.to_jsl() == expected
    
    def test_collection_functions(self):
        """Test collection function implementations."""
        func = E.lambda_("x", V.x * 2)
        arr = E.list(1, 2, 3)
        
        # Map
        map_expr = E.map(func, arr)
        expected = ["map", ["lambda", ["x"], ["*", "x", 2]], ["@", [1, 2, 3]]]
        assert map_expr.to_jsl() == expected
        
        # Filter
        filter_expr = E.filter(func, arr)
        expected = ["filter", ["lambda", ["x"], ["*", "x", 2]], ["@", [1, 2, 3]]]
        assert filter_expr.to_jsl() == expected
        
        # Reduce
        reduce_expr = E.reduce(func, 0, arr)
        expected = ["reduce", ["lambda", ["x"], ["*", "x", 2]], 0, ["@", [1, 2, 3]]]
        assert reduce_expr.to_jsl() == expected
    
    def test_host_function(self):
        """Test host function implementation."""
        host_expr = E.host("file/read", "/tmp/test.txt")
        assert host_expr.to_jsl() == ["host", "@file/read", "/tmp/test.txt"]


class TestVariableBuilder:
    """Test cases for VariableBuilder (V) class."""
    
    def test_attribute_access(self):
        """Test variable creation via attribute access."""
        x_var = V.x
        assert x_var.to_jsl() == "x"
        
        long_name_var = V.long_variable_name
        assert long_name_var.to_jsl() == "long_variable_name"
    
    def test_item_access(self):
        """Test variable creation via item access."""
        x_var = V["x"]
        assert x_var.to_jsl() == "x"
        
        special_var = V["variable-with-dashes"]
        assert special_var.to_jsl() == "variable-with-dashes"


class TestGlobalInstances:
    """Test cases for global E and V instances."""
    
    def test_global_e_instance(self):
        """Test that E is a working ExpressionBuilder instance."""
        expr = E.add(1, 2)
        assert expr.to_jsl() == ["+", 1, 2]
    
    def test_global_v_instance(self):
        """Test that V is a working VariableBuilder instance."""
        var_expr = V.x
        assert var_expr.to_jsl() == "x"


class TestUtilityFunctions:
    """Test cases for utility functions."""
    
    def test_unwrap_function(self):
        """Test _unwrap utility function."""
        # FluentExpression
        fe = FluentExpression(["+", 1, 2])
        assert _unwrap(fe) == ["+", 1, 2]
        
        # Regular values
        assert _unwrap(42) == 42
        assert _unwrap("string") == "string"
        assert _unwrap([1, 2, 3]) == [1, 2, 3]
        assert _unwrap({"key": "value"}) == {"key": "value"}
    
    def test_literal_function(self):
        """Test literal convenience function."""
        # String literal
        str_literal = literal("hello")
        assert str_literal.to_jsl() == "@hello"
        
        # List literal
        list_literal = literal([1, 2, 3])
        assert list_literal.to_jsl() == ["@", [1, 2, 3]]
        
        # Other types
        num_literal = literal(42)
        assert num_literal.to_jsl() == 42
    
    def test_var_function(self):
        """Test var convenience function."""
        x_var = var("x")
        assert x_var.to_jsl() == "x"
    
    def test_expr_function(self):
        """Test expr convenience function."""
        jsl_expr = ["+", 1, 2]
        wrapped = expr(jsl_expr)
        assert wrapped.to_jsl() == jsl_expr


class TestPipeline:
    """Test cases for Pipeline class."""
    
    def test_pipeline_creation(self):
        """Test pipeline creation."""
        p = Pipeline(42)
        assert p.value.to_jsl() == 42
    
    def test_pipeline_chaining(self):
        """Test pipeline method chaining."""
        double = lambda x: x * 2
        p = Pipeline(5).pipe(double)
        
        # Since we can't easily test Python functions in pipelines,
        # let's test with FluentExpression functions
        p = Pipeline(E.list(1, 2, 3))
        p = p.pipe(lambda arr: arr.map(E.lambda_("x", V.x * 2)))
        
        expected = ["map", ["lambda", ["x"], ["*", "x", 2]], ["@", [1, 2, 3]]]
        assert p.result().to_jsl() == expected
    
    def test_pipeline_function(self):
        """Test pipeline convenience function."""
        p = pipeline(42)
        assert isinstance(p, Pipeline)
        assert p.value.to_jsl() == 42


class TestComplexExpressions:
    """Test cases for complex expression building."""
    
    def test_method_chaining_pipeline(self):
        """Test the main documentation example."""
        pipeline_expr = E.list(1, 2, 3, 4, 5, 6).map(
            E.lambda_("n", V.n * 2)
        ).filter(
            E.lambda_("n", V.n > 5)
        )
        
        expected = [
            "filter",
            ["lambda", ["n"], [">", "n", 5]],
            ["map", ["lambda", ["n"], ["*", "n", 2]], ["@", [1, 2, 3, 4, 5, 6]]]
        ]
        assert pipeline_expr.to_jsl() == expected
    
    def test_nested_expressions(self):
        """Test deeply nested expression building."""
        expr = E.let(
            {"nums": E.list(1, 2, 3, 4, 5)},
            E.reduce(
                E.lambda_(["acc", "n"], V.acc + V.n),
                0,
                V.nums
            )
        )
        
        expected = [
            "let",
            [["nums", ["@", [1, 2, 3, 4, 5]]]],
            ["reduce", ["lambda", ["acc", "n"], ["+", "acc", "n"]], 0, "nums"]
        ]
        assert expr.to_jsl() == expected
    
    def test_mixed_operators_and_methods(self):
        """Test mixing operator overloading with method calls."""
        expr = (V.x + V.y).str_concat(literal(" = "), (V.x + V.y))
        expected = [
            "str-concat",
            ["+", "x", "y"],
            "@ = ",
            ["+", "x", "y"]
        ]
        assert expr.to_jsl() == expected
    
    def test_conditional_with_operators(self):
        """Test conditional expressions with operators."""
        expr = E.if_(
            V.x > literal(10),
            literal("big"),
            literal("small")
        )
        expected = ["if", [">", "x", 10], "@big", "@small"]
        assert expr.to_jsl() == expected


class TestIntegrationWithRunner:
    """Test cases for fluent API integration with JSLRunner."""
    
    def test_basic_integration(self):
        """Test that fluent expressions work with JSLRunner."""
        # Import here to avoid circular dependencies in testing
        from jsl.runner import JSLRunner
        
        runner = JSLRunner()
        
        # Simple arithmetic
        expr = E.add(1, 2, 3)
        result = runner.execute(expr.to_jsl())
        assert result == 6
        
        # Variable operations
        runner.execute(["def", "x", 10])
        expr = V.x * 2
        result = runner.execute(expr.to_jsl())
        assert result == 20
    
    def test_complex_pipeline_integration(self):
        """Test complex pipeline with JSLRunner."""
        from jsl.runner import JSLRunner
        
        runner = JSLRunner()
        
        # The documentation example
        pipeline_expr = E.list(1, 2, 3, 4, 5, 6).map(
            E.lambda_("n", V.n * 2)
        ).filter(
            E.lambda_("n", V.n > 5)
        )
        
        result = runner.execute(pipeline_expr.to_jsl())
        assert result == [6, 8, 10, 12]


if __name__ == "__main__":
    pytest.main([__file__])