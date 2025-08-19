"""
Unit tests for regex functions in JSL.
"""

import pytest
from jsl.runner import JSLRunner


class TestRegexFunctions:
    """Test cases for regex string operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = JSLRunner()
    
    def test_str_matches_basic(self):
        """Test basic pattern matching."""
        # Simple match
        result = self.runner.execute(["str-matches", "@hello world", "@hello"])
        assert result is True
        
        # No match
        result = self.runner.execute(["str-matches", "@hello world", "@goodbye"])
        assert result is False
        
        # Regex pattern with metacharacters
        result = self.runner.execute(["str-matches", "@test123", "@test\\d+"])
        assert result is True
        
        # Pattern at end
        result = self.runner.execute(["str-matches", "@hello world", "@world$"])
        assert result is True
        
        # Pattern at start
        result = self.runner.execute(["str-matches", "@hello world", "@^hello"])
        assert result is True
    
    def test_str_matches_complex_patterns(self):
        """Test complex regex patterns."""
        # Email pattern
        email_pattern = "@[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
        result = self.runner.execute(["str-matches", "@user@example.com", email_pattern])
        assert result is True
        
        result = self.runner.execute(["str-matches", "@invalid-email", email_pattern])
        assert result is False
        
        # Phone number pattern
        phone_pattern = "@\\d{3}-\\d{3}-\\d{4}"
        result = self.runner.execute(["str-matches", "@555-123-4567", phone_pattern])
        assert result is True
        
        result = self.runner.execute(["str-matches", "@55-123-4567", phone_pattern])
        assert result is False
    
    def test_str_replace_basic(self):
        """Test basic string replacement with regex."""
        # Simple replacement
        result = self.runner.execute(["str-replace", "@hello world", "@world", "@universe"])
        assert result == "hello universe"
        
        # Replace all digits
        result = self.runner.execute(["str-replace", "@test123abc456", "@\\d+", "@XXX"])
        assert result == "testXXXabcXXX"
        
        # Replace with backreference
        result = self.runner.execute(["str-replace", "@hello world", "@(\\w+) (\\w+)", "@\\2 \\1"])
        assert result == "world hello"
    
    def test_str_replace_with_count(self):
        """Test string replacement with count limit."""
        # Replace only first match
        result = self.runner.execute(["str-replace", "@aaabbbccc", "@a", "@X", 1])
        assert result == "Xaabbbccc"
        
        # Replace first two matches
        result = self.runner.execute(["str-replace", "@aaabbbccc", "@a", "@X", 2])
        assert result == "XXabbbccc"
        
        # Replace all (count=0 is default)
        result = self.runner.execute(["str-replace", "@aaabbbccc", "@a", "@X", 0])
        assert result == "XXXbbbccc"
    
    def test_str_find_all(self):
        """Test finding all pattern matches."""
        # Find all words
        result = self.runner.execute(["str-find-all", "@hello world from jsl", "@\\w+"])
        assert result == ["hello", "world", "from", "jsl"]
        
        # Find all numbers
        result = self.runner.execute(["str-find-all", "@test123and456plus789", "@\\d+"])
        assert result == ["123", "456", "789"]
        
        # Find with groups (returns lists when using groups)
        result = self.runner.execute(["str-find-all", "@a1b2c3", "@([a-z])(\\d)"])
        assert result == [["a", "1"], ["b", "2"], ["c", "3"]]
        
        # No matches
        result = self.runner.execute(["str-find-all", "@hello world", "@\\d+"])
        assert result == []
    
    def test_regex_with_flags(self):
        """Test regex with flags (case insensitive)."""
        # Case insensitive flag (re.IGNORECASE = 2)
        result = self.runner.execute(["str-matches", "@Hello World", "@hello", 2])
        assert result is True
        
        # Without flag should not match
        result = self.runner.execute(["str-matches", "@Hello World", "@hello", 0])
        assert result is False
        
        # Find all with case insensitive
        result = self.runner.execute(["str-find-all", "@HeLLo WoRLd", "@hello|world", 2])
        assert result == ["HeLLo", "WoRLd"]
    
    def test_regex_in_expressions(self):
        """Test regex functions in larger expressions."""
        # Filter list using regex
        self.runner.execute(["def", "emails", ["@", [
            "@user@example.com",
            "@invalid-email",
            "@admin@test.org",
            "@not-an-email"
        ]]])
        
        result = self.runner.execute([
            "filter",
            ["lambda", ["email"], [
                "str-matches", 
                "email", 
                "@[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
            ]],
            "emails"
        ])
        assert result == ["@user@example.com", "@admin@test.org"]
        
        # Map with replacement
        self.runner.execute(["def", "codes", ["@", ["@ABC-123", "@DEF-456", "@GHI-789"]]])
        result = self.runner.execute([
            "map",
            ["lambda", ["code"], ["str-replace", "code", "@([A-Z]+)-(\\d+)", "@\\2:\\1"]],
            "codes"
        ])
        assert result == ["@123:ABC", "@456:DEF", "@789:GHI"]
    
    def test_regex_error_handling(self):
        """Test error handling for invalid regex patterns."""
        # Invalid regex pattern
        with pytest.raises(Exception) as exc_info:
            self.runner.execute(["str-matches", "@test", "@["])
        assert "Invalid regex pattern" in str(exc_info.value)
        
        # Invalid replacement pattern  
        with pytest.raises(Exception) as exc_info:
            self.runner.execute(["str-replace", "@test", "@[", "@replacement"])
        assert "Invalid regex pattern" in str(exc_info.value)
        
        # Invalid find-all pattern
        with pytest.raises(Exception) as exc_info:
            self.runner.execute(["str-find-all", "@test", "@("])
        assert "Invalid regex pattern" in str(exc_info.value)
    
    def test_regex_with_special_chars(self):
        """Test regex with special characters."""
        # Escape special chars in pattern
        result = self.runner.execute(["str-matches", "@$100.50", "@\\$\\d+\\.\\d+"])
        assert result is True
        
        # Match parentheses
        result = self.runner.execute(["str-matches", "@(hello)", "@\\(.*\\)"])
        assert result is True
        
        # Match brackets
        result = self.runner.execute(["str-matches", "@[test]", "@\\[.*\\]"])
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__])