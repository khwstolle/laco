import copy
import functools
import typing

import laco.keys
import laco.utils


def partial(
    **kwargs: typing.Any,
) -> typing.Callable[..., typing.Any]:
    cb = kwargs.pop(laco.keys.LAZY_PART)
    if isinstance(cb, str):
        cb = laco.utils.locate_object(cb)
    if not callable(cb):
        msg = f"Expected a callable object or location (str), got {cb} (type {type(cb)}"
        raise TypeError(msg)
    return functools.partial(cb, **kwargs)


def repeat[_O](num: int, src: _O) -> list[_O]:
    return [copy.deepcopy(src) for _ in range(num)]
