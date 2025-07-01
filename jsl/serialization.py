import json
from typing import Any, Union

from .core import Env, Closure

JSON = Union[int, float, str, bool, None, list, dict]
JSL = Union[int, float, str, bool, None, list, dict, Closure, Env]

def jsl_to_json(x: JSL) -> JSON:
    """
    Converts a JSL type to a JSON type.
    """
    if isinstance(x, (int, float, str, bool)) or x is None:
        return x
    elif isinstance(x, list):
        return [jsl_to_json(item) for item in x]
    elif isinstance(x, dict):
        return {k: jsl_to_json(v) for k, v in x.items()}
    elif isinstance(x, Closure):
        # Special handling for closures - will be handled by JSLEncoder
        return x
    else:
        raise TypeError(f"Object of type {type(x)} is not JSON serializable")


def json_to_jsl(x: JSON) -> JSL:
    """
    Converts a JSON type to a JSL type.
    """
    if isinstance(x, (int, float, str, bool)) or x is None:
        return x
    elif isinstance(x, list):
        return [json_to_jsl(item) for item in x]
    elif isinstance(x, dict):
        return {k: json_to_jsl(v) for k, v in x.items()}
    else:
        raise TypeError(f"Object of type {type(x)} is not JSL deserializable")


class JSLEncoder(json.JSONEncoder):
    """
    A JSON encoder for JSL types including closures.
    """
    def default(self, o: Any) -> Any:
        if isinstance(o, Closure):
            # Serialize closure with its environment
            return {
                "__jsl_closure__": True,
                "params": o.params,
                "body": o.body,
                "env": self.default(o.env)
            }
        elif isinstance(o, Env):
            # Serialize environment bindings (not parent - that's the prelude)
            return {
                "__jsl_env__": True,
                "bindings": {k: self.default(v) for k, v in o.items()}
            }
        return super().default(o)


class JSLDecoder(json.JSONDecoder):
    """
    A JSON decoder for JSL types including closures.
    """
    def __init__(self, **kwargs) -> None:
        # Delay import of prelude to avoid circular dependency
        from .prelude import prelude
        self.prelude_env = prelude
        super().__init__(object_hook=self.object_hook, **kwargs)

    def object_hook(self, obj: dict) -> Any:
        if "__jsl_closure__" in obj:
            # Reconstruct closure
            active_prelude = self.prelude_env

            env_data = obj["env"]
            if "__jsl_env__" in env_data:
                # Reconstruct environment with prelude as parent
                user_bindings = {k: self.object_hook(v) if isinstance(v, dict) else v
                               for k, v in env_data["bindings"].items()}
                closure_env = Env(user_bindings, parent=active_prelude)
            else:
                closure_env = Env(parent=active_prelude)

            return Closure(obj["params"], obj["body"], closure_env)
        elif "__jsl_env__" in obj:
            # This case is handled above in closure reconstruction
            return obj
        else:
            return obj


def dumps(obj: JSL, **kwargs) -> str:
    """
    Serialize a JSL object to a JSON formatted string.
    """
    return json.dumps(obj, cls=JSLEncoder, **kwargs)


def loads(s: str, **kwargs) -> JSL:
    """
    Deserialize a JSON formatted string to a JSL object.
    """
    return json.loads(s, cls=JSLDecoder, **kwargs)


# Aliases for backward compatibility and tests
to_json = dumps
from_json = loads
