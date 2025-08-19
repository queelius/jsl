"""
Test the public API surface of the jsl package.

This ensures all documented exports are available and work as expected.
"""

import unittest


class TestPublicAPI(unittest.TestCase):
    """Test that the public API is properly exposed."""
    
    def test_imports_from_package(self):
        """Test that all public exports can be imported from jsl package."""
        # Core imports
        from jsl import (
            Env,
            Closure,
            Evaluator,
            HostDispatcher,
            JSLError,
            SymbolNotFoundError,
            JSLTypeError,
            JSLValue,
            JSLExpression,
        )
        
        # High-level API
        from jsl import (
            JSLRunner,
            run_program,
            eval_expression,
        )
        
        # Serialization
        from jsl import (
            serialize,
            deserialize,
            to_json,
            from_json,
        )
        
        # Prelude
        from jsl import make_prelude
        
        # Version info
        from jsl import __version__, __author__, __license__
        
        # Basic smoke tests
        self.assertIsNotNone(Env)
        self.assertIsNotNone(JSLRunner)
        self.assertIsNotNone(eval_expression)
        
    def test_jslrunner_basic_usage(self):
        """Test that JSLRunner works from package-level import."""
        from jsl import JSLRunner
        
        runner = JSLRunner()
        result = runner.execute('["+", 1, 2, 3]')
        self.assertEqual(result, 6)
        
    def test_eval_expression_basic_usage(self):
        """Test that eval_expression works from package-level import."""
        from jsl import eval_expression
        
        result = eval_expression('["+", 5, 10]')
        self.assertEqual(result, 15)
        
    def test_run_program_basic_usage(self):
        """Test that run_program works from package-level import."""
        from jsl import run_program
        
        program = '''
        ["do",
          ["def", "x", 10],
          ["*", "x", 2]
        ]
        '''
        result = run_program(program)
        self.assertEqual(result, 20)
        
    def test_readme_examples(self):
        """Test that README examples work as documented."""
        from jsl import JSLRunner
        
        runner = JSLRunner()
        
        # JSON array syntax
        result = runner.execute('["+", 1, 2, 3]')
        self.assertEqual(result, 6)
        
        # Lisp-style syntax
        result = runner.execute('(+ 1 2 3)')
        self.assertEqual(result, 6)
        
        # Function definition
        program = '''
        (do
          (def square (lambda (x) (* x x)))
          (square 5))
        '''
        result = runner.execute(program)
        self.assertEqual(result, 25)
        
        # Query operations
        runner.execute('[\"def\", \"data\", [\"@\", [{"name": "Alice", "role": "admin"}, {"name": "Bob", "role": "user"}]]]')
        
        admins = runner.execute('[\"where\", \"data\", [\"=\", \"role\", \"@admin\"]]')
        self.assertEqual(len(admins), 1)
        self.assertEqual(admins[0]['name'], 'Alice')
        
        names = runner.execute('[\"transform\", \"data\", [\"pick\", \"@name\"]]')
        self.assertEqual(len(names), 2)
        self.assertEqual(names[0], {'name': 'Alice'})
        self.assertEqual(names[1], {'name': 'Bob'})
        
    def test_version_info(self):
        """Test that version information is available."""
        from jsl import __version__, __author__, __license__
        
        self.assertIsInstance(__version__, str)
        self.assertEqual(__version__, "0.2.0")
        self.assertEqual(__author__, "Alex Towell")
        self.assertEqual(__license__, "MIT")


if __name__ == "__main__":
    unittest.main()