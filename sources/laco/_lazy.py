"""
Instantiation of configuration objects.
"""

import dataclasses
import logging
import pprint
import types
import typing

import omegaconf
from omegaconf import DictConfig, ListConfig

__all__ = [
    "instantiate",
]

if typing.TYPE_CHECKING:

    class LazyObject[_L]:
        def __getattr__(self, name: str, /) -> typing.Any: ...

        @typing.override
        def __setattr__(self, name: str, value: typing.Any, /) -> None: ...  # noqa: PYI063

else:

    class LazyObject(dict[str, typing.Any]):
        def __class_getitem__(cls, item: typing.Any) -> dict[str, typing.Any]:
            return types.GenericAlias(dict, (str, typing.Any))


type AnyConfig = DictConfig | ListConfig


def migrate_target(target: typing.Any) -> typing.Any:
    return target


_INST_SEQ_TYPEMAP: dict[type, type] = {
    ListConfig: list,
    list: list,
    tuple: tuple,
    set: set,
    frozenset: frozenset,
}


def instantiate(cfg: typing.Any, /) -> object:  # noqa: C901, PLR0912
    """
    Recursively instantiate objects defined in dictionaries with keys:

    - Special key ``keys.CONFIG_CALL``: defines the callable/objec to be instantiated.
    - Special key ``"_args_"``: defines the positional arguments to be passed to the
        callable.
    - Other keys define the keyword arguments to be passed to the callable.
    """
    import laco._env
    import laco.keys
    import laco.utils

    if cfg is None or isinstance(
        cfg,
        int
        | float
        | bool
        | str
        | set
        | frozenset
        | bytes
        | type
        | types.NoneType
        | types.FunctionType,
    ):
        return cfg  # type: ignore[return-value]

    if laco.get_env(bool, "LACO_TRACE", default=False):
        logging.getLogger(__name__).info(
            "Instantiating %s", pprint.pprint(omegaconf.OmegaConf.to_container(cfg))
        )

    if isinstance(cfg, typing.Sequence) and not isinstance(
        cfg, typing.Mapping | str | bytes
    ):
        cls = type(cfg)
        cls = _INST_SEQ_TYPEMAP.get(cls, cls)
        return cls(instantiate(x) for x in cfg)

    # If input is a DictConfig backed by dataclasses (structured config)
    # instantiate it to the actual dataclass.
    if isinstance(cfg, DictConfig) and dataclasses.is_dataclass(
        cfg._metadata.object_type
    ):
        return omegaconf.OmegaConf.to_object(cfg)

    if isinstance(cfg, typing.Mapping) and laco.keys.LAZY_CALL in cfg:
        # conceptually equivalent to hydra.utils.instantiate(cfg) with _convert_=all,
        # but faster: https://github.com/facebookresearch/hydra/issues/1200
        cfg = {k: instantiate(v) for k, v in cfg.items()}
        cls = cfg.pop(laco.keys.LAZY_CALL)
        cls = migrate_target(cls)
        cls = instantiate(cls)

        if isinstance(cls, str):
            cls_name = cls
            cls = laco.utils.locate_object(cls_name)
            assert cls is not None, cls_name
        else:
            try:
                cls_name = cls.__module__ + "." + cls.__qualname__
            except Exception:  # noqa: B902, PIE786
                # target could be anything, so the above could fail
                cls_name = str(cls)
        if not callable(cls):
            msg = f"Non-callable object found: {laco.keys.LAZY_CALL}={cls!r}!"
            raise TypeError(msg)

        cfg_args = cfg.pop(laco.keys.LAZY_ARGS, ())
        if not isinstance(cfg_args, typing.Sequence):
            msg = (
                f"Expected sequence for {laco.keys.LAZY_ARGS}, "
                f"but got {type(cfg_args)}!"
            )
            raise TypeError(msg)

        try:
            return cls(*cfg_args, **cfg)
        except Exception as err:
            msg = (
                f"Error instantiating lazy object {cls_name}.\n\nConfig node:\n\t{cfg}!"
            )
            raise RuntimeError(msg) from err

    if isinstance(cfg, dict | DictConfig):
        return {k: instantiate(v) for k, v in cfg.items()}  # type: ignore[return-value]

    if callable(cfg):
        return cfg

    err = f"Cannot instantiate {cfg}, type {type(cfg)}!"
    raise ValueError(err)
