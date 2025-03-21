r"""
Working with environment variables.
"""

import enum
import functools
import os
import typing

__all__ = ["get_env", "EnvFilter"]

type EnvVarCompatible = int | str | bool


class EnvFilter(enum.StrEnum):
    STRING = enum.auto()
    TRUTHY = enum.auto()
    FALSY = enum.auto()
    POSITIVE = enum.auto()
    NEGATIVE = enum.auto()
    NONNEGATIVE = enum.auto()
    NONPOSITIVE = enum.auto()

    @staticmethod
    def apply(f: "EnvFilter | str | None", v: typing.Any, /) -> bool:  # noqa: PLR0911
        if f is None:
            return True
        if v is None:
            return False
        match f:
            case EnvFilter.STRING:
                if not isinstance(v, str):
                    return False
                v = v.lower()
                return v != ""
            case EnvFilter.TRUTHY:
                return bool(v)
            case EnvFilter.FALSY:
                return not bool(v)
            case EnvFilter.POSITIVE:
                return float(v) > 0
            case EnvFilter.NEGATIVE:
                return float(v) < 0
            case EnvFilter.NONNEGATIVE:
                return float(v) >= 0
            case EnvFilter.NONPOSITIVE:
                return float(v) <= 0
            case _:
                msg = f"Invalid filter: {f!r}"
                raise ValueError(msg)


@typing.overload
def get_env[_T: EnvVarCompatible](
    __type: type[_T],
    /,
    *keys: str,
    default: _T,
    filter: EnvFilter | None = None,
) -> _T: ...


@typing.overload
def get_env[_T: EnvVarCompatible](
    __type: type[_T],
    /,
    *keys: str,
    default: _T | None = None,
    filter: EnvFilter | None = None,
) -> _T | None: ...


@functools.cache
def get_env[_T: EnvVarCompatible](
    __type: type[_T],
    /,
    *keys: str,
    default: _T | None = None,
    filter: EnvFilter | None = None,
) -> _T | None:
    """
    Read an environment variable. If the variable is not set, return the default value.

    If no default is given, an error is raised if the variable is not set.
    """
    keys_read = []
    for k in keys:
        keys_read.append(k)
        v = os.getenv(k)
        if v is None:
            continue
        v = strtobool(v) if issubclass(__type, bool) else __type(v)
        if not EnvFilter.apply(filter, v):
            continue
        break
    else:
        v = default
    return typing.cast(_T, v)


def strtobool(v: str) -> bool:
    """
    Convert a string to a boolean value.
    """
    v = v.lower()
    if v in {"true", "yes", "on", "1"}:
        return True
    if v in {"false", "no", "off", "0"}:
        return False
    msg = f"Invalid boolean value: {v!r}"
    raise ValueError(msg)
