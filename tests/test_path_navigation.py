"""
Unit tests for JSON path navigation functions in JSL.
"""

import pytest
from jsl.runner import JSLRunner


class TestPathNavigation:
    """Test cases for deep path navigation operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = JSLRunner()
        
        # Create test data structure using quote to avoid evaluation
        self.runner.execute(["def", "user", ["@", {
            "name": "John Doe",
            "age": 30,
            "address": {
                "street": "123 Main St",
                "city": "New York",
                "country": "USA",
                "coordinates": {
                    "lat": 40.7128,
                    "lng": -74.0060
                }
            },
            "emails": [
                "john@example.com",
                "john.doe@work.com"
            ],
            "orders": [
                {
                    "id": 1,
                    "total": 99.99,
                    "items": [
                        {"name": "Widget", "price": 29.99},
                        {"name": "Gadget", "price": 69.99}
                    ]
                },
                {
                    "id": 2,
                    "total": 149.99,
                    "items": [
                        {"name": "Doohickey", "price": 149.99}
                    ]
                }
            ]
        }]])
    
    def test_get_path_simple(self):
        """Test simple path access."""
        # Direct property access
        result = self.runner.execute(["get-path", "user", "@name"])
        assert result == "John Doe"
        
        result = self.runner.execute(["get-path", "user", "@age"])
        assert result == 30
    
    def test_get_path_nested(self):
        """Test nested path access."""
        # Nested object access
        result = self.runner.execute(["get-path", "user", "@address.city"])
        assert result == "New York"
        
        result = self.runner.execute(["get-path", "user", "@address.coordinates.lat"])
        assert result == 40.7128
        
        # Deep nesting
        result = self.runner.execute(["get-path", "user", "@address.coordinates.lng"])
        assert result == -74.0060
    
    def test_get_path_array_access(self):
        """Test array index access in paths."""
        # Array index with dot notation
        result = self.runner.execute(["get-path", "user", "@emails.0"])
        assert result == "john@example.com"
        
        result = self.runner.execute(["get-path", "user", "@emails.1"])
        assert result == "john.doe@work.com"
        
        # Nested arrays
        result = self.runner.execute(["get-path", "user", "@orders.0.id"])
        assert result == 1
        
        result = self.runner.execute(["get-path", "user", "@orders.1.total"])
        assert result == 149.99
        
        # Array within array
        result = self.runner.execute(["get-path", "user", "@orders.0.items.0.name"])
        assert result == "Widget"
        
        result = self.runner.execute(["get-path", "user", "@orders.0.items.1.price"])
        assert result == 69.99
    
    def test_get_path_bracket_notation(self):
        """Test bracket notation for array access."""
        # Bracket notation should also work
        result = self.runner.execute(["get-path", "user", "@emails[0]"])
        assert result == "john@example.com"
        
        result = self.runner.execute(["get-path", "user", "@orders[0].items[1].name"])
        assert result == "Gadget"
    
    def test_get_path_wildcard(self):
        """Test wildcard path access."""
        # Get all values from object
        result = self.runner.execute(["get-path", {"@a": 1, "@b": 2, "@c": 3}, "@*"])
        assert set(result) == {1, 2, 3}
        
        # Get all items from array (need to quote the array)
        result = self.runner.execute(["get-path", ["@", ["@a", "@b", "@c"]], "@*"])
        assert result == ["@a", "@b", "@c"]
    
    def test_get_path_errors(self):
        """Test error handling for invalid paths."""
        # Non-existent key
        with pytest.raises(Exception) as exc_info:
            self.runner.execute(["get-path", "user", "@nonexistent"])
        assert "Key" in str(exc_info.value) or "not found" in str(exc_info.value)
        
        # Invalid array index
        with pytest.raises(Exception) as exc_info:
            self.runner.execute(["get-path", "user", "@emails.5"])
        assert "Index" in str(exc_info.value) or "out of range" in str(exc_info.value)
        
        # Type mismatch
        with pytest.raises(Exception) as exc_info:
            self.runner.execute(["get-path", "user", "@name.city"])
        assert "Cannot navigate" in str(exc_info.value) or "Type" in str(exc_info.value)
    
    def test_set_path_simple(self):
        """Test simple path setting."""
        # Set top-level property
        self.runner.execute(["def", "updated", ["set-path", "user", "@name", "@Jane Doe"]])
        assert self.runner.execute(["get-path", "updated", "@name"]) == "Jane Doe"
        
        # Original should be unchanged
        assert self.runner.execute(["get-path", "user", "@name"]) == "John Doe"
    
    def test_set_path_nested(self):
        """Test nested path setting."""
        # Set nested property
        self.runner.execute(["def", "updated", ["set-path", "user", "@address.city", "@Boston"]])
        assert self.runner.execute(["get-path", "updated", "@address.city"]) == "Boston"
        
        # Other properties should remain
        assert self.runner.execute(["get-path", "updated", "@address.street"]) == "123 Main St"
    
    def test_set_path_array(self):
        """Test setting values in arrays."""
        # Set array element
        self.runner.execute(["def", "updated", ["set-path", "user", "@emails.0", "@jane@example.com"]])
        assert self.runner.execute(["get-path", "updated", "@emails.0"]) == "jane@example.com"
        assert self.runner.execute(["get-path", "updated", "@emails.1"]) == "john.doe@work.com"
        
        # Set nested array element
        self.runner.execute(["def", "updated2", ["set-path", "user", "@orders.0.items.0.price", 19.99]])
        assert self.runner.execute(["get-path", "updated2", "@orders.0.items.0.price"]) == 19.99
    
    def test_set_path_auto_create(self):
        """Test auto-creation of intermediate objects."""
        # Start with empty object
        self.runner.execute(["def", "new_obj", ["set-path", {}, "@user.profile.name", "@Test"]])
        assert self.runner.execute(["get-path", "new_obj", "@user.profile.name"]) == "Test"
        
        # Verify structure was created
        assert self.runner.execute(["has-path", "new_obj", "@user"]) is True
        assert self.runner.execute(["has-path", "new_obj", "@user.profile"]) is True
    
    def test_has_path(self):
        """Test path existence checking."""
        # Existing paths
        assert self.runner.execute(["has-path", "user", "@name"]) is True
        assert self.runner.execute(["has-path", "user", "@address.city"]) is True
        assert self.runner.execute(["has-path", "user", "@emails.0"]) is True
        assert self.runner.execute(["has-path", "user", "@orders.0.items.1.price"]) is True
        
        # Non-existing paths
        assert self.runner.execute(["has-path", "user", "@nonexistent"]) is False
        assert self.runner.execute(["has-path", "user", "@address.state"]) is False
        assert self.runner.execute(["has-path", "user", "@emails.10"]) is False
        assert self.runner.execute(["has-path", "user", "@name.foo"]) is False
    
    def test_get_safe(self):
        """Test safe path access with defaults."""
        # Existing path returns value
        result = self.runner.execute(["get-safe", "user", "@name"])
        assert result == "John Doe"
        
        # Non-existing path returns None
        result = self.runner.execute(["get-safe", "user", "@nonexistent"])
        assert result is None
        
        # With custom default
        result = self.runner.execute(["get-safe", "user", "@nonexistent", "@default"])
        assert result == "default"
        
        # Invalid navigation returns default
        result = self.runner.execute(["get-safe", "user", "@name.invalid", "@fallback"])
        assert result == "fallback"
    
    def test_get_default(self):
        """Test get-default alias."""
        # Existing path
        result = self.runner.execute(["get-default", "user", "@name", "@default"])
        assert result == "John Doe"
        
        # Non-existing path
        result = self.runner.execute(["get-default", "user", "@missing", "@default"])
        assert result == "default"
    
    def test_path_navigation_in_expressions(self):
        """Test path navigation in larger expressions."""
        # Use in conditionals
        result = self.runner.execute([
            "if",
            ["has-path", "user", "@address.city"],
            ["get-path", "user", "@address.city"],
            "@No city"
        ])
        assert result == "New York"
        
        # Map over nested array using paths
        result = self.runner.execute([
            "map",
            ["lambda", ["order"], ["get-path", "order", "@total"]],
            ["get-path", "user", "@orders"]
        ])
        assert result == [99.99, 149.99]
        
        # Filter based on nested values
        self.runner.execute(["def", "products", ["@", [
            {"name": "Widget", "category": "tools", "price": 29.99},
            {"name": "Gadget", "category": "electronics", "price": 99.99},
            {"name": "Doohickey", "category": "tools", "price": 19.99}
        ]]])
        
        self.runner.execute(["def", "filtered", [
            "filter",
            ["lambda", ["product"], [
                "=",
                ["get-path", "product", "@category"],
                "@tools"
            ]],
            "products"
        ]])
        
        result = self.runner.execute("filtered")
        assert len(result) == 2
        # First element should be the Widget
        assert self.runner.execute(["get-path", ["first", "filtered"], "@name"]) == "Widget"
    
    def test_complex_path_operations(self):
        """Test complex combinations of path operations."""
        # Update nested value and check
        self.runner.execute(["def", "updated", [
            "set-path",
            "user",
            "@orders.0.status",
            "@completed"
        ]])
        
        assert self.runner.execute(["has-path", "updated", "@orders.0.status"]) is True
        assert self.runner.execute(["get-path", "updated", "@orders.0.status"]) == "completed"
        
        # Chain multiple set-path operations
        self.runner.execute(["def", "chained", [
            "set-path",
            ["set-path", "user", "@verified", True],
            "@lastLogin",
            "@2024-01-01"
        ]])
        
        assert self.runner.execute(["get-path", "chained", "@verified"]) is True
        assert self.runner.execute(["get-path", "chained", "@lastLogin"]) == "2024-01-01"
        
        # Use with reduce to collect nested values
        total = self.runner.execute([
            "reduce",
            ["lambda", ["sum", "order"], [
                "+", "sum", ["get-path", "order", "@total"]
            ]],
            ["get-path", "user", "@orders"],
            0
        ])
        assert abs(total - 249.98) < 0.001  # 99.99 + 149.99 (with floating point tolerance)


if __name__ == "__main__":
    pytest.main([__file__])