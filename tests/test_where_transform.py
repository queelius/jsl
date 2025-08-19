"""
Simple tests for where and transform operators.
"""

import pytest
from jsl.runner import JSLRunner


class TestWhereTransform:
    """Test where and transform operators."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = JSLRunner()
        
    def test_where_basic(self):
        """Test basic where filtering."""
        # Create test data
        self.runner.execute(["def", "users", ["@", [
            {"name": "Alice", "age": 30, "role": "admin"},
            {"name": "Bob", "age": 25, "role": "user"},
            {"name": "Charlie", "age": 35, "role": "admin"}
        ]]])
        
        # Filter by role - condition is not quoted, where evaluates it
        result = self.runner.execute(["where", "users", ["=", "role", "@admin"]])
        assert len(result) == 2
        assert all(user["role"] == "admin" for user in result)
        
        # Filter by age
        result = self.runner.execute(["where", "users", [">", "age", 25]])
        assert len(result) == 2
        
    def test_where_logical(self):
        """Test where with logical operators."""
        self.runner.execute(["def", "data", ["@", [
            {"x": 10, "y": 20, "z": True},
            {"x": 5, "y": 15, "z": False},
            {"x": 15, "y": 10, "z": True}
        ]]])
        
        # AND condition
        result = self.runner.execute(["where", "data", [
            "and",
            [">", "x", 5],
            ["=", "z", True]
        ]])
        assert len(result) == 2
        
        # OR condition  
        result = self.runner.execute(["where", "data", [
            "or",
            ["=", "x", 5],
            ["=", "y", 10]
        ]])
        assert len(result) == 2
        
    def test_transform_basic(self):
        """Test basic transform operations."""
        self.runner.execute(["def", "user", ["@", {
            "name": "Alice",
            "age": 30,
            "email": "alice@example.com"
        }]])
        
        # Assign new field
        result = self.runner.execute([
            "transform", "user",
            ["assign", "@id", 123]
        ])
        assert result["id"] == 123
        assert result["name"] == "Alice"
        
        # Pick fields
        result = self.runner.execute([
            "transform", "user",
            ["pick", "@name", "@age"]
        ])
        assert set(result.keys()) == {"name", "age"}
        
        # Omit fields
        result = self.runner.execute([
            "transform", "user",
            ["omit", "@email"]
        ])
        assert "email" not in result
        assert "name" in result
        
    def test_transform_collection(self):
        """Test transform on collections."""
        self.runner.execute(["def", "users", ["@", [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]]])
        
        # Add field to all items
        result = self.runner.execute([
            "transform", "users",
            ["assign", "@active", True]
        ])
        assert len(result) == 2
        assert all(u["active"] is True for u in result)
        
    def test_pick_omit(self):
        """Test pick and omit operations with transform."""
        self.runner.execute(["def", "obj", ["@", {
            "a": 1, "b": 2, "c": 3, "d": 4
        }]])
        
        # pick and omit are now operators used with transform
        # They need field names as string literals
        result = self.runner.execute(["transform", "obj", ["pick", "@a", "@c"]])
        assert result == {"a": 1, "c": 3}
        
        result = self.runner.execute(["transform", "obj", ["omit", "@b", "@d"]])
        assert result == {"a": 1, "c": 3}
        
    def test_pluck(self):
        """Test pluck function."""
        self.runner.execute(["def", "items", ["@", [
            {"name": "A", "value": 1},
            {"name": "B", "value": 2},
            {"name": "C", "value": 3}
        ]]])
        
        names = self.runner.execute(["pluck", "items", "@name"])
        assert names == ["A", "B", "C"]
        
        values = self.runner.execute(["pluck", "items", "@value"])
        assert values == [1, 2, 3]
        
    def test_index_by(self):
        """Test index-by function."""
        self.runner.execute(["def", "items", ["@", [
            {"id": "a", "value": 1},
            {"id": "b", "value": 2}
        ]]])
        
        result = self.runner.execute(["index-by", "items", "@id"])
        assert "a" in result
        assert "b" in result
        assert result["a"]["value"] == 1
        assert result["b"]["value"] == 2
        
    def test_combined_operations(self):
        """Test combining where and transform."""
        self.runner.execute(["def", "products", ["@", [
            {"name": "Widget", "price": 29.99, "category": "tools"},
            {"name": "Gadget", "price": 99.99, "category": "electronics"},
            {"name": "Doohickey", "price": 19.99, "category": "tools"}
        ]]])
        
        # Filter then transform
        self.runner.execute(["def", "cheap_tools", [
            "transform",
            ["where", "products", ["=", "category", "@tools"]],
            ["pick", "@name", "@price"]
        ]])
        
        result = self.runner.execute("cheap_tools")
        assert len(result) == 2
        for item in result:
            assert set(item.keys()) == {"name", "price"}
            
        # Pluck names of tools
        names = self.runner.execute([
            "pluck",
            ["where", "products", ["=", "category", "@tools"]],
            "@name"
        ])
        assert names == ["Widget", "Doohickey"]


if __name__ == "__main__":
    pytest.main([__file__])