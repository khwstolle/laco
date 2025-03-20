"""
Lazy configuration system, inspired by and based on Detectron2 and Hydra.
"""

from . import cli, handler, keys, language, ops, utils
from ._env import *
from ._lazy import *
from ._loader import *
from ._overrides import *
from ._resolvers import *

__version__: str


def __getattr__(name: str):
    from importlib.metadata import PackageNotFoundError, version

    if name == "__version__":
        try:
            return version(__name__)
        except PackageNotFoundError:
            return "unknown"
    msg = f"Module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
