import builtins
import dataclasses
import io
import os
import pathlib
import pprint
import typing
from contextlib import contextmanager, suppress
from copy import deepcopy
from uuid import uuid4

import iopathlib
import yaml
from omegaconf import DictConfig, ListConfig, OmegaConf, SCMode

from . import keys, utils
from .language import ParamsWrapper
from .utils import as_omegadict, check_syntax

__all__ = ["load", "dump", "save"]


PATCH_PREFIX: typing.Final = "_laco_"


@contextmanager
def _patch_import():  # noqa: C901
    import importlib.machinery
    import importlib.util

    import_default = builtins.__import__

    def find_relative(original_file, relative_import_path, level):
        # NOTE: "from . import x" is not handled. Because then it's unclear
        # if such import should produce `x` as a python module or DictConfig.
        # This can be discussed further if needed.
        relative_import_err = (
            "Relative import of directories is not allowed within config files. "
            "Within a config file, relative import can only import other config files."
        )
        if not len(relative_import_path):
            raise ImportError(relative_import_err)

        cur_file = os.path.dirname(original_file)  # noqa: PTH120
        for _ in range(level - 1):
            cur_file = os.path.dirname(cur_file)  # noqa: PTH120
        cur_name = relative_import_path.lstrip(".")
        for part in cur_name.split("."):
            cur_file = os.path.join(cur_file, part)  # noqa: PTH118
        if not cur_file.endswith(".py"):
            cur_file += ".py"
        if not iopathlib.isfile(cur_file):
            cur_file_no_suffix = cur_file[: -len(".py")]
            if iopathlib.isdir(cur_file_no_suffix):
                raise ImportError(
                    f"Cannot import from {cur_file_no_suffix}." + relative_import_err
                )
            msg = (
                f"Cannot import name {relative_import_path} from "
                f"{original_file}: {cur_file} does not exist."
            )
            raise ImportError(msg)
        return cur_file

    def import_patched(name, globals=None, locals=None, fromlist=(), level=0):
        if (
            # Only deal with relative imports inside config files
            level != 0
            and globals is not None
            and (globals.get("__package__", "") or "").startswith(PATCH_PREFIX)
        ):
            cur_file = find_relative(globals["__file__"], name, level)
            check_syntax(cur_file)
            spec = importlib.machinery.ModuleSpec(
                _generate_packagename(cur_file), None, origin=cur_file
            )
            module = importlib.util.module_from_spec(spec)
            module.__file__ = cur_file
            with iopathlib.open(cur_file) as f:
                content = f.read()
            exec(compile(content, cur_file, "exec"), module.__dict__)
            for name in fromlist:  # noqa: PLR1704
                val = as_omegadict(module.__dict__[name])
                module.__dict__[name] = val
            return module
        return import_default(name, globals, locals, fromlist=fromlist, level=level)

    builtins.__import__ = import_patched
    yield import_patched
    builtins.__import__ = import_default


def _filepath_to_name(path: str | pathlib.Path | os.PathLike) -> str | None:
    """
    Convert a file path to a module name.
    """

    configs_root = pathlib.Path("./configs").resolve()
    path = iopathlib.locate(path).resolve()
    try:
        name = "/".join((path.relative_to(configs_root).parent.as_posix(), path.stem))
    except Exception:
        name = "/".join([path.parent.stem, path.stem])

    name = name.replace("./", "")
    name = name.replace("//", "/")

    if name in {"__init__", "defaults", "unknown", "config", "configs"}:
        return None
    return name.removesuffix(".py")


def _generate_packagename(path: str):
    return PATCH_PREFIX + str(uuid4())[:4] + "." + pathlib.Path(path).name


def load(path: str | pathlib.Path | os.PathLike) -> DictConfig:
    """Loads a configuration from a local source."""
    import laco
    import laco.keys
    import laco.utils

    path = iopathlib.locate(path)

    ext = os.path.splitext(path)[1]  # noqa: PTH122
    match ext.lower():
        case ".py":
            laco.utils.check_syntax(path)

            with _patch_import():
                # Record the filename
                nsp = {
                    "__file__": path,
                    "__package__": _generate_packagename(path),
                }
                with iopathlib.open(path) as f:
                    content = f.read()
                # Compile first with filename to:
                # 1. make filename appears in stacktrace
                # 2. make load_rel able to find its parent's (possibly remote) location
                exec(compile(content, iopathlib.locate(path), "exec"), nsp)

            export = nsp.get(
                "__all__",
                (
                    k
                    for k, v in nsp.items()
                    if not k.startswith("_")
                    and (
                        isinstance(
                            v,
                            dict
                            | ParamsWrapper
                            | list
                            | DictConfig
                            | ListConfig
                            | int
                            | float
                            | str
                            | bool,
                        )
                        or v is None
                    )
                ),
            )
            obj: dict[str, typing.Any] = {
                k: v() if isinstance(v, ParamsWrapper) else v
                for k, v in nsp.items()
                if k in export
            }
            obj.setdefault(laco.keys.CONFIG_NAME, _filepath_to_name(path))
            obj.setdefault(laco.keys.CONFIG_VERSION, laco.__version__)

        case ".yaml":
            with iopathlib.open(path) as f:
                obj = yaml.unsafe_load(f)
            obj.setdefault(laco.keys.CONFIG_NAME, "unknown")
            obj.setdefault(laco.keys.CONFIG_VERSION, "unknown")
        case _:
            msg = "Unsupported file extension %s!"
            raise ValueError(msg, ext)

    return laco.utils.as_omegadict(obj)


@typing.overload
def dump(cfg: object, fh: None = None) -> str: ...


@typing.overload
def dump(cfg: object, fh: io.StringIO) -> None: ...


def dump(cfg: object, fh: io.StringIO | None = None) -> str | None:
    r"""Dump configuration file to YAML format.

    Parameters
    ----------
    cfg
        An omegaconf config object.
    fh
        A file handle to write the config to. If None, a string will be returned.

    Returns
    -------
    str
        The dumped config file in YAML format.
    """
    if not isinstance(cfg, DictConfig):
        cfg = utils.as_omegadict(
            dataclasses.asdict(cfg) if dataclasses.is_dataclass(cfg) else cfg  # type: ignore[arg-type]
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
        dumped = yaml.dump(cfg_as_dict, fh, **dump_kwargs)
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


def save[ConfigType: object | DictConfig](
    cfg: ConfigType, path: str | pathlib.Path | os.PathLike, *, reload: bool = True
) -> ConfigType | DictConfig:
    """
    Save a config object to a yaml file.

    Parameters
    ----------
    cfg
        An omegaconf config object.
    path
        The file path to save the config file.
    reload
        If True, reload the file (for validation) after saving.

    Returns
    -------
    ConfigType
        The saved config object. If `reload` is True, the reloaded config object is
        returned.

    Raises
    ------
    AssertionError
        If the config cannot be dumped or the post-save check fails.
    """
    dumped = dump(cfg)
    with iopathlib.open(path, "w") as fh:  # noqa: PTH123
        fh.write(dumped)

    return load(path) if reload else cfg
