import functools
import typing
from dataclasses import is_dataclass

from omegaconf import DictConfig

import laco.utils 
import laco.keys


def partial(
    **kwargs: typing.Any,
) -> typing.Callable[..., typing.Any]:
    cb = kwargs.get(laco.keys.LAZY_PART, None)
    if isinstance(cb, str):
        cb = laco.utils.locate_object(cb)
    if not callable(cb):
        msg = f"Expected a callable object or location (str), got {cb} (type {type(cb)}"
        raise TypeError(msg)
    return functools.partial(cb, **kwargs)
