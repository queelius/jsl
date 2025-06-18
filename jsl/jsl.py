"""
JSL (JSON Serializable Language) - A Network-Native Functional Language

JSL is a Lisp-like functional programming language designed from the ground up for 
network transmission and distributed computing. Unlike traditional languages that 
treat serialization as an afterthought, JSL makes wire-format compatibility a 
first-class design principle.

MOTIVATION AND DESIGN PHILOSOPHY
===============================

Modern distributed systems require seamless code mobility - the ability to send 
executable code across network boundaries, store it in databases, and reconstruct 
it in different runtime environments. Traditional approaches face fundamental 
challenges:

1. **Serialization Complexity**: Most languages require complex serialization 
   frameworks (pickle, protobuf, etc.) that are brittle, version-dependent, and 
   often insecure.

2. **Runtime Dependencies**: Serialized code often depends on specific runtime 
   versions, libraries, or execution contexts that may not be available on the 
   receiving end.

3. **Security Vulnerabilities**: Deserializing code often requires executing 
   arbitrary instructions, creating attack vectors.

4. **Platform Lock-in**: Serialization formats are often language-specific, 
   preventing cross-platform code sharing.

JSL solves these problems by making JSON the native representation of both data 
AND code. This creates several powerful properties:

THEORETICAL FOUNDATIONS
======================

**Homoiconicity**: Like classic Lisps, JSL code and data share the same 
representation. However, unlike S-expressions, JSL uses JSON - a universally 
supported, standardized format with existing tooling and security properties.

**Closure Serializability**: The most challenging aspect of code mobility is 
handling closures (functions that capture their lexical environment). JSL 
solves this by:
- Separating built-in primitives (non-serializable) from user code (serializable)
- Reconstructing closure environments by merging serialized user bindings with 
  a fresh prelude on the receiving end
- Using environment chaining to ensure closures always have access to built-ins

**Wire-Format Transparency**: Every JSL value can be serialized to JSON and 
reconstructed identically in any compliant runtime. This enables:
- Database storage of executable code
- HTTP transmission of functions
- Cross-language interoperability
- Audit trails of code execution

PRACTICAL APPLICATIONS
======================

1. **Distributed Computing**: Send computations to data rather than moving data 
   to computations
2. **Edge Computing**: Deploy code dynamically to edge nodes
3. **Database Functions**: Store and execute business logic directly in databases
4. **Microservices**: Share functional components across service boundaries
5. **Code as Configuration**: Express complex configurations as executable code
6. **Live Programming**: Update running systems by transmitting new code

IMPLEMENTATION ARCHITECTURE
===========================

The JSL runtime consists of three layers:

1. **Prelude Layer**: Non-serializable built-in functions (+, map, get, etc.) 
   that form the computational foundation
2. **User Layer**: Serializable functions and data defined by user programs
3. **Wire Layer**: JSON representation that can be transmitted and reconstructed

This separation ensures that transmitted code is always safe (contains no 
executable primitives) while remaining fully functional when reconstructed 
with a compatible prelude.

SECURITY MODEL
==============

JSL's security model is based on capability restriction:
- Transmitted code cannot contain arbitrary executable primitives
- All capabilities come from the receiving environment's prelude
- The prelude can be customized to provide only safe operations
- Code execution is deterministic and sandboxable

This makes JSL suitable for scenarios where traditional code mobility would 
be too dangerous, such as user-submitted code or cross-tenant execution.
"""

# Re-export all public components for backward compatibility
from .core import Env, Closure, prelude
from .prelude import make_prelude, eval_closure_or_builtin, reduce_jsl
from .evaluator import eval_expr, eval_template, find_free_variables
from .serialization import to_json, from_json, to_json_env_user_only, from_json_env_value, reconstruct_env
from .modules import load_module
from .runner import run_program, run_with_imports, main

# Export the main function for command-line usage
__all__ = [
    # Core data structures
    'Env', 'Closure', 'prelude',
    
    # Prelude and built-ins
    'make_prelude', 'eval_closure_or_builtin', 'reduce_jsl',
    
    # Evaluation engine
    'eval_expr', 'eval_template', 'find_free_variables',
    
    # Serialization
    'to_json', 'from_json', 'to_json_env_user_only', 'from_json_env_value', 'reconstruct_env',
    
    # Module system
    'load_module',
    
    # Program execution
    'run_program', 'run_with_imports', 'main'
]

# Legacy compatibility: maintain the same interface
if __name__ == "__main__":
    main()
