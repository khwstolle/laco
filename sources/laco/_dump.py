import dataclasses
import pprint
from contextlib import suppress
from copy import deepcopy

import iopathlib
import yaml
from omegaconf import DictConfig, OmegaConf, SCMode

from . import keys, utils

__all__ = ["dump_config", "save_config"]


def dump_config(cfg) -> str:  # noqa: C901
    if not isinstance(cfg, DictConfig):
        cfg = utils.as_omegadict(
            dataclasses.asdict(cfg) if dataclasses.is_dataclass(cfg) else cfg
        )
    try:
        cfg = deepcopy(cfg)
    except Exception:
        pass
    else:

        def _replace_type_by_name(x):
            if keys.LAZY_CALL in x and callable(x._target_):
                with suppress(AttributeError):
                    x._target_ = utils.generate_path(x._target_)

        utils.apply_recursive(cfg, _replace_type_by_name)

    try:
        cfg_as_dict = OmegaConf.to_container(
            cfg,
            # Do not resolve interpolation when saving, i.e. do not turn ${a} into
            # actual values when saving.
            resolve=False,
            # Save structures (dataclasses) in a format that can be instantiated later.
            # Without this option, the type information of the dataclass will be erased.
            structured_config_mode=SCMode.INSTANTIATE,
        )
    except Exception as err:
        cfg_pretty = pprint.pformat(OmegaConf.to_container(cfg)).replace("\n", "\n\t")
        msg = f"Config cannot be converted to a dict!\n\nConfig node:\n{cfg_pretty}"
        raise ValueError(msg) from err

    dump_kwargs = {"default_flow_style": None, "allow_unicode": True}

    def _find_undumpable(cfg_as_dict, *, _key=()) -> tuple[str, ...] | None:
        for key, value in cfg_as_dict.items():
            if not isinstance(value, dict):
                continue
            try:
                _ = yaml.dump(value, **dump_kwargs)
                continue
            except Exception:
                pass
            key_with_error = _find_undumpable(value, _key=_key + (key,))
            if key_with_error:
                return key_with_error
            return _key + (key,)
        return None

    try:
        dumped = yaml.dump(cfg_as_dict, **dump_kwargs)
    except Exception as err:
        cfg_pretty = pprint.pformat(cfg_as_dict).replace("\n", "\n\t")
        problem_key = _find_undumpable(cfg_as_dict)
        if problem_key:
            problem_key = ".".join(problem_key)
            msg = f"Config cannot be saved due to key {problem_key!r}"
        else:
            msg = "Config cannot be saved due to an unknown entry"
        msg += f"\n\nConfig node:\n\t{cfg_pretty}"
        raise SyntaxError(msg) from err

    return dumped


def save_config(cfg, path: str):
    """
    Save a config object to a yaml file.

    Parameters
    ----------
    cfg
        An omegaconf config object.
    filename
        The file name to save the config file.
    """
    local_path = iopathlib.get_local_path(path)  # type: ignore[arg-type]
    if not local_path.endswith(".yaml"):
        msg = f"Config file should be saved as a yaml file! Got: {path}"
        raise ValueError(msg)

    dumped = dump_config(cfg)
    try:
        with open(local_path, "w") as fh:  # noqa: PTH123
            fh.write(dumped)
        _ = yaml.unsafe_load(dumped)
    except Exception as err:
        msg = f"Config file cannot be saved at {local_path!r}"
        raise SyntaxError(msg) from err
