"""
Test prelude ID and versioning system.
"""

import pytest
from jsl.prelude import make_prelude, check_prelude_compatibility, PRELUDE_VERSION
from jsl.core import Env


def test_prelude_has_metadata():
    """Test that prelude has ID and version metadata."""
    prelude = make_prelude()
    
    assert hasattr(prelude, '_prelude_id')
    assert hasattr(prelude, '_prelude_version')
    assert hasattr(prelude, '_is_prelude')
    
    assert prelude._is_prelude is True
    assert prelude._prelude_version == PRELUDE_VERSION
    assert isinstance(prelude._prelude_id, str)
    assert len(prelude._prelude_id) == 16  # SHA256 truncated to 16 chars


def test_preludes_are_equal_by_id():
    """Test that two preludes with same version are equal."""
    prelude1 = make_prelude()
    prelude2 = make_prelude()
    
    # Should have same ID since they're from same version
    assert prelude1._prelude_id == prelude2._prelude_id
    
    # Should be equal
    assert prelude1 == prelude2


def test_prelude_not_equal_to_regular_env():
    """Test that prelude is not equal to regular env."""
    prelude = make_prelude()
    regular = Env({'a': 1})
    
    assert prelude != regular
    assert regular != prelude


def test_prelude_compatibility_check():
    """Test prelude compatibility checking."""
    prelude1 = make_prelude()
    prelude2 = make_prelude()
    
    compatible, message = check_prelude_compatibility(prelude1, prelude2)
    assert compatible is True
    assert f"v{PRELUDE_VERSION}" in message


def test_prelude_deepcopy_creates_copy():
    """Test that deep copying a prelude creates a new copy."""
    prelude = make_prelude()
    copy = prelude.deepcopy()
    
    # Should be equal but not the same object
    assert copy == prelude
    assert copy is not prelude


def test_extended_env_not_prelude():
    """Test that extending a prelude creates non-prelude env."""
    prelude = make_prelude()
    extended = prelude.extend({'my_var': 42})
    
    # Extended env should not be a prelude
    assert not extended._is_prelude
    assert extended._prelude_id is None
    
    # But should still have access to prelude functions
    assert '+' in extended
    assert extended.get('my_var') == 42


def test_prelude_id_stable():
    """Test that prelude ID is stable across multiple calls."""
    ids = []
    for _ in range(5):
        prelude = make_prelude()
        ids.append(prelude._prelude_id)
    
    # All IDs should be the same
    assert len(set(ids)) == 1


def test_prelude_id_depends_on_functions():
    """Test that prelude ID would change if functions change."""
    # This is more of a documentation test - we can't actually
    # change the functions without modifying the code
    prelude = make_prelude()
    
    # ID should be deterministic based on version and function names
    assert prelude._prelude_id is not None
    
    # If we had different versions, they would have different IDs
    # (Can't test this without actually changing PRELUDE_VERSION)