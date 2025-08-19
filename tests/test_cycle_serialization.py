"""
Test serialization and deserialization of complex environments with cycles.
"""

import pytest
import json
from jsl.core import Env, Closure
from jsl.serialization import ContentAddressableSerializer, ContentAddressableDeserializer
from jsl.prelude import make_prelude


def test_simple_closure_cycle():
    """Test serialization of a closure that references its own environment."""
    # Create environment with a variable
    prelude = make_prelude()
    env = prelude.extend({'x': 42})
    
    # Create closure that references x
    closure = Closure(
        params=['n'],
        body=['+', 'n', 'x'],
        env=env
    )
    
    # Add closure to environment (creating cycle: env -> closure -> env)
    env.define('add_x', closure)
    
    # Serialize
    serializer = ContentAddressableSerializer()
    json_str = serializer.serialize(env)
    
    # Deserialize
    deserializer = ContentAddressableDeserializer(make_prelude())
    restored_env = deserializer.deserialize(json_str)
    
    # Verify structure
    assert 'x' in restored_env
    assert 'add_x' in restored_env
    assert restored_env.get('x') == 42
    
    # Verify closure
    restored_closure = restored_env.get('add_x')
    assert isinstance(restored_closure, Closure)
    assert restored_closure.params == ['n']
    assert restored_closure.body == ['+', 'n', 'x']
    
    # Verify closure's env points back correctly
    assert restored_closure.env is not None
    assert 'x' in restored_closure.env
    assert restored_closure.env.get('x') == 42
    


def test_nested_closures():
    """Test serialization of nested closures with mutual references."""
    prelude = make_prelude()
    env = prelude.extend({'scale': 10})
    
    # Create first closure
    multiply_by_scale = Closure(
        params=['n'],
        body=['*', 'n', 'scale'],
        env=env
    )
    env.define('multiply', multiply_by_scale)
    
    # Create second closure that uses the first
    double_multiply = Closure(
        params=['n'],
        body=['multiply', ['*', 'n', 2]],
        env=env
    )
    env.define('double_multiply', double_multiply)
    
    # Serialize
    serializer = ContentAddressableSerializer()
    json_str = serializer.serialize(env)
    
    # Deserialize
    deserializer = ContentAddressableDeserializer(make_prelude())
    restored_env = deserializer.deserialize(json_str)
    
    # Verify all elements are present
    assert 'scale' in restored_env
    assert 'multiply' in restored_env
    assert 'double_multiply' in restored_env
    
    # Verify first closure
    multiply = restored_env.get('multiply')
    assert isinstance(multiply, Closure)
    assert 'scale' in multiply.env
    
    # Verify second closure
    double = restored_env.get('double_multiply')
    assert isinstance(double, Closure)
    assert 'multiply' in double.env
    
    # Verify they share the same environment
    assert double.env.get('scale') == 10
    assert isinstance(double.env.get('multiply'), Closure)
    
    print("✓ Nested closures test passed")


def test_mutual_recursion():
    """Test mutually recursive closures."""
    prelude = make_prelude()
    env = prelude.extend({})
    
    # Create mutually recursive even/odd functions
    # even(n) = if n == 0 then true else odd(n-1)
    # odd(n) = if n == 0 then false else even(n-1)
    
    even = Closure(
        params=['n'],
        body=['if', ['=', 'n', 0], True, ['odd', ['-', 'n', 1]]],
        env=env
    )
    
    odd = Closure(
        params=['n'],
        body=['if', ['=', 'n', 0], False, ['even', ['-', 'n', 1]]],
        env=env
    )
    
    env.define('even', even)
    env.define('odd', odd)
    
    # Serialize
    serializer = ContentAddressableSerializer()
    json_str = serializer.serialize(env)
    
    # Deserialize
    deserializer = ContentAddressableDeserializer(make_prelude())
    restored_env = deserializer.deserialize(json_str)
    
    # Verify both functions exist
    assert 'even' in restored_env
    assert 'odd' in restored_env
    
    restored_even = restored_env.get('even')
    restored_odd = restored_env.get('odd')
    
    assert isinstance(restored_even, Closure)
    assert isinstance(restored_odd, Closure)
    
    # Verify they can see each other
    assert 'odd' in restored_even.env
    assert 'even' in restored_odd.env
    
    print("✓ Mutual recursion test passed")


def test_deeply_nested_environments():
    """Test serialization of deeply nested environment chains."""
    # Create base environment
    prelude = make_prelude()
    base_env = prelude.extend({'a': 1})
    
    # Create nested environments
    env1 = base_env.extend({'b': 2})
    env2 = env1.extend({'c': 3})
    env3 = env2.extend({'d': 4})
    
    # Create closure at each level
    closure1 = Closure(['x'], ['+', 'x', 'a'], env1)
    closure2 = Closure(['x'], ['+', 'x', 'b'], env2)
    closure3 = Closure(['x'], ['+', 'x', 'c'], env3)
    
    env3.define('f1', closure1)
    env3.define('f2', closure2)
    env3.define('f3', closure3)
    
    # Serialize the deepest environment
    serializer = ContentAddressableSerializer()
    json_str = serializer.serialize(env3)
    
    # Deserialize
    deserializer = ContentAddressableDeserializer(make_prelude())
    restored_env = deserializer.deserialize(json_str)
    
    # Verify all levels are accessible
    assert restored_env.get('a') == 1  # From base
    assert restored_env.get('b') == 2  # From env1
    assert restored_env.get('c') == 3  # From env2
    assert restored_env.get('d') == 4  # From env3
    
    # Verify closures
    f1 = restored_env.get('f1')
    f2 = restored_env.get('f2')
    f3 = restored_env.get('f3')
    
    assert isinstance(f1, Closure)
    assert isinstance(f2, Closure)
    assert isinstance(f3, Closure)
    
    # Each closure should see the right variables
    # f1 was created in env1, so it sees a and b
    assert 'a' in f1.env
    assert 'b' in f1.env
    
    # f2 was created in env2, so it sees a, b, and c  
    assert 'a' in f2.env
    assert 'b' in f2.env
    assert 'c' in f2.env
    
    # f3 was created in env3, so it sees a, b, c, and d
    assert 'a' in f3.env
    assert 'b' in f3.env
    assert 'c' in f3.env
    assert 'd' in f3.env
    
    print("✓ Deeply nested environments test passed")


if __name__ == "__main__":
    test_simple_closure_cycle()
    test_nested_closures()
    test_mutual_recursion()
    test_deeply_nested_environments()
    print("\n✅ All cycle serialization tests passed!")