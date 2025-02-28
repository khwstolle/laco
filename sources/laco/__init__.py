"""
Lazy configuration system, inspired by and based on Detectron2 and Hydra.
"""

from ._lazy import *
from ._loader import *
from ._overrides import *
from ._resolvers import *

__lazy__ = ("env", "language", "builtins", "cli", "env", "handler", "keys", "utils", "handler")


def __getattr__(name: str):
    from importlib.metadata import PackageNotFoundError, version
    from importlib import import_module

    if name in __lazy__:
        return import_module(name, package=__name__)
    if name == "__version__":
        try:
            return version(__name__)
        except PackageNotFoundError:
            return "unknown"
    msg = f"Module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)

def __dir__() -> list[str]:
    from ._lazy import __all__ as all_lazy
    from ._loader import __all__ as all_loader
    from ._overrides import __all__ as all_overrides
    from ._resolvers import __all__ as all_resolvers
    
    return sorted(__lazy__ + ["__version__"] + all_lazy + all_loader + all_overrides + all_resolvers)