import typing

from omegaconf import DictConfig, OmegaConf

__all__ = ["apply_overrides"]


def apply_overrides(cfg: DictConfig, overrides: typing.Iterable[str]) -> DictConfig:
    """
    In-place override contents of cfg.

    Parameters
    ----------
    cfg
        An omegaconf config object
    overrides
        List of strings in the format of "a=b" to override configs.
        See: https://hydra.cc/docs/next/advanced/override_grammar/basic/

    Returns
    -------
    DictConfig
        Lazy configuration object
    """

    try:
        from hydra.core.override_parser.overrides_parser import OverridesParser
    except ImportError as err:
        msg = "Hydra is not installed. Please install Hydra to use this function."
        raise ImportError(msg) from err

    overrides = list(overrides)

    def safe_update(cfg, key, value):
        parts = key.split(".")
        for idx in range(1, len(parts)):
            prefix = ".".join(parts[:idx])
            v = OmegaConf.select(cfg, prefix, default=None)
            if v is None:
                break
            if not OmegaConf.is_config(v):
                msg = (
                    f"Trying to update key {key}, but {prefix} "
                    f"is not a config, but has type {type(v)}."
                )
                raise KeyError(msg)
        OmegaConf.update(cfg, key, value, merge=True)

    for o in OverridesParser.create().parse_overrides(overrides):
        key = o.key_or_group
        value = o.value()
        if o.is_delete():
            msg = "deletion is not yet a supported override"
            raise NotImplementedError(msg)
        safe_update(cfg, key, value)

    return cfg
