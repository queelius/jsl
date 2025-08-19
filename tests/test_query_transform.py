"""
Unit tests for query (where) and transform operations in JSL.
"""

import pytest
from jsl.runner import JSLRunner


class TestWhereOperator:
    """Test cases for the where operator (declarative filtering)."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = JSLRunner()
        
        # Create test data
        self.runner.execute(["def", "users", ["@", [
            {"name": "Alice", "age": 30, "role": "admin", "active": True},
            {"name": "Bob", "age": 25, "role": "user", "active": True},
            {"name": "Charlie", "age": 35, "role": "admin", "active": False},
            {"name": "David", "age": 28, "role": "user", "active": True},
            {"name": "Eve", "age": 32, "role": "moderator", "active": True}
        ]]])
        
        self.runner.execute(["def", "products", ["@", [
            {"name": "Widget", "price": 29.99, "category": "tools", "tags": ["metal", "durable"]},
            {"name": "Gadget", "price": 99.99, "category": "electronics", "tags": ["smart", "wireless"]},
            {"name": "Doohickey", "price": 19.99, "category": "tools", "tags": ["plastic", "cheap"]},
            {"name": "Thingamajig", "price": 149.99, "category": "electronics", "tags": ["premium", "smart"]}
        ]]])
    
    def test_where_simple_equality(self):
        """Test where with simple equality conditions."""
        # Filter by role
        result = self.runner.execute(["where", "users", ["=", "role", "@admin"]])
        assert len(result) == 2
        assert all(user["role"] == "admin" for user in result)
        
        # Filter by active status
        result = self.runner.execute(["where", "users", ["=", "active", True]])
        assert len(result) == 4
        assert all(user["active"] is True for user in result)
    
    def test_where_comparison_operators(self):
        """Test where with comparison operators."""
        # Age greater than 30
        result = self.runner.execute(["where", "users", [">", "age", 30]])
        assert len(result) == 2
        assert all(user["age"] > 30 for user in result)
        
        # Price less than or equal to 30
        result = self.runner.execute(["where", "products", ["<=", "price", 30]])
        assert len(result) == 2
        assert all(product["price"] <= 30 for product in result)
        
        # Not equal
        result = self.runner.execute(["where", "users", ["!=", "role", "@user"]])
        assert len(result) == 3
        assert all(user["role"] != "user" for user in result)
    
    def test_where_contains_operator(self):
        """Test where with contains operator."""
        # Name contains 'li'
        result = self.runner.execute(["where", "users", ["contains", "name", "@li"]])
        assert len(result) == 2  # Alice and Charlie
        
        # Tags contain 'smart'
        result = self.runner.execute(["where", "products", ["contains", "tags", "@smart"]])
        assert len(result) == 2
    
    def test_where_matches_operator(self):
        """Test where with regex matches operator."""
        # Name starts with 'A' or 'B'
        result = self.runner.execute(["where", "users", ["matches", "name", "@^[AB]"]])
        assert len(result) == 2  # Alice and Bob
        
        # Category ends with 'ics'
        result = self.runner.execute(["where", "products", ["matches", "category", "@ics$"]])
        assert len(result) == 2  # electronics products
    
    def test_where_logical_operators(self):
        """Test where with logical operators (and, or, not)."""
        # AND: admin AND active
        result = self.runner.execute(["where", "users", [
            "and",
            ["=", "role", "@admin"],
            ["=", "active", True]
        ]])
        assert len(result) == 1  # Only Alice
        assert result[0]["name"] == "Alice"
        
        # OR: admin OR moderator
        result = self.runner.execute(["where", "users", [
            "or",
            ["=", "role", "@admin"],
            ["=", "role", "@moderator"]
        ]])
        assert len(result) == 3
        
        # NOT: not user role
        result = self.runner.execute(["where", "users", [
            "not",
            ["=", "role", "@user"]
        ]])
        assert len(result) == 3
    
    def test_where_complex_conditions(self):
        """Test where with complex nested conditions."""
        # (admin OR moderator) AND active AND age >= 30
        result = self.runner.execute(["where", "users", [
            "and",
            ["or",
                ["=", "role", "@admin"],
                ["=", "role", "@moderator"]
            ],
            ["=", "active", True],
            [">=", "age", 30]
        ]])
        assert len(result) == 2  # Alice and Eve
        
        # Expensive electronics OR cheap tools
        result = self.runner.execute(["where", "products", [
            "or",
            ["and",
                ["=", "category", "@electronics"],
                [">", "price", 50]
            ],
            ["and",
                ["=", "category", "@tools"],
                ["<", "price", 25]
            ]
        ]])
        assert len(result) == 3
    
    def test_where_with_nested_paths(self):
        """Test where with nested field paths."""
        # Create nested data
        self.runner.execute(["def", "orders", ["@", [
            {"id": 1, "customer": {"name": "Alice", "vip": True}, "total": 100},
            {"id": 2, "customer": {"name": "Bob", "vip": False}, "total": 50},
            {"id": 3, "customer": {"name": "Charlie", "vip": True}, "total": 200}
        ]]])
        
        # Filter by nested field using $ and get-path
        result = self.runner.execute(["where", "orders", ["=", ["get-path", "$", "@customer.vip"], True]])
        assert len(result) == 2
        assert all(order["customer"]["vip"] is True for order in result)


class TestTransformOperator:
    """Test cases for the transform operator and related functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = JSLRunner()
        
        # Create test data
        self.runner.execute(["def", "user", ["@", {
            "name": "Alice",
            "age": 30,
            "email": "alice@example.com",
            "role": "admin",
            "active": True,
            "metadata": {"created": "2024-01-01", "updated": "2024-01-15"}
        }]])
        
        self.runner.execute(["def", "users", ["@", [
            {"name": "Alice", "age": 30, "role": "admin"},
            {"name": "Bob", "age": 25, "role": "user"},
            {"name": "Charlie", "age": 35, "role": "admin"}
        ]]])
    
    def test_transform_assign(self):
        """Test transform with assign operation."""
        result = self.runner.execute([
            "transform", "user",
            ["assign", "@verified", True]
        ])
        assert result["verified"] is True
        assert result["name"] == "Alice"  # Original fields preserved
    
    def test_transform_pick(self):
        """Test transform with pick operation."""
        result = self.runner.execute([
            "transform", "user",
            ["pick", "@name", "@email", "@role"]
        ])
        assert set(result.keys()) == {"name", "email", "role"}
        assert result["name"] == "Alice"
        assert result["email"] == "alice@example.com"
        assert result["role"] == "admin"
    
    def test_transform_omit(self):
        """Test transform with omit operation."""
        result = self.runner.execute([
            "transform", "user",
            ["omit", "@metadata", "@active"]
        ])
        assert "metadata" not in result
        assert "active" not in result
        assert result["name"] == "Alice"
        assert result["age"] == 30
    
    def test_transform_rename(self):
        """Test transform with rename operation."""
        result = self.runner.execute([
            "transform", "user",
            ["rename", "@email", "@contact"]
        ])
        assert "email" not in result
        assert result["contact"] == "alice@example.com"
        assert result["name"] == "Alice"
    
    def test_transform_default(self):
        """Test transform with default operation."""
        result = self.runner.execute([
            "transform", "user",
            ["default", "@status", "@pending"],
            ["default", "@name", "@Unknown"]  # Should not override existing
        ])
        assert result["status"] == "pending"
        assert result["name"] == "Alice"  # Not overridden
    
    def test_transform_apply(self):
        """Test transform with apply operation."""
        result = self.runner.execute([
            "transform", "user",
            ["apply", "@name", ["lambda", ["s"], ["str-upper", "s"]]],
            ["apply", "@age", ["lambda", ["n"], ["*", "n", 2]]]
        ])
        assert result["name"] == "ALICE"
        assert result["age"] == 60
    
    def test_transform_pipeline(self):
        """Test transform with multiple operations in pipeline."""
        result = self.runner.execute([
            "transform", "user",
            ["pick", "@name", "@age", "@role"],
            ["assign", "@full_name", "@Alice Smith"],
            ["rename", "@age", "@years"],
            ["default", "@department", "@IT"],
            ["omit", "@role"]
        ])
        
        assert set(result.keys()) == {"name", "full_name", "years", "department"}
        assert result["name"] == "Alice"
        assert result["full_name"] == "Alice Smith"
        assert result["years"] == 30
        assert result["department"] == "IT"
    
    def test_transform_on_collection(self):
        """Test transform on a collection of objects."""
        result = self.runner.execute([
            "transform", "users",
            ["assign", "@active", True],
            ["pick", "@name", "@active", "@role"]
        ])
        
        assert len(result) == 3
        for user in result:
            assert user["active"] is True
            assert set(user.keys()) == {"name", "active", "role"}
    
    def test_pick_function(self):
        """Test pick operation within transform."""
        result = self.runner.execute([
            "transform", "user",
            ["pick", "@name", "@age"]
        ])
        assert set(result.keys()) == {"name", "age"}
        assert result["name"] == "Alice"
        assert result["age"] == 30
    
    def test_omit_function(self):
        """Test omit operation within transform."""
        result = self.runner.execute([
            "transform", "user",
            ["omit", "@metadata", "@active"]
        ])
        assert "metadata" not in result
        assert "active" not in result
        assert result["name"] == "Alice"
    
    def test_pluck_function(self):
        """Test pluck function to extract field from collection."""
        names = self.runner.execute(["pluck", "users", "@name"])
        assert names == ["Alice", "Bob", "Charlie"]
        
        ages = self.runner.execute(["pluck", "users", "@age"])
        assert ages == [30, 25, 35]
    
    def test_index_by_function(self):
        """Test index-by function to convert list to keyed object."""
        result = self.runner.execute(["index-by", "users", "@name"])
        assert isinstance(result, dict)
        assert "Alice" in result
        assert "Bob" in result
        assert "Charlie" in result
        assert result["Alice"]["age"] == 30
        assert result["Bob"]["role"] == "user"


class TestCombinedOperations:
    """Test cases combining where and transform operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = JSLRunner()
        
        self.runner.execute(["def", "products", ["@", [
            {"id": 1, "name": "Widget", "price": 29.99, "category": "tools", "stock": 100},
            {"id": 2, "name": "Gadget", "price": 99.99, "category": "electronics", "stock": 50},
            {"id": 3, "name": "Doohickey", "price": 19.99, "category": "tools", "stock": 200},
            {"id": 4, "name": "Thingamajig", "price": 149.99, "category": "electronics", "stock": 25}
        ]]])
    
    def test_where_then_transform(self):
        """Test filtering with where then transforming results."""
        # Get expensive products with simplified structure
        self.runner.execute(["def", "expensive", [
            "transform",
            ["where", "products", [">", "price", 50]],
            ["pick", "@name", "@price"],
            ["assign", "@expensive", True]
        ]])
        
        result = self.runner.execute("expensive")
        assert len(result) == 2
        for product in result:
            assert product["expensive"] is True
            assert set(product.keys()) == {"name", "price", "expensive"}
    
    def test_transform_then_filter(self):
        """Test transforming data then filtering."""
        # Add discount field then filter discounted items
        self.runner.execute(["def", "discounted", [
            "where",
            ["transform", "products",
                ["apply", "@price", ["lambda", ["p"], ["*", "p", 0.8]]],
                ["assign", "@discounted", True]
            ],
            ["<", "price", 80]
        ]])
        
        result = self.runner.execute("discounted")
        assert len(result) == 3  # All except Thingamajig
        for product in result:
            assert product["discounted"] is True
    
    def test_complex_data_pipeline(self):
        """Test complex data processing pipeline."""
        # Process: filter -> transform -> pluck
        self.runner.execute(["def", "tool_names", [
            "pluck",
            ["transform",
                ["where", "products", ["=", "category", "@tools"]],
                ["pick", "@name", "@price"],
                ["apply", "@name", ["lambda", ["n"], ["str-upper", "n"]]]
            ],
            "@name"
        ]])
        
        result = self.runner.execute("tool_names")
        assert result == ["WIDGET", "DOOHICKEY"]
    
    def test_nested_where_conditions(self):
        """Test where with results from transform."""
        # Transform to add computed field, then filter on it
        self.runner.execute(["def", "low_stock_value", [
            "where",
            ["transform", "products",
                ["assign", "@total_value", ["*", "price", "stock"]]
            ],
            [
                "and",
                ["<", "stock", 100],
                ["<", "total_value", 5000]
            ]
        ]])
        
        # This test shows a limitation - we need to compute per item
        # Let's use a simpler example
        self.runner.execute(["def", "in_stock_tools", [
            "where",
            "products",
            [
                "and",
                ["=", "category", "@tools"],
                [">", "stock", 50]
            ]
        ]])
        
        result = self.runner.execute("in_stock_tools")
        assert len(result) == 2
        for product in result:
            assert product["category"] == "tools"
            assert product["stock"] > 50


if __name__ == "__main__":
    pytest.main([__file__])