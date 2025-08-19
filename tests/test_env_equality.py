"""
Test environment equality and serialization roundtrip.
"""

import pytest
from jsl.core import Env, Closure
from jsl.serialization import serialize, deserialize
from jsl.prelude import make_prelude


def test_env_equality_basic():
    """Test basic environment equality."""
    env1 = Env({'a': 1, 'b': 2})
    env2 = Env({'a': 1, 'b': 2})
    env3 = Env({'a': 1, 'b': 3})
    
    assert env1 == env2
    assert env1 != env3


def test_env_equality_with_parent():
    """Test environment equality with parent chains."""
    parent = Env({'a': 1})
    env1 = parent.extend({'b': 2})
    env2 = parent.extend({'b': 2})
    
    assert env1 == env2
    
    # Create equivalent env without shared parent
    standalone = Env({'a': 1, 'b': 2})
    assert env1 == standalone


def test_env_equality_with_closures():
    """Test environment equality with closures."""
    env1 = Env({'x': 10})
    closure1 = Closure(['n'], ['+', 'n', 'x'], env1)
    env1.define('add_x', closure1)
    
    env2 = Env({'x': 10})
    closure2 = Closure(['n'], ['+', 'n', 'x'], env2)
    env2.define('add_x', closure2)
    
    assert env1 == env2


def test_serialization_roundtrip_simple():
    """Test that simple env survives serialization roundtrip."""
    prelude = make_prelude()
    original = prelude.extend({'my_var': 42, 'my_list': [1, 2, 3]})
    
    # Serialize and deserialize
    json_str = serialize(original)
    restored = deserialize(json_str, make_prelude())
    
    # Should be equal
    assert original == restored


def test_serialization_roundtrip_with_closure():
    """Test that env with closures survives serialization roundtrip."""
    prelude = make_prelude()
    original = prelude.extend({'scale': 10})
    
    closure = Closure(
        params=['n'],
        body=['*', 'n', 'scale'],
        env=original
    )
    original.define('scale_func', closure)
    
    # Serialize and deserialize
    json_str = serialize(original)
    restored = deserialize(json_str, make_prelude())
    
    # Check structural equality
    assert 'scale' in restored
    assert 'scale_func' in restored
    assert restored.get('scale') == 10
    
    restored_closure = restored.get('scale_func')
    assert isinstance(restored_closure, Closure)
    assert restored_closure.params == ['n']
    assert restored_closure.body == ['*', 'n', 'scale']
    
    # The closure's env should see scale
    assert 'scale' in restored_closure.env
    assert restored_closure.env.get('scale') == 10


def test_serialization_roundtrip_mutual_recursion():
    """Test mutually recursive closures survive serialization."""
    prelude = make_prelude()
    original = prelude.extend({})
    
    # Create mutually recursive functions
    is_even = Closure(
        params=['n'],
        body=['if', ['=', 'n', 0], True, ['is_odd', ['-', 'n', 1]]],
        env=original
    )
    
    is_odd = Closure(
        params=['n'],
        body=['if', ['=', 'n', 0], False, ['is_even', ['-', 'n', 1]]],
        env=original
    )
    
    original.define('is_even', is_even)
    original.define('is_odd', is_odd)
    
    # Serialize and deserialize
    json_str = serialize(original)
    restored = deserialize(json_str, make_prelude())
    
    # Verify structure
    assert 'is_even' in restored
    assert 'is_odd' in restored
    
    restored_even = restored.get('is_even')
    restored_odd = restored.get('is_odd')
    
    # Both should be closures
    assert isinstance(restored_even, Closure)
    assert isinstance(restored_odd, Closure)
    
    # They should see each other in their environments
    assert 'is_odd' in restored_even.env
    assert 'is_even' in restored_odd.env
    
    # The actual functions they see should be closures
    assert isinstance(restored_even.env.get('is_odd'), Closure)
    assert isinstance(restored_odd.env.get('is_even'), Closure)


def test_complex_environment_roundtrip():
    """Test complex nested environment with multiple closures."""
    prelude = make_prelude()
    base = prelude.extend({'global_scale': 100})
    
    # Create nested environments with closures at each level
    level1 = base.extend({'x': 10})
    closure1 = Closure(['n'], ['*', 'n', 'x'], level1)
    level1.define('multiply_x', closure1)
    
    level2 = level1.extend({'y': 20})
    closure2 = Closure(['n'], ['+', ['multiply_x', 'n'], 'y'], level2)
    level2.define('transform', closure2)
    
    level3 = level2.extend({'z': 30})
    closure3 = Closure(
        ['n'], 
        ['+', ['transform', 'n'], ['*', 'z', 'global_scale']], 
        level3
    )
    level3.define('complex_calc', closure3)
    
    # Serialize the deepest level
    json_str = serialize(level3)
    restored = deserialize(json_str, make_prelude())
    
    # Verify all bindings are accessible
    assert restored.get('global_scale') == 100
    assert restored.get('x') == 10
    assert restored.get('y') == 20
    assert restored.get('z') == 30
    
    # Verify all closures are present and correct
    assert 'multiply_x' in restored
    assert 'transform' in restored
    assert 'complex_calc' in restored
    
    # Each closure should see the right variables
    multiply_x = restored.get('multiply_x')
    assert isinstance(multiply_x, Closure)
    assert 'x' in multiply_x.env
    assert 'global_scale' in multiply_x.env
    
    transform = restored.get('transform')
    assert isinstance(transform, Closure)
    assert 'x' in transform.env
    assert 'y' in transform.env
    assert 'multiply_x' in transform.env
    
    complex_calc = restored.get('complex_calc')
    assert isinstance(complex_calc, Closure)
    assert 'z' in complex_calc.env
    assert 'transform' in complex_calc.env
    assert 'global_scale' in complex_calc.env