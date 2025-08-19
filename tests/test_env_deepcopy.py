"""
Test environment deep copy functionality.
"""

import pytest
from jsl.core import Env, Closure
from jsl.prelude import make_prelude


def test_deepcopy_simple():
    """Test deep copy of simple environment."""
    original = Env({'a': 1, 'b': [1, 2, 3]})
    copy = original.deepcopy()
    
    # Should be equal
    assert original == copy
    
    # But not the same object
    assert original is not copy
    
    # Modifying copy shouldn't affect original
    copy.define('c', 3)
    assert 'c' in copy
    assert 'c' not in original
    
    # Lists should be deep copied
    copy.bindings['b'].append(4)
    assert len(copy.bindings['b']) == 4
    assert len(original.bindings['b']) == 3


def test_deepcopy_with_parent():
    """Test deep copy flattens parent chain."""
    parent = Env({'a': 1})
    child = parent.extend({'b': 2})
    grandchild = child.extend({'c': 3})
    
    copy = grandchild.deepcopy()
    
    # Should have all values
    assert copy.get('a') == 1
    assert copy.get('b') == 2
    assert copy.get('c') == 3
    
    # But no parent chain - all values are in the single env
    assert copy.parent is None
    assert 'a' in copy.bindings
    assert 'b' in copy.bindings
    assert 'c' in copy.bindings


def test_deepcopy_with_closures():
    """Test deep copy of environment with closures."""
    prelude = make_prelude()
    original = prelude.extend({'scale': 10})
    
    closure = Closure(
        params=['n'],
        body=['*', 'n', 'scale'],
        env=original
    )
    original.define('scale_func', closure)
    
    # Deep copy
    copy = original.deepcopy()
    
    # Should have the closure
    assert 'scale_func' in copy
    copy_closure = copy.get('scale_func')
    assert isinstance(copy_closure, Closure)
    
    # Closure should point to the new environment
    assert copy_closure.env is copy
    
    # Modifying copy shouldn't affect original
    copy.define('scale', 20)
    assert copy.get('scale') == 20
    assert original.get('scale') == 10
    
    # The closures should see different values
    assert copy_closure.env.get('scale') == 20
    assert closure.env.get('scale') == 10


def test_deepcopy_mutual_recursion():
    """Test deep copy preserves mutual recursion."""
    prelude = make_prelude()
    original = prelude.extend({})
    
    even = Closure(
        params=['n'],
        body=['if', ['=', 'n', 0], True, ['odd', ['-', 'n', 1]]],
        env=original
    )
    
    odd = Closure(
        params=['n'],
        body=['if', ['=', 'n', 0], False, ['even', ['-', 'n', 1]]],
        env=original
    )
    
    original.define('even', even)
    original.define('odd', odd)
    
    # Deep copy
    copy = original.deepcopy()
    
    # Should have both functions
    assert 'even' in copy
    assert 'odd' in copy
    
    copy_even = copy.get('even')
    copy_odd = copy.get('odd')
    
    # Both should be closures pointing to the copy env
    assert isinstance(copy_even, Closure)
    assert isinstance(copy_odd, Closure)
    assert copy_even.env is copy
    assert copy_odd.env is copy
    
    # They should see each other
    assert copy_even.env.get('odd') is copy_odd
    assert copy_odd.env.get('even') is copy_even
    
    # Original closures should still point to original env
    assert even.env is original
    assert odd.env is original


def test_deepcopy_preserves_prelude():
    """Test that deep copy preserves all prelude functions."""
    prelude = make_prelude()
    original = prelude.extend({'my_var': 42})
    
    copy = original.deepcopy()
    
    # Should have all prelude functions
    assert '+' in copy
    assert 'map' in copy
    assert 'filter' in copy
    
    # And the custom variable
    assert 'my_var' in copy
    assert copy.get('my_var') == 42
    
    # Modifying copy shouldn't affect original
    copy.define('my_var', 100)
    assert copy.get('my_var') == 100
    assert original.get('my_var') == 42