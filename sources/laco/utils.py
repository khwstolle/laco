r"""
Utils
-----

General utilities.
"""

import ast
import importlib
import pydoc
import types
import typing
from collections.abc import Callable

import expath
from omegaconf import DictConfig, ListConfig


def check_syntax(path: expath.PathType):
    """
    Validate the syntax of a Python-based configuration file.
    """
    content = expath.locate(path).read_text()
    try:
        ast.parse(content)
    except SyntaxError as e:
        msg = f"Config file {path} has syntax error!"
        raise SyntaxError(msg) from e


def as_omegadict(obj: dict | DictConfig) -> DictConfig:
    if isinstance(obj, dict):
        return DictConfig(obj, flags={"allow_objects": True})
    return obj


def generate_path(obj: typing.Any) -> str:
    """
    Inverse of ``locate()``. Generates the fully qualified name of an object.
    Handles cases where the object is not directly importable, e.g. due to
    nested classes or private modules.

    The generated path is simplified by removing redundant module parts, e.g.
    ``module.submodule._impl.class`` may become ``module.submodule.class`` if
    the later also resolves to the same object.

    Bound methods are supported by inspecting the ``__self__`` attribute.

    Parameters
    ----------
    obj
        The object to generate the path for.

    Returns
    -------
    str
        The fully qualified name of the object.
    """

    def __check(path: str, obj: typing.Any) -> bool:
        # Check if the path resolves to the same object
        try:
            check_ok = locate_object(path) is obj
        except ImportError:
            check_ok = False
        return check_ok

    try:
        self = obj.__self__
    except AttributeError:
        self = None

    if self is not None:
        self_path = generate_path(self)
        return f"{self_path}.{obj.__name__}"

    module, qualname = obj.__module__, obj.__qualname__

    # Compress the path to this object, e.g. ``module.submodule._impl.class``
    # may become ``module.submodule.class``, if the later also resolves to the same
    # object. This simplifies the string, and also is less affected by moving the
    # class implementation.
    module_parts = module.split(".")
    for k in range(1, len(module_parts)):
        prefix = ".".join(module_parts[:k])
        path = f"{prefix}.{qualname}"
        if __check(path, obj):
            return path

    # Default to the full path plus qualname
    path = f"{module}.{qualname}"
    if not __check(path, obj):
        msg = f"Cannot generate path for object {obj}!"
        raise ImportError(msg)

    return path


def locate_object(path: str) -> typing.Any:  # noqa: C901
    """
    Dynamically locates and returns an object by its fully qualified name.

    Parameters
    ----------
    name (str):
        The fully qualified name of the object to locate.

    Returns
    -------
    Any:
        The located object.

    Raises
    ------
    ImportError
        If the object cannot be located.
    """

    # Sanitization: input path
    if path == "":
        msg = "Cannot locate object: empty path."
        raise ImportError(msg)

    # Try to locate the object using pydoc
    obj = pydoc.locate(path)
    if obj is not None:
        return obj

    # Pydoc failed, try to locate the object manually
    parts = list(path.split("."))
    assert len(parts) > 0
    for part in parts:
        if not len(part):
            msg = (
                f"Error loading {path!r}: invalid dotstring.\n\n"
                "Relative imports are not supported."
            )
            raise ValueError(msg)

    mod_name = parts[0]
    try:
        obj = importlib.import_module(mod_name)
    except Exception as exc_import:
        msg = (
            f"Error loading {path!r}:\n{repr(exc_import)}\n\n"
            f"Are you sure that module {mod_name!r} is installed?"
        )
        raise ImportError(msg) from exc_import
    for m in range(1, len(parts)):
        part = parts[m]
        try:
            obj = getattr(obj, part)
        except AttributeError as exc_attr:
            parent_dotpath = ".".join(parts[:m])
            if isinstance(obj, types.ModuleType):
                mod = ".".join(parts[: m + 1])
                try:
                    obj = importlib.import_module(mod)
                    continue
                except ModuleNotFoundError as exc_import:
                    msg = (
                        f"Error loading {path!r}:\n{repr(exc_import)}\n\n"
                        f"Is {part!r} importable from {parent_dotpath!r}?"
                    )
                    raise ImportError(msg) from exc_import
                except Exception as exc_import:
                    msg = f"Error loading {path!r}:\n{repr(exc_import)}"
                    raise ImportError(msg) from exc_import
            msg = (
                f"Error loading {path!r}:\n{repr(exc_attr)}\n\n"
                f"Are you sure that {part!r} is an attribute of {parent_dotpath}?"
            )
            raise ImportError(msg) from exc_attr
    return obj


def apply_recursive[_C: (DictConfig, ListConfig)](
    cfg: _C, func: Callable[[_C], None]
) -> None:
    """
    Apply func recursively to all DictConfig in cfg.
    """
    if isinstance(cfg, DictConfig):
        func(cfg)
        for v in cfg.values():
            apply_recursive(v, func)
    elif isinstance(cfg, ListConfig):
        for v in cfg:
            apply_recursive(v, func)


def check_lazy(obj: typing.Any, checks: typing.Iterable[Callable] | Callable) -> bool:
    """
    Check if an object is a lazy call to a target callable.

    Parameters
    ----------
    obj : any
        The object to check.
    target : callable or str
        The target callable to check against.

    Returns
    -------
    bool
        Whether the object is a lazy call to the target callable.
    """
    from .keys import LAZY_CALL

    if not isinstance(obj, DictConfig):
        return False
    tgt = obj.get(LAZY_CALL, None)
    if tgt is None:
        return False
    if isinstance(tgt, str):
        tgt = locate_object(tgt)
    if callable(checks):
        checks = [checks]
    return any(tgt is check for check in checks)
