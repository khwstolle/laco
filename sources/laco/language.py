import abc
import collections
import functools
import typing
import warnings
from collections.abc import Callable
from dataclasses import is_dataclass

import omegaconf
import regex as re
from omegaconf import DictConfig

from laco import ops

__all__ = [
    "call",
    "bind",
    "node",
    "ref",
    "partial",
    "Dict",
    "OrderedDict",
    "Set",
    "Tuple",
    "List",
]


# --------------- #
# Config file API #
# --------------- #


def call[**_P, _L](
    target: Callable[_P, _L],
    *,
    reserved_ok: typing.Collection[str] = (),
    expand_args: bool = False,
) -> Callable[_P, _L]:
    r"""Peform a lazy call to a function or class.

    Parameters
    ----------
    target : callable
        The target function or class to call.
    reserved_ok : collection of str
        A collection of reserved keys that are allowed in the kwargs.
    expand_args : bool
        Whether to expand the first positional argument as *args. If True, only one
        positional argument is allowed, and it will be expanded as *args. If False, the
        first and second positional arguments are passed as *args.
    """
    import laco.keys
    import laco.utils

    assert isinstance(reserved_ok, typing.Collection), type(reserved_ok)
    assert callable(target) or isinstance(target, str | typing.Mapping), type(target)

    @functools.wraps(target)
    def wrap(*args: _P.args, **kwargs: _P.kwargs) -> DictConfig:
        resv_keys_used = (
            set(laco.keys.LazyKey.__members__.values()).difference(reserved_ok)
            & kwargs.keys()
        )
        if resv_keys_used:
            msg = f"Reserved keys found in kwargs: {resv_keys_used}"
            raise ValueError(msg)

        node = {}
        if is_dataclass(target):
            node[laco.keys.LAZY_CALL] = laco.utils.generate_path(target)
        else:
            node[laco.keys.LAZY_CALL] = target
        if args and len(args) > 0:
            if expand_args:
                lazy_args, *remaining_args = args
                if len(remaining_args) > 0:
                    msg = (
                        f"Only one positional argument is allowed when {expand_args=}!"
                        f" Got {len(args)} arguments."
                    )
                    raise ValueError(msg)
            else:
                lazy_args = tuple(args)
            node[laco.keys.LAZY_ARGS] = lazy_args

        node.update(kwargs)

        return laco.utils.as_omegadict(node)

    return wrap


def bind[**_P, _R](func: Callable[_P, _R], /) -> Callable[_P, omegaconf.DictConfig]:
    """
    Wrapper around call with type hints that support use in OmegaConf's structured
    configuration system.

    Primary use is the definition of root nodes that are also lazy calls.
    """
    return call(func)  # type: ignore[no-any-return]


def pairs(
    node: DictConfig | typing.Mapping,
) -> typing.Iterator[tuple[str, typing.Any]]:
    r"""
    Key-value pairs from a configuration node, where special keys are ignored.
    """
    import laco.keys

    if not isinstance(node, DictConfig):
        msg = f"Expected a configuration node, got {node=} (type {type(node)})!"
        raise TypeError(msg)
    for k, v in node.items():
        if k in {laco.keys.LAZY_CALL, laco.keys.LAZY_ARGS}:
            continue
        assert isinstance(k, str), type(k)
        yield str(k), v


@typing.dataclass_transform(kw_only_default=True)
class NodeSpec:
    pass


def node[_T: NodeSpec](_: type[_T], /) -> type[_T]:
    """
    Uses a template :class:`ConfigNode` to define an OmegaConf node that has the same
    fields as the template


    The type checker will treat the resulting object as a :class:`ConfigNode`, but
    at runtime the resulting object is a regular OmegaConf node based on the fields
    of the template.
    """
    import laco.utils

    def _create_fake_class(**kwargs):
        return laco.utils.as_omegadict(kwargs)

    return _create_fake_class  # type: ignore[no-any-return]


def ref[_R](target: str) -> _R:
    """
    Reference to another variable in the configuration using an OmegaConf interpolation
    string.
    """
    return typing.cast(_R, target)


def wrap_on_result(func_wrap, func_next, **kwargs_next):
    """
    Run a function on the result of another function. Useful in configuration files when
    you want to wrap a function on the result of another function, without having to
    change the keys of the configuration file.
    """

    def wrapper(*args, **kwargs):
        return func_next(func_wrap(*args, **kwargs), **kwargs_next)

    return wrapper


def partial(func: Callable[..., typing.Any], /) -> Callable[..., typing.Any]:
    """
    Partially apply a function with keyword arguments.

    Parameters
    ----------
    func : callable
        The function to partially apply.

    Returns
    -------
    callable
        A lazy callable object that is forwarded to ``functools.partial``.
    """
    import laco.keys
    import laco.ops

    def wrapper(**kwargs):
        if laco.keys.LAZY_PART in kwargs:
            msg = f"Reserved key {laco.keys.LAZY_PART!r} found in arguments!"
            raise ValueError(msg)
        kwargs[laco.keys.LAZY_PART] = func
        return call(laco.ops.partial, reserved_ok={laco.keys.LazyKey.PARTIAL})(**kwargs)

    return wrapper


def repeat[_O](num: int, src: _O) -> list[_O]:
    return call(ops.repeat)(num=num, src=src)  # type: ignore[no-any-return]


# ------ #
# Macros #
# ------ #

PATTERN_CONFIG_KEY_STRICT = r"^[a-zA-Z_][a-zA-Z0-9_]*$"


def _check_valid_key(key: str, *, warn: bool = True) -> bool:
    if not re.match(PATTERN_CONFIG_KEY_STRICT, key):
        if warn:
            msg = (
                f"Key '{key}' may possibly lead to bad interoperability! "
                "It is recommended that keys start with a letter or underscore, "
                "and can only contain letters, numbers, and underscores."
            )
            warnings.warn(msg, stacklevel=2)
        return False
    return True


class _PositionalMacro[_R](metaclass=abc.ABCMeta):
    r"""
    A macro that generates a :func:`call` from positional arguments (accepts a sequence
    of items).
    """

    def __new__(cls, *args: typing.Any) -> _R:
        return call(cls.target)(items=list(args))

    @classmethod
    @abc.abstractmethod
    def target(cls, items: list[typing.Any]) -> _R:
        msg = "Method 'target' must be implemented in subclasses!"
        raise NotImplementedError(msg)


class _KeywordMacro[_R](metaclass=abc.ABCMeta):
    r"""
    A macro that generates a :func:`call` from keyword arguments (accepts a mapping of
    key-value pairs).
    """

    def __new__(cls, **kwargs: typing.Any) -> _R:
        for k in kwargs:
            _check_valid_key(k)
        return call(cls.target)(**kwargs)

    @classmethod
    @abc.abstractmethod
    def target(cls, **kwargs: typing.Any) -> _R:
        msg = "Method 'target' must be implemented in subclasses!"
        raise NotImplementedError(msg)


class Dict[_T](_KeywordMacro[dict[str, _T]]):
    @typing.override
    @classmethod
    def target(cls, **kwargs: _T):
        return dict(kwargs.items())


class OrderedDict[_T](_PositionalMacro[collections.OrderedDict[str, _T]]):
    @typing.override
    @classmethod
    def target(cls, items: list[tuple[str, _T]]):
        return collections.OrderedDict(items)


class DictFromItems[_T](_PositionalMacro[dict[str, _T]]):
    @classmethod
    @typing.override
    def target(cls, items: list[tuple[str, _T]]):
        return dict(items)


class Set[_T](_PositionalMacro[set[_T]]):
    @classmethod
    @typing.override
    def target(cls, items: list[_T]):
        if isinstance(items, omegaconf.ListConfig):
            items = omegaconf.OmegaConf.to_object(items)  # type: ignore[ no-untyped-call]
            assert isinstance(items, typing.Sequence), type(items)
        return set(items)


class Tuple[_T](_PositionalMacro[tuple[_T]]):
    def __new__(cls, *args):
        return call(cls.target)(items=list(args))

    @classmethod
    @typing.override
    def target(cls, items: typing.Any) -> tuple:
        items = (
            omegaconf.OmegaConf.to_object(items)
            if isinstance(items, omegaconf.ListConfig)
            else items
        )
        return tuple(i for i in items)


class List[_T](_PositionalMacro[list[_T]]):
    def __new__(cls, *args):
        return call(cls.target)(items=list(args))

    @classmethod
    @typing.override
    def target(cls, items: typing.Any) -> list:
        if isinstance(items, omegaconf.ListConfig):
            items = omegaconf.OmegaConf.to_object(items)  # type: ignore[no-untyped-call]
            assert isinstance(items, typing.Sequence), type(items)
        return list(items)


#####################
# Config Parameters #
#####################


class ParamsWrapper[_T]:
    __slots__ = ("_node", "_dict")

    def __init__(self, cls: type[_T]):
        self._node = cls.__name__
        self._dict = {
            k: v
            for k, v in cls.__dict__.items()
            if not k.startswith("_") or callable(v)
        }

        if len(self._dict) == 0:
            msg = f"Parameter class {cls!r} contains no items!"
            raise ValueError(msg)

    def __getattr__(self, name: str):
        if not name.startswith("_"):
            return ref(f"${{{self._node}.{name}}}")
        raise AttributeError(name)

    @typing.override
    def __setattr__(self, name, value):
        if not name.startswith("_"):
            self._dict.__setitem__(name, value)
        else:
            super().__setattr__(name, value)

    def __contains__(self, name: str):
        return name in self._dict

    def __call__(self) -> dict[str, typing.Any]:
        return self._dict


def params[_T](cls: type[_T]) -> type[_T]:
    r"""
    Create a class that represents a set of hyperparameters,
    accessing an attribute will return a reference, while accesing the item will
    return the actual value.

    This is useful for typing in configuration objects.
    """

    return typing.cast(type[_T], ParamsWrapper(cls))
