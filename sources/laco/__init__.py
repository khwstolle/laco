r"""Laco
========

LAzy COnfiguration (LACO) system, inspired by and based on Detectron2 and Hydra.
"""

from . import keys, utils
from ._env import *
from ._io import *
from ._lazy import *
from ._overrides import *
from ._resolvers import *

__version__: str


def __getattr__(name: str):
    from importlib.metadata import PackageNotFoundError, version

    if name == "__version__":
        try:
            return version(__name__)
        except PackageNotFoundError:  # pragma: no cover
            return "unknown"
    msg = f"Module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
