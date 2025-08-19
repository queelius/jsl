"""
Tests for the group-by function.
"""

import pytest
from jsl.runner import JSLRunner


class TestGroupBy:
    """Test cases for group-by function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = JSLRunner()
        
        # Create test data
        self.runner.execute(["def", "items", ["@", [
            {"name": "Alice", "age": 30, "role": "admin", "dept": "IT"},
            {"name": "Bob", "age": 25, "role": "user", "dept": "Sales"},
            {"name": "Charlie", "age": 35, "role": "admin", "dept": "IT"},
            {"name": "David", "age": 28, "role": "user", "dept": "Sales"},
            {"name": "Eve", "age": 32, "role": "moderator", "dept": "Support"}
        ]]])
        
        self.runner.execute(["def", "products", ["@", [
            {"name": "Widget", "price": 29.99, "category": "tools", "stock": 100},
            {"name": "Gadget", "price": 99.99, "category": "electronics", "stock": 50},
            {"name": "Doohickey", "price": 19.99, "category": "tools", "stock": 200},
            {"name": "Thingamajig", "price": 149.99, "category": "electronics", "stock": 25},
            {"name": "Whatsit", "price": 39.99, "category": "tools", "stock": 75}
        ]]])
    
    def test_group_by_simple_field(self):
        """Test grouping by a simple field."""
        result = self.runner.execute([
            "group-by",
            ["lambda", ["x"], ["get", "x", "@role"]],
            "items"
        ])
        
        assert "admin" in result
        assert "user" in result
        assert "moderator" in result
        assert len(result["admin"]) == 2
        assert len(result["user"]) == 2
        assert len(result["moderator"]) == 1
    
    def test_group_by_nested_field(self):
        """Test grouping by department."""
        result = self.runner.execute([
            "group-by",
            ["lambda", ["x"], ["get", "x", "@dept"]],
            "items"
        ])
        
        assert "IT" in result
        assert "Sales" in result
        assert "Support" in result
        assert len(result["IT"]) == 2
        assert len(result["Sales"]) == 2
        assert len(result["Support"]) == 1
    
    def test_group_by_computed_key(self):
        """Test grouping by a computed key."""
        # Group by age ranges
        self.runner.execute(["def", "age-range", ["lambda", ["x"],
            ["if", ["<", ["get", "x", "@age"], 30], "@under-30",
                ["if", ["<", ["get", "x", "@age"], 35], "@30-34", "@35-plus"]]]])
        
        result = self.runner.execute(["group-by", "age-range", "items"])
        
        assert "under-30" in result
        assert "30-34" in result
        assert "35-plus" in result
        assert len(result["under-30"]) == 2  # Bob (25), David (28)
        assert len(result["30-34"]) == 2  # Alice (30), Eve (32)
        assert len(result["35-plus"]) == 1  # Charlie (35)
    
    def test_group_by_multiple_criteria(self):
        """Test grouping by composite key."""
        # Group by category and stock level
        self.runner.execute(["def", "category-stock", ["lambda", ["x"],
            ["str-concat",
                ["get", "x", "@category"],
                "@-",
                ["if", ["<", ["get", "x", "@stock"], 50], "@low",
                    ["if", ["<", ["get", "x", "@stock"], 100], "@medium", "@high"]]]]])
        
        result = self.runner.execute(["group-by", "category-stock", "products"])
        
        assert "tools-high" in result
        assert "electronics-low" in result
        assert "electronics-medium" in result
        assert len(result["tools-high"]) == 2  # Widget (100), Doohickey (200)
        assert len(result["tools-medium"]) == 1  # Whatsit (75)
        assert len(result["electronics-medium"]) == 1  # Gadget (50)
        assert len(result["electronics-low"]) == 1  # Thingamajig (25)
    
    def test_group_by_with_transform(self):
        """Test combining group-by with transform operations."""
        # First group by category
        grouped = self.runner.execute([
            "group-by",
            ["lambda", ["x"], ["get", "x", "@category"]],
            "products"
        ])
        
        # Then calculate total value per category
        self.runner.execute(["def", "grouped", ["@", grouped]])
        
        # Calculate sum of prices for each group
        result = {}
        for category in grouped.keys():
            items = grouped[category]
            self.runner.execute(["def", "cat-items", ["@", items]])
            total = self.runner.execute([
                "reduce",
                "+",
                ["pluck", "cat-items", "@price"],
                0
            ])
            result[category] = total
        
        assert result["tools"] == pytest.approx(89.97, 0.01)  # 29.99 + 19.99 + 39.99
        assert result["electronics"] == pytest.approx(249.98, 0.01)  # 99.99 + 149.99
    
    def test_group_by_empty_list(self):
        """Test group-by with empty list."""
        result = self.runner.execute([
            "group-by",
            ["lambda", ["x"], ["get", "x", "@category"]],
            ["@", []]
        ])
        
        assert result == {}
    
    def test_group_by_single_group(self):
        """Test when all items map to the same key."""
        self.runner.execute(["def", "same-key", ["lambda", ["x"], "@same"]])
        
        result = self.runner.execute(["group-by", "same-key", "items"])
        
        assert len(result) == 1
        assert "same" in result
        assert len(result["same"]) == 5
    
    def test_group_by_with_where(self):
        """Test combining group-by with where filtering."""
        # First filter for high-value products
        self.runner.execute(["def", "expensive", [
            "where", "products", [">", "price", 30]
        ]])
        
        # Then group by category
        result = self.runner.execute([
            "group-by",
            ["lambda", ["x"], ["get", "x", "@category"]],
            "expensive"
        ])
        
        assert "tools" in result
        assert "electronics" in result
        assert len(result["tools"]) == 1  # Only Whatsit (39.99)
        assert len(result["electronics"]) == 2  # Gadget and Thingamajig
    
    def test_group_by_preserves_items(self):
        """Test that items in groups maintain all their fields."""
        result = self.runner.execute([
            "group-by",
            ["lambda", ["x"], ["get", "x", "@role"]],
            "items"
        ])
        
        # Check that items still have all their fields
        admin_items = result["admin"]
        assert all("name" in item for item in admin_items)
        assert all("age" in item for item in admin_items)
        assert all("role" in item for item in admin_items)
        assert all("dept" in item for item in admin_items)


if __name__ == "__main__":
    pytest.main([__file__])